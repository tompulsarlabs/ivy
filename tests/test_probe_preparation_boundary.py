"""Independent source-boundary controls; no Docker or model execution."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from ivy_acceptance.budget import BudgetBlocked, Limits
from ivy_acceptance.canonical import InvalidManifest
from ivy_acceptance.docker_probe import DockerProbeAdapter
from ivy_acceptance.ports import WorkerRequest, WorkloadHandle
from ivy_acceptance.storage import AttemptStore, read_record


class PreparationBoundaryTests(unittest.TestCase):
    binding = {"plan_sha256": "a" * 64, "fixture_sha256": "b" * 64,
               "agent_version_sha256": "c" * 64}

    def adapter(self, store):
        return DockerProbeAdapter(store, {}, self.binding,
                                  "python@sha256:" + "d" * 64, "synthetic")

    def request(self):
        return WorkerRequest("attempt", "probe", "a" * 64, "b" * 64, "c" * 64, 10)

    def test_inherited_build_hooks_and_volumes_fail_before_build(self):
        for config in ({"OnBuild": ["RUN untrusted"]}, {"Volumes": {"/data": {}}}):
            with self.subTest(config=config), tempfile.TemporaryDirectory() as tmp:
                with AttemptStore(tmp, self.binding, Limits(32, 90, 3600)) as store:
                    adapter = self.adapter(store)
                    response = SimpleNamespace(stdout=json.dumps(
                        [{"Id": "sha256:" + "e" * 64, "Config": config}]).encode())
                    with patch.object(adapter, "_cmd", return_value=response) as command:
                        with self.assertRaisesRegex(InvalidManifest, "build hooks or volumes"):
                            adapter.prepare(self.request())
                        self.assertEqual(command.call_count, 1)
                        self.assertEqual(command.call_args.args[0][:2], ["image", "inspect"])
                    self.assertTrue(store.state["attempts"][0]["termination_confirmed"])
                    failure = read_record(Path(tmp) / "attempt" / "preparation-failure.json")
                    self.assertEqual(failure["termination_basis"], "no_workload_submitted")
                    self.assertEqual(failure["execution_state"], "execution_error")

    def test_preparation_timeout_survives_restart_and_blocks_next_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            with AttemptStore(tmp, self.binding, Limits(32, 90, 3600)) as store:
                adapter = self.adapter(store)
                base = SimpleNamespace(stdout=json.dumps(
                    [{"Id": "sha256:" + "e" * 64, "Config": {}}]).encode())
                with patch.object(adapter, "_cmd", side_effect=[base, subprocess.TimeoutExpired("docker", 10)]):
                    with self.assertRaises(subprocess.TimeoutExpired):
                        adapter.prepare(self.request())
            self.assertEqual(read_record(Path(tmp) / "attempt" / "preparation.json")
                             ["deadline_scope"], "preparation_and_run")
            with AttemptStore(tmp, self.binding, Limits(32, 90, 3600)) as store:
                self.assertEqual(len(store.state["attempts"]), 1)
                self.assertEqual(store.state["attempts"][0]["outcome"], "timed_out")
                failure = read_record(Path(tmp) / "attempt" / "preparation-failure.json")
                self.assertEqual(failure["phase"], "build_submitted")
                self.assertEqual(failure["termination_basis"], "daemon_build_unconfirmed")
                with self.assertRaises(BudgetBlocked):
                    store.reserve("next", "next-container", 10)

    def test_missing_base_closes_only_never_submitted_work_and_retains_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            with AttemptStore(tmp, self.binding, Limits(32, 90, 3600)) as store:
                adapter = self.adapter(store)
                with patch.object(adapter, "_cmd", side_effect=subprocess.CalledProcessError(1, "docker")) as command:
                    with self.assertRaises(subprocess.CalledProcessError):
                        adapter.prepare(self.request())
                    self.assertEqual(command.call_count, 1)
            with AttemptStore(tmp, self.binding, Limits(32, 90, 3600)) as store:
                self.assertTrue(store.state["attempts"][0]["termination_confirmed"])
                with self.assertRaises(BudgetBlocked):
                    store.reserve("attempt", "other", 10)
                store.reserve("next", "next-container", 10)

    def test_interrupted_build_stays_unconfirmed_and_keeps_failure(self):
        for error in (KeyboardInterrupt(), subprocess.CalledProcessError(1, "docker")):
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory() as tmp:
                with AttemptStore(tmp, self.binding, Limits(32, 90, 3600)) as store:
                    adapter = self.adapter(store)
                    base = SimpleNamespace(stdout=json.dumps(
                        [{"Id": "sha256:" + "e" * 64, "Config": {}}]).encode())
                    with patch.object(adapter, "_cmd", side_effect=[base, error]):
                        with self.assertRaises(type(error)):
                            adapter.prepare(self.request())
                    self.assertFalse(store.state["attempts"][0]["termination_confirmed"])
                    failure = read_record(Path(tmp) / "attempt" / "preparation-failure.json")
                    self.assertEqual(failure["phase"], "build_submitted")
                    self.assertEqual(failure["execution_state"],
                                     "canceled" if isinstance(error, KeyboardInterrupt) else "execution_error")
                    with self.assertRaises(BudgetBlocked):
                        store.reserve("next", "next-container", 10)

    def test_lost_create_response_attempts_owned_shutdown(self):
        for stopped in (True, False):
            with self.subTest(stopped=stopped), tempfile.TemporaryDirectory() as tmp:
                from ivy_acceptance.ports import StopConfirmation
                with AttemptStore(tmp, self.binding, Limits(32, 90, 3600)) as store:
                    adapter = self.adapter(store)
                    base = SimpleNamespace(stdout=json.dumps(
                        [{"Id": "sha256:" + "e" * 64, "Config": {}}]).encode())
                    build = SimpleNamespace(stdout=b"built", stderr=b"")
                    derived = SimpleNamespace(stdout=json.dumps([{"Id": "sha256:" + "f" * 64}]).encode())
                    with patch.object(adapter, "_cmd", side_effect=[base, build, derived,
                            subprocess.TimeoutExpired("docker create", 10)]), patch.object(adapter, "cancel") as cancel:
                        cancel.side_effect = lambda handle: StopConfirmation(handle.runtime_id, stopped, "stop.json")
                        with self.assertRaises(subprocess.TimeoutExpired):
                            adapter.prepare(self.request())
                        self.assertEqual(cancel.call_args.args[0].runtime_id, store.state["attempts"][0]["runtime_id"])
                    self.assertEqual(store.state["attempts"][0]["termination_confirmed"], stopped)
                    self.assertEqual(read_record(Path(tmp) / "attempt" / "preparation-failure.json")["phase"],
                                     "create_submitted")

    def test_unreachable_container_cannot_close_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            with AttemptStore(tmp, self.binding, Limits(32, 90, 3600)) as store:
                store.reserve("attempt", "owned", 10)
                (Path(tmp) / "attempt").mkdir()
                adapter = self.adapter(store)
                failure = subprocess.CalledProcessError(1, "docker", stderr=b"unreachable")
                with patch.object(adapter, "_cmd", side_effect=failure):
                    result = adapter.cancel(WorkloadHandle("attempt", "owned"))
                self.assertFalse(result.terminated)
                store.finish("attempt", "owned", "execution_error", terminated=result.terminated)
                with self.assertRaises(BudgetBlocked):
                    store.reserve("next", "next-container", 10)

    def test_expired_client_cleanup_keeps_receipt_and_container_confirmation(self):
        from ivy_acceptance.ports import StopConfirmation
        with tempfile.TemporaryDirectory() as tmp:
            with AttemptStore(tmp, self.binding, Limits(32, 90, 3600)) as store:
                store.reserve("attempt", "owned", 10)
                path = Path(tmp) / "attempt"
                path.mkdir()
                adapter = self.adapter(store)
                adapter.path, adapter.request = path, self.request()
                adapter.operation_deadline, adapter.cancel_after = 100, 1
                process = MagicMock()
                process.poll.return_value = None
                clock = iter((0, 0, 2, 2, 2))
                with patch.object(adapter, "_inspect", return_value={}), patch.object(
                        adapter, "cancel", return_value=StopConfirmation("owned", True, "stop.json")), patch.object(
                        adapter, "_remaining", side_effect=[1, subprocess.TimeoutExpired("cleanup", 0)]), patch(
                        "ivy_acceptance.docker_probe.time.monotonic", side_effect=lambda: next(clock, 2)), patch(
                        "ivy_acceptance.docker_probe.subprocess.Popen", return_value=process), patch(
                        "ivy_acceptance.docker_probe.selectors.DefaultSelector"):
                    adapter.run(WorkloadHandle("attempt", "owned"), lambda event: None)
                receipt = read_record(path / "receipt.json")
                self.assertEqual(receipt["execution_state"], "canceled")
                self.assertTrue(receipt["termination_confirmed"])
                self.assertFalse(receipt["capture_complete"])
                self.assertIn("TimeoutExpired", receipt["client_cleanup_error"])
                process.kill.assert_called_once()
                process.wait.assert_not_called()  # Expired grace cannot add another five seconds.
                self.assertTrue(store.state["attempts"][0]["termination_confirmed"])
