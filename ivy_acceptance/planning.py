"""Compile a read-only, content-bound plan. Never starts a harness or approves a run."""
import hashlib
import json
import re
from .canonical import InvalidManifest, canonical_bytes, contained_path, digest, read_json, snapshot_tree

VARIANTS = ("baseline", "changed")


def exact_keys(value, keys, label):
    if type(value) is not dict or set(value) != set(keys):
        raise InvalidManifest(f"{label}: expected exactly {sorted(keys)}")


def positive_int(value, label):
    if type(value) is not int or value <= 0:
        raise InvalidManifest(f"{label}: expected positive integer")
    return value


def identifier(value, label):
    if type(value) is not str or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise InvalidManifest(f"{label}: expected letters, numbers, underscore or hyphen")
    return value


def _optional_text(value, label):
    if value is not None and (type(value) is not str or not value.strip()):
        raise InvalidManifest(f"{label}: expected nonempty text or null")


def primary_slots(case_ids, repetitions, seed):
    positive_int(repetitions, "repetitions")
    if type(seed) is not int:
        raise InvalidManifest("order_seed: expected integer")
    if type(case_ids) is not list or not case_ids:
        raise InvalidManifest("cases must be a nonempty list")
    for case in case_ids:
        identifier(case, "case id")
    if len(set(case_ids)) != len(case_ids):
        raise InvalidManifest("duplicate case id")
    slots = []
    for case in case_ids:
        for repetition in range(1, repetitions + 1):
            flip = hashlib.sha256(f"{seed}:{case}:{repetition}".encode()).digest()[0] % 2
            order = VARIANTS if not flip else tuple(reversed(VARIANTS))
            for variant in order:
                slots.append({"id": f"{case}.{repetition}.{variant}", "case_id": case,
                              "repetition": repetition, "variant": variant})
    return slots


def validate_schedule(slots, case_ids, repetitions, seed):
    if slots != primary_slots(case_ids, repetitions, seed):
        raise InvalidManifest("primary schedule differs from the frozen paired schedule")


