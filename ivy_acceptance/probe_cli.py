"""Bounded infrastructure proof, independently labeled from model evaluation."""
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

from .budget import BudgetBlocked, Limits
from .canonical import InvalidManifest, read_json
from .docker_probe import DockerProbeAdapter
from .grading import check_citations
from .materialization import materialize_preview
from .planning import compile_plan
from .ports import WorkerRequest, WorkloadHandle
from .storage import AttemptStore, file_sha256, read_record, write_record


def add_commands(sub):
    p = sub.add_parser("probe", help="execute a fixed credential-free container probe; never run a model")
    p.add_argument("config", type=Path)
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--store", type=Path, required=True, help="private supervisor artifact directory")
    p.add_argument("--image", required=True, help="local image pinned as repository@sha256:digest")
    p.add_argument("--context", required=True, help="explicit Docker context")
    p.add_argument("--attempt", required=True, help="fresh identifier; never silently reuse an attempt")
    p.add_argument("--case", default="R1")
    p.add_argument("--variant", choices=("baseline", "changed"), default="baseline")
    p.add_argument("--deadline", type=int, default=10)
    p.add_argument("--wait", action="store_true", help="keep probe alive for cancellation/timeout control")
    p.add_argument("--cancel-after", type=float)
    p.add_argument("--preflight-only", action="store_true", help="check setup and record evidence without reserving an attempt")
    r = sub.add_parser("recover-probe", help="confirm shutdown of a reserved probe after supervisor failure")
    r.add_argument("--store", type=Path, required=True)
    r.add_argument("--attempt", required=True)
    v = sub.add_parser("verify-probe", help="verify saved runtime evidence hashes without executing")
    v.add_argument("directory", type=Path)
    e = sub.add_parser("authorize-probe-extension", help="record explicit local approval for one 20-minute, three-probe extension")
    e.add_argument("--store", type=Path, required=True)
    e.add_argument("--authorization-reference", required=True)
    c = sub.add_parser("authorize-completion-probe", help="append explicit approval for one completion probe in 10 minutes")
    c.add_argument("--store", type=Path, required=True)
    c.add_argument("--authorization-reference", required=True)
    s = sub.add_parser("authorize-validation-session", help="record one 10-minute runtime session with at most three fresh probes")
    s.add_argument("--store", type=Path, required=True)
    s.add_argument("--authorization-reference", required=True)


def verify_probe(directory):
    receipt = read_record(directory / "receipt.json")
    if (receipt.get("schema_version") != 1
            or receipt.get("evidence_kind") != "infrastructure_probe_not_model_evaluation"):
        raise InvalidManifest("not a probe receipt")
    expected = receipt["artifact_sha256"]
    required = {"preparation.json", "prepared.json", "events.jsonl", receipt["stop_evidence"]}
    if receipt["runtime"].get("derived_image"):
        required.update(("image-input.json", "image-build.json"))
    if type(expected) is not dict or set(expected) != required:
        raise InvalidManifest("incomplete artifact bindings")
    for name, sha in expected.items():
        from .canonical import relative_path
        relative_path(name)
        if "/" in name or file_sha256(directory / name) != sha:
            raise InvalidManifest("bound probe artifact changed")
    if receipt["capture_sha256"] != expected["events.jsonl"]:
        raise InvalidManifest("capture binding changed")
    prep = read_record(directory / "preparation.json")
    stop = read_record(directory / receipt["stop_evidence"])
    if (prep["binding"] != receipt["binding"] or prep["runtime_id"] != receipt["runtime_id"]
            or stop["runtime_id"] != receipt["runtime_id"]
            or stop["termination_confirmed"] != receipt["termination_confirmed"]):
        raise InvalidManifest("probe provenance mismatch")
    if receipt["runtime"].get("derived_image"):
        image_input = read_record(directory / "image-input.json")
        build = read_record(directory / "image-build.json")
        prepared = read_record(directory / "prepared.json")
        if (build["derived_image"] != receipt["runtime"]["derived_image"]
                or prepared["container"]["Image"] != build["derived_image"]
                or build["base_image"] != prep["runtime"]["image"]
                or any(build[k] != image_input[k] for k in ("base_image", "base_id", "context_sha256"))):
            raise InvalidManifest("probe image provenance mismatch")
    return {"integrity": "verified", "execution_state": receipt["execution_state"],
            "termination_confirmed": receipt["termination_confirmed"],
            "capture_complete": receipt["capture_complete"],
            "model_evaluation": False, "benchmark_status": "evidence_incomplete"}


