"""Real Docker execution for a fixed, credential-free infrastructure probe.

This is deliberately not a model adapter. It exercises the same preparation,
capture and termination boundary needed by the later authenticated harness.
"""
import base64
import hashlib
import io
import json
import os
import re
import selectors
import subprocess
import tarfile
import time
from pathlib import Path

from .canonical import InvalidManifest, canonical_bytes, digest
from .materialization import pack_worker
from .ports import AttemptOutcome, ExecutionState, StopConfirmation, WorkloadHandle
from .storage import file_sha256, safe_id, write_record


PROBE = b'''import hashlib, json, os, pathlib, socket, sys, time
root = pathlib.Path('/worker/fixture')
files = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(root.rglob('*')) if p.is_file()}
print(json.dumps({'event': 'fixture_read', 'files': files}), flush=True)
for path in ['/worker/fixture/prohibited-write', '/ivy-evidence/prohibited-write']:
    try:
        pathlib.Path(path).write_text('probe')
        result = 'write_succeeded'
    except OSError as exc:
        result = type(exc).__name__
    print(json.dumps({'event': 'write_probe', 'path': path, 'result': result}), flush=True)
print(json.dumps({'event': 'probe_ready', 'uid': os.getuid(),
                  'credential_environment_present': any(k in os.environ for k in
                      ['OPENAI_API_KEY', 'CODEX_API_KEY']),
                  'visible_instruction_files': sorted(p.name for p in pathlib.Path('/worker/instructions').iterdir())}), flush=True)
if sys.argv[1] == 'wait':
    time.sleep(3600)
'''


def pack_image_context(files, base_id):
    """A fixed COPY-only context; no host paths, RUN, remote ADD or build hooks."""
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", base_id):
        raise InvalidManifest("invalid local base image identity")
    buffer = io.BytesIO(pack_worker(files))
    with tarfile.open(fileobj=buffer, mode="a") as archive:
        body = ("FROM " + base_id + "\nCOPY worker/ /worker/\n").encode()
        entry = tarfile.TarInfo("Dockerfile")
        entry.size, entry.mode = len(body), 0o444
        archive.addfile(entry, io.BytesIO(body))
    return buffer.getvalue()