def compile_plan(config, root):
    # Detach every nested value from caller-owned mutable configuration.
    config = json.loads(canonical_bytes(config))
    exact_keys(config, {"schema_version", "comparison_id", "workflow_id", "cases",
                       "variants", "runtime", "repetitions", "order_seed", "budget"}, "config")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise InvalidManifest("unsupported schema version")
    for key in ("comparison_id", "workflow_id"):
        identifier(config[key], key)
    exact_keys(config["variants"], VARIANTS, "variants")
    runtime = config["runtime"]
    exact_keys(runtime, {"harness", "harness_version", "requested_model", "requested_effort",
                         "environment_sha256", "tools", "visibility_gaps"}, "runtime")
    identifier(runtime["harness"], "harness")
    for key in ("harness_version", "requested_model", "requested_effort", "environment_sha256"):
        _optional_text(runtime[key], key)
    if runtime["environment_sha256"] is not None and not re.fullmatch(r"[0-9a-f]{64}", runtime["environment_sha256"]):
        raise InvalidManifest("environment_sha256: expected SHA-256")
    for key in ("tools", "visibility_gaps"):
        items = runtime[key]
        if type(items) is not list or any(type(x) is not str or not x.strip() for x in items):
            raise InvalidManifest(f"{key}: expected text list")
        if len(set(items)) != len(items):
            raise InvalidManifest(f"{key}: duplicates are not allowed")
    budget = config["budget"]
    exact_keys(budget, {"max_attempts", "per_attempt_seconds", "total_seconds"}, "budget")
    for key, value in budget.items():
        positive_int(value, key)
    cases = config["cases"]
    if type(cases) is not list or not cases:
        raise InvalidManifest("cases must be a nonempty list")
    case_records, blockers, case_ids = [], ["live_adapter_not_implemented"], []
    visible_roots, grader_roots = [], []
    for case in cases:
        exact_keys(case, {"id", "worker_dir", "grader_dir"}, "case")
        identifier(case["id"], "case id")
        worker = contained_path(root, case["worker_dir"])
        grader = contained_path(root, case["grader_dir"])
        if worker == grader or worker in grader.parents or grader in worker.parents:
            raise InvalidManifest("worker and grader trees must be disjoint")
        visible_roots.append(worker)
        grader_roots.append(grader)
        visible, hidden = snapshot_tree(worker), snapshot_tree(grader)
        if not any(f["path"] == "task.md" for f in visible):
            raise InvalidManifest("worker tree requires neutral task.md")
        labels = read_json(grader / "labels.json")
        if (type(labels) is not dict or type(labels.get("schema_version")) is not int
                or labels["schema_version"] != 1 or labels.get("case_id") != case["id"]):
            raise InvalidManifest("grader labels do not identify this case/version")
        criteria = labels.get("criteria")
        if type(criteria) is not list or not criteria:
            raise InvalidManifest("grader requires explicit criteria")
        criterion_ids = []
        for criterion in criteria:
            exact_keys(criterion, {"id", "critical", "description"}, "criterion")
            identifier(criterion["id"], "criterion id")
            if type(criterion["critical"]) is not bool or type(criterion["description"]) is not str or not criterion["description"].strip():
                raise InvalidManifest("invalid criterion")
            criterion_ids.append(criterion["id"])
        if len(set(criterion_ids)) != len(criterion_ids):
            raise InvalidManifest("duplicate criterion id")
        # This is descriptive metadata, not authenticated reviewer authority.
        if labels.get("status") != "owner_reviewed" or not labels.get("acceptance_owner"):
            blockers.append(f"{case['id']}:owner_review_pending")
        case_records.append({"id": case["id"], "worker_files": visible,
                             "fixture_sha256": digest(visible), "grader_files": hidden,
                             "rubric_sha256": digest(hidden), "criteria": criteria})
        case_ids.append(case["id"])
    slots = primary_slots(case_ids, config["repetitions"], config["order_seed"])
    if len(slots) > budget["max_attempts"] or len(slots) * budget["per_attempt_seconds"] > budget["total_seconds"]:
        raise InvalidManifest("planned primary slots exceed the attempt/time budget")
    variants = {}
    for variant in VARIANTS:
        entry = config["variants"][variant]
        exact_keys(entry, {"instructions_dir"}, variant)
        instructions = contained_path(root, entry["instructions_dir"])
        visible_roots.append(instructions)
        files = snapshot_tree(instructions)
        version = {"schema_version": 1, "runtime": runtime, "instruction_files": files}
        variants[variant] = {"agent_version": version, "agent_version_sha256": digest(version)}
    for visible_root in visible_roots:
        for grader_root in grader_roots:
            if (visible_root == grader_root or visible_root in grader_root.parents
                    or grader_root in visible_root.parents):
                raise InvalidManifest("all worker-visible trees must be disjoint from all grader trees")
    for key in ("harness_version", "requested_model", "requested_effort", "environment_sha256"):
        if runtime[key] is None:
            blockers.append(f"runtime:{key}_unresolved")
    if runtime["visibility_gaps"]:
        blockers.append("runtime:visibility_gaps_require_preflight")
    benchmark = {"schema_version": 1, "workflow_id": config["workflow_id"], "cases": case_records,
                 "policy": "all_required_primary_checks_v1"}
    plan = {"schema_version": 1, "comparison_id": config["comparison_id"], "phase": "scaffold_preview",
            "benchmark": benchmark, "benchmark_sha256": digest(benchmark), "variants": variants,
            "primary_slots": slots, "repetitions": config["repetitions"], "order_seed": config["order_seed"],
            "budget": budget, "execution_ready": False, "blockers": blockers}
    # Detached digest: never include a plan's own hash inside its hashed bytes.
    # JSON normalization also removes aliases shared between the two variants.
    return json.loads(canonical_bytes({"plan": plan, "plan_sha256": digest(plan)}))