def run_command(args):
    if args.command == "verify-probe":
        return verify_probe(args.directory)
    if args.command in ("authorize-probe-extension", "authorize-completion-probe", "authorize-validation-session"):
        prior = read_record(args.store / "ledger.json")
        with AttemptStore(args.store, prior["binding"], Limits(**prior["limits"])) as store:
            grant = (store.authorize_validation_session(args.authorization_reference)
                     if args.command == "authorize-validation-session" else store.authorize_completion(args.authorization_reference)
                     if args.command == "authorize-completion-probe"
                     else store.authorize_extension(args.authorization_reference))
            key = ("validation_session" if args.command == "authorize-validation-session" else
                   "completion_authorization" if args.command == "authorize-completion-probe" else "authorization_extension")
            return {key: grant,
                    "original_limits_preserved": True, "model_evaluation": False}
    if args.command == "recover-probe":
        from .storage import safe_id
        safe_id(args.attempt)
        prior = read_record(args.store / "ledger.json")
        prep = read_record(args.store / args.attempt / "preparation.json")
        with AttemptStore(args.store, prior["binding"], Limits(**prior["limits"])) as store:
            if prep["binding"] != prior["binding"]:
                raise InvalidManifest("recovery binding mismatch")
            adapter = DockerProbeAdapter(store, {}, prior["binding"], prep["runtime"]["image"], prep["runtime"]["context"])
            row = next((r for r in store.state["attempts"] if r["id"] == args.attempt), None)
            if row is None or row["runtime_id"] != prep["runtime_id"] or row["termination_confirmed"]:
                raise InvalidManifest("no unresolved reservation for this attempt")
            stop = adapter.cancel(WorkloadHandle(args.attempt, row["runtime_id"]))
            store.finish(args.attempt, row["runtime_id"], row["outcome"] or "execution_error", terminated=stop.terminated)
            return {"recovery": asdict(stop), "model_evaluation": False,
                    "result": "reservation_closed" if stop.terminated else "still_blocked"}
    config = read_json(args.config)
    envelope = compile_plan(config, args.root)
    files, binding = materialize_preview(config, envelope, args.root, args.case, args.variant)
    # No runtime proof can authorize or occupy a frozen model-comparison slot.
    binding = {**binding, "purpose": "infrastructure_probe_not_model_evaluation"}
    with AttemptStore(args.store, binding, Limits(**config["budget"])) as store:
        adapter = DockerProbeAdapter(store, files, binding, args.image, args.context,
                                     wait=args.wait, cancel_after=args.cancel_after)
        request = WorkerRequest(args.attempt, "infrastructure-probe", binding["plan_sha256"],
                                binding["fixture_sha256"], binding["agent_version_sha256"], args.deadline)
        if args.preflight_only:
            return {"preflight": adapter.preflight(), "attempt_reserved": False, "model_evaluation": False}
        store.check_reservation(args.attempt, args.attempt, args.deadline)
        adapter.preflight()
        try:
            handle = adapter.prepare(request)
        except subprocess.CalledProcessError as exc:
            raise InvalidManifest("Docker preparation failed: " +
                                  (exc.stderr or b"").decode(errors="replace").strip()) from exc
        outcome = adapter.run(handle, lambda event: None)
        bad = {"findings": [{"path": "not-present.py", "line": 999, "explanation": "Known bad citation for the software control."}]}
        control = {"evidence_kind": "deterministic_bad_output_control_not_model_evaluation",
                   "assessment": check_citations(bad, files)}
        write_record(args.store / args.attempt / "bad-output-control.json", control)
        return {"attempt_id": args.attempt, "execution_state": outcome.execution_state.value,
                "evidence_directory": str((args.store / args.attempt).resolve()),
                "integrity": verify_probe(args.store / args.attempt),
                "bad_output_control_status": control["assessment"]["status"],
                "milestone_a": "not_passed_model_authentication_and_real_agent_run_pending"}