class DockerProbeAdapter:
    """The caller holds AttemptStore's exclusive lock for the entire workload."""
    def __init__(self, store, files, binding, image, context, *, wait=False, cancel_after=None):
        if not re.fullmatch(r"[\w./:-]+@sha256:[a-f0-9]{64}", image):
            raise InvalidManifest("runtime image must use an immutable repository digest")
        safe_id(context)
        if cancel_after is not None and (type(cancel_after) not in (float, int) or not 0 < cancel_after <= 90):
            raise InvalidManifest("invalid cancellation delay")
        self.store, self.binding = store, binding
        self.files = dict(files)
        self.files["probe.py"] = PROBE
        self.image, self.context = image, context
        self.wait, self.cancel_after = wait, cancel_after
        self.request = None
        self.path = None
        self.derived_image = None
        self.operation_deadline = None
        self.cleanup_deadline = None
        self.preparation_phase = None

    def _phase(self, phase):
        # Persist before submitting a daemon operation: a lost client response is
        # never evidence that Docker did not receive the request.
        write_record(self.path / "preparation-phase.json", {"phase": phase, "observed_at": time.time()})
        self.preparation_phase = phase

    def _remaining(self, maximum, *, cleanup=False):
        deadline = self.cleanup_deadline if cleanup else self.operation_deadline
        if deadline is None:
            return maximum
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired("Docker probe operation", 0)
        return min(maximum, remaining)

    def _cmd(self, args, *, data=None, timeout=15, env=None, cleanup=False):
        try:
            return subprocess.run(["docker", "--context", self.context, *args], input=data,
                                  capture_output=True, timeout=self._remaining(timeout, cleanup=cleanup), check=True, env=env)
        except subprocess.SubprocessError as exc:
            if self.path is not None:
                write_record(self.path / ("command-error-" + str(time.time_ns()) + ".json"), {
                    "arguments": args, "error": type(exc).__name__,
                    "returncode": getattr(exc, "returncode", None),
                    "stdout": (getattr(exc, "stdout", None) or b"").decode(errors="replace"),
                    "stderr": (getattr(exc, "stderr", None) or b"").decode(errors="replace"),
                    "input_sha256": hashlib.sha256(data).hexdigest() if data is not None else None})
            raise

    def describe(self):
        return {"available": True, "kind": "runtime_probe", "model_execution": False,
                "image": self.image, "context": self.context, "network": "none",
                "read_only_root": True, "host_mounts": [], "credentials": "none",
                "derived_image": self.derived_image,
                "capture_scope": "Docker stdout/stderr and supervisor lifecycle; not an agent tool trace"}

    def preflight(self):
        """Read Docker through the execution path before reserving any workload.

        Evidence writes test store access. This cannot prove a future build will
        succeed, and prepare repeats image checks to handle intervening changes.
        """
        if self.request is not None:
            raise InvalidManifest("preflight must precede attempt reservation")
        path = self.store.directory / ("preflight-" + str(time.time_ns()) + ".json")
        record = {"kind": "setup_preflight_not_worker_attempt", "status": "checking",
                  "context": self.context, "image": self.image, "workload_submitted": False}
        write_record(path, record)
        previous_deadline = self.operation_deadline
        self.operation_deadline = time.monotonic() + 15
        try:
            context = json.loads(self._cmd(["context", "inspect", self.context]).stdout)[0]
            if context["Name"] != self.context:
                raise InvalidManifest("Docker context mismatch")
            server = json.loads(self._cmd(["version", "--format", "{{json .Server}}"]).stdout)
            if not server or not server.get("Version"):
                raise InvalidManifest("Docker daemon unavailable")
            base = json.loads(self._cmd(["image", "inspect", self.image]).stdout)[0]
            if (not re.fullmatch(r"sha256:[a-f0-9]{64}", base["Id"])
                    or base["Config"].get("OnBuild") or base["Config"].get("Volumes")):
                raise InvalidManifest("invalid base identity, build hooks or volumes")
            record.update(status="ready", server_version=server["Version"], base_id=base["Id"])
        except (Exception, KeyboardInterrupt) as exc:
            record.update(status="failed", error=type(exc).__name__ + ": " + str(exc),
                          stderr=(getattr(exc, "stderr", None) or b"").decode(errors="replace"))
            write_record(path, record)
            raise
        finally:
            self.operation_deadline = previous_deadline
        write_record(path, record)
        return {"status": "ready", "evidence_reference": path.name, "workload_submitted": False}

    def _inspect(self, handle, *, cleanup=False):
        info = json.loads(self._cmd(["container", "inspect", handle.runtime_id], cleanup=cleanup).stdout)[0]
        labels = info["Config"].get("Labels") or {}
        if (labels.get("ivy.attempt") != handle.attempt_id
                or labels.get("ivy.binding") != digest(self.binding)):
            raise InvalidManifest("container ownership mismatch")
        return info

    def prepare(self, request):
        if self.request is not None:
            raise InvalidManifest("adapter already owns an attempt")
        try:
            return self._prepare(request)
        except (Exception, KeyboardInterrupt) as exc:
            if self.path is not None and self.preparation_phase is not None:
                # Before build submission this adapter has issued only reads.
                # During/after a failed build, no final container is insufficient
                # to establish daemon-side shutdown, so keep the reservation open.
                terminated = self.preparation_phase == "before_build"
                stop = None
                if self.preparation_phase in ("create_submitted", "created"):
                    row = next(r for r in self.store.state["attempts"] if r["id"] == request.attempt_id)
                    stop = self.cancel(WorkloadHandle(request.attempt_id, row["runtime_id"]))
                    terminated = stop.terminated
                state = (ExecutionState.CANCELED if isinstance(exc, KeyboardInterrupt) else
                         ExecutionState.TIMED_OUT if isinstance(exc, subprocess.TimeoutExpired)
                         else ExecutionState.EXECUTION_ERROR)
                write_record(self.path / "preparation-failure.json", {
                    "phase": self.preparation_phase, "error": type(exc).__name__ + ": " + str(exc),
                    "execution_state": state.value, "termination_confirmed": terminated,
                    "termination_basis": "no_workload_submitted" if self.preparation_phase == "before_build"
                        else "container_inspection" if stop is not None else "daemon_build_unconfirmed",
                    "stop_evidence": Path(stop.evidence_reference).name if stop else None,
                    "evidence_kind": "infrastructure_preparation_failure_not_model_evaluation"})
                row = next(r for r in self.store.state["attempts"] if r["id"] == request.attempt_id)
                self.store.finish(request.attempt_id, row["runtime_id"], state.value, terminated=terminated)
            raise

    def _prepare(self, request):
        if (self.request is not None or request.comparison_sha256 != self.binding["plan_sha256"]
                or request.worker_snapshot_sha256 != self.binding["fixture_sha256"]
                or request.agent_version_sha256 != self.binding["agent_version_sha256"]):
            raise InvalidManifest("request is not bound to these materialized inputs")
        safe_id(request.attempt_id)
        name = "ivy-" + hashlib.sha256((str(self.store.directory.resolve()) + request.attempt_id).encode()).hexdigest()[:32]
        handle = WorkloadHandle(request.attempt_id, name)
        # One monotonic execution deadline includes reserve, preparation and run.
        self.operation_deadline = time.monotonic() + request.deadline_seconds
        self.store.reserve(request.attempt_id, name, request.deadline_seconds)
        self.request = request
        self.path = self.store.directory / request.attempt_id
        self.path.mkdir(mode=0o700)  # Existing evidence is never reused.
        self._phase("before_build")
        write_record(self.path / "preparation.json", {
            "binding": self.binding, "runtime": self.describe(), "runtime_id": name,
            "visible_files": {k: hashlib.sha256(v).hexdigest() for k, v in sorted(self.files.items())},
            "deadline_seconds": request.deadline_seconds,
            "deadline_scope": "preparation_and_run", "shutdown_grace_seconds": 15,
            "evidence_kind": "infrastructure_probe_not_model_evaluation"})
        # Resolve the already-local pinned base before building. The legacy builder
        # accepts its content ID directly without a registry resolver. No fallback
        # or engine installation is attempted if this Docker capability is absent.
        base = json.loads(self._cmd(["image", "inspect", self.image]).stdout)[0]
        if base["Config"].get("OnBuild") or base["Config"].get("Volumes"):
            raise InvalidManifest("base image must not define build hooks or volumes")
        context = pack_image_context(self.files, base["Id"])
        write_record(self.path / "image-input.json", {
            "base_image": self.image, "base_id": base["Id"],
            "context_sha256": hashlib.sha256(context).hexdigest(),
            "dockerfile": "FROM " + base["Id"] + "\nCOPY worker/ /worker/\n"})
        self._phase("build_submitted")
        built = self._cmd(["build", "--network", "none", "--pull=false", "--no-cache",
                           "--tag", name + ":probe", "-"], data=context, timeout=60,
                          env={**os.environ, "DOCKER_BUILDKIT": "0"})
        self._phase("build_finished")
        derived = json.loads(self._cmd(["image", "inspect", name + ":probe"]).stdout)[0]
        self.derived_image = derived["Id"]
        if not re.fullmatch(r"sha256:[a-f0-9]{64}", self.derived_image):
            raise InvalidManifest("invalid derived image identity")
        write_record(self.path / "image-build.json", {
            "base_image": self.image, "base_id": base["Id"], "derived_image": self.derived_image,
            "context_sha256": hashlib.sha256(context).hexdigest(),
            "stdout": built.stdout.decode(errors="replace"), "stderr": built.stderr.decode(errors="replace")})
        # Reservation already names the container, even if create's response is lost.
        self._phase("create_submitted")
        self._cmd(["create", "--name", name, "--label", "ivy.attempt=" + request.attempt_id,
                   "--label", "ivy.binding=" + digest(self.binding), "--read-only",
                   "--network", "none", "--user", "65534:65534", "--cap-drop", "ALL",
                   "--security-opt", "no-new-privileges=true", "--pids-limit", "64",
                   "--memory", "256m", "--cpus", "1", "--restart", "no",
                   "--log-driver", "local", "--log-opt", "max-size=1m", "--log-opt", "max-file=1",
                   "--log-opt", "compress=false",
                   "--entrypoint", "python3", self.derived_image, "-I", "-B", "-u",
                   "/worker/probe.py", "wait" if self.wait else "complete"])
        self._phase("created")
        info = self._inspect(handle)
        hc = info["HostConfig"]
        if (info["Image"] != self.derived_image or info["Mounts"] or not hc["ReadonlyRootfs"] or hc["NetworkMode"] != "none"
                or info["Config"]["User"] != "65534:65534" or hc["Privileged"]
                or hc["CapDrop"] != ["ALL"] or "no-new-privileges=true" not in hc["SecurityOpt"]):
            raise InvalidManifest("effective container isolation does not match the probe")
        write_record(self.path / "prepared.json", {"container": info, "prepared_at": time.time()})
        return handle

    def cancel(self, handle):
        """Confirm the attempt-owned container stopped, independently of its client."""
        path = self.store.directory / safe_id(handle.attempt_id)
        terminated, info, error = False, None, None
        # Safety shutdown has its own single bounded grace, including every CLI
        # call. Expired execution time must not prevent container termination.
        if self.cleanup_deadline is None:
            self.cleanup_deadline = time.monotonic() + 15
        try:
            info = self._inspect(handle, cleanup=True)
            if info["State"]["Running"] or info["State"].get("Restarting"):
                self._cmd(["kill", handle.runtime_id], cleanup=True)
                info = self._inspect(handle, cleanup=True)
            terminated = (info["State"]["Status"] in ("exited", "dead", "created")
                          and not info["State"]["Running"] and not info["State"].get("Restarting"))
        except (OSError, subprocess.SubprocessError, ValueError, KeyError) as exc:
            # An unreachable daemon or missing container is not proof of shutdown.
            error = type(exc).__name__ + ": " + str(exc)
        evidence = path / ("stop-" + str(time.time_ns()) + ".json")
        write_record(evidence, {"runtime_id": handle.runtime_id, "termination_confirmed": terminated,
                                "container": info, "error": error, "observed_at": time.time()})
        return StopConfirmation(handle.runtime_id, terminated, str(evidence))

    def run(self, handle, emit):
        if self.request is None or handle.attempt_id != self.request.attempt_id:
            raise InvalidManifest("adapter has not prepared this attempt")
        capture = self.path / "events.jsonl"
        state, process = ExecutionState.EXECUTION_ERROR, None
        complete, total, sequence = False, 0, 0
        error = None
        started = time.monotonic()
        control = None
        try:
            self._inspect(handle)
            with open(capture, "xb", buffering=0) as output, selectors.DefaultSelector() as selector:
                def event(kind, **values):
                    nonlocal sequence
                    sequence += 1
                    record = {"sequence": sequence, "supervisor_elapsed_seconds": time.monotonic() - started,
                              "kind": kind, **values}
                    output.write(canonical_bytes(record) + b"\n")
                    emit(record)

                event("start_requested", runtime_id=handle.runtime_id)
                self._remaining(1)  # Never start after preparation consumed the deadline.
                process = subprocess.Popen(["docker", "--context", self.context, "start", "--attach", handle.runtime_id],
                                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for stream, channel in ((process.stdout, "stdout"), (process.stderr, "stderr")):
                    selector.register(stream, selectors.EVENT_READ, channel)
                while selector.get_map():
                    elapsed = time.monotonic() - started
                    deadline_reached = time.monotonic() >= self.operation_deadline
                    if deadline_reached or (self.cancel_after is not None and elapsed >= self.cancel_after):
                        state = ExecutionState.TIMED_OUT if deadline_reached else ExecutionState.CANCELED
                        event("stop_requested", reason=state.value)
                        control = self.cancel(handle)
                        break
                    for key, _ in selector.select(timeout=0.05):
                        chunk = os.read(key.fileobj.fileno(), 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        total += len(chunk)
                        if total > 1024 * 1024:
                            raise RuntimeError("capture byte limit exceeded; evidence is incomplete")
                        event("worker_stream", channel=key.data, data_base64=base64.b64encode(chunk).decode())
                else:
                    process.wait(timeout=self._remaining(5))
                    info = self._inspect(handle)
                    complete = True
                    state = (ExecutionState.COMPLETED if process.returncode == 0 and info["State"]["ExitCode"] == 0
                             else ExecutionState.EXECUTION_ERROR)
                    event("stream_closed", exit_code=info["State"]["ExitCode"])
                os.fsync(output.fileno())
        except (Exception, KeyboardInterrupt) as exc:
            error = type(exc).__name__ + ": " + str(exc)
            state = (ExecutionState.CANCELED if isinstance(exc, KeyboardInterrupt) else
                     ExecutionState.TIMED_OUT if isinstance(exc, subprocess.TimeoutExpired) else ExecutionState.EXECUTION_ERROR)
        finally:
            control = control or self.cancel(handle)
            client_cleanup_error = None
            if process is not None:
                try:
                    if process.poll() is None:
                        process.kill()  # Client cleanup never supplies termination evidence.
                        process.wait(timeout=self._remaining(5, cleanup=True))
                except (OSError, subprocess.SubprocessError) as exc:
                    client_cleanup_error = type(exc).__name__ + ": " + str(exc)
                    complete = False
                    if state == ExecutionState.COMPLETED:
                        state = ExecutionState.EXECUTION_ERROR
                finally:
                    process.stdout.close()
                    process.stderr.close()
            receipt = {"schema_version": 1, "evidence_kind": "infrastructure_probe_not_model_evaluation",
                       "binding": self.binding, "runtime": self.describe(), "attempt_id": handle.attempt_id,
                       "runtime_id": handle.runtime_id, "execution_state": state.value,
                       "capture_sha256": file_sha256(capture) if capture.exists() else None,
                       "capture_complete": complete and control.terminated,
                       "termination_confirmed": control.terminated,
                       "stop_evidence": Path(control.evidence_reference).name,
                       "requested_model": None, "observed_model": None,
                       "observed_effort": None, "usage": None, "error": error,
                       "client_cleanup_error": client_cleanup_error}
            receipt["artifact_sha256"] = {
                name: file_sha256(self.path / name)
                for name in ("preparation.json", "prepared.json", "image-input.json", "image-build.json",
                             "events.jsonl", receipt["stop_evidence"])
                if (self.path / name).exists()}
            write_record(self.path / "receipt.json", receipt)
            self.store.finish(handle.attempt_id, handle.runtime_id, state.value, terminated=control.terminated)
        return AttemptOutcome(state, handle, receipt["capture_sha256"], None, None, None)
