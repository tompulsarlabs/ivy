"""Setup checks use the same Docker path but never consume a worker attempt."""
import argparse
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ivy_acceptance.budget import Limits
from ivy_acceptance.docker_probe import DockerProbeAdapter
from ivy_acceptance.probe_cli import add_commands, run_command
from ivy_acceptance.storage import AttemptStore, read_record

ROOT = Path(__file__).resolve().parents[1]


class PreflightTests(unittest.TestCase):
    def responses(self):
        return [SimpleNamespace(stdout=json.dumps(value).encode()) for value in (
            [{"Name": "test-context"}], {"Version": "test-daemon"},
            [{"Id": "sha256:" + "a" * 64, "Config": {}}])]

    def test_success_only_reads_docker_and_keeps_ledger_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with AttemptStore(tmp, {}, Limits(32, 90, 3600)) as store:
                before = (Path(tmp) / "ledger.json").read_bytes()
                adapter = DockerProbeAdapter(store, {}, {}, "python@sha256:" + "a" * 64, "test-context")
                with patch.object(adapter, "_cmd", side_effect=self.responses()) as command:
                    result = adapter.preflight()
                self.assertEqual(result["status"], "ready")
                self.assertEqual([call.args[0][0] for call in command.call_args_list], ["context", "version", "image"])
                self.assertIsNone(adapter.operation_deadline)
                self.assertEqual((Path(tmp) / "ledger.json").read_bytes(), before)

    def test_cli_permission_denial_is_setup_evidence_without_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            parser = argparse.ArgumentParser()
            add_commands(parser.add_subparsers(dest="command"))
            args = parser.parse_args(["probe", str(ROOT / "examples/acceptance/preview.json"),
                                     "--root", str(ROOT), "--store", tmp, "--image", "python@sha256:" + "a" * 64,
                                     "--context", "test-context", "--attempt", "never-reserved"])
            failure = subprocess.CalledProcessError(1, "docker", stderr=b"permission denied")
            with patch.object(DockerProbeAdapter, "_cmd", side_effect=failure), patch.object(
                    DockerProbeAdapter, "prepare") as prepare:
                with self.assertRaises(subprocess.CalledProcessError):
                    run_command(args)
                prepare.assert_not_called()
            self.assertEqual(read_record(Path(tmp) / "ledger.json")["attempts"], [])
            self.assertFalse((Path(tmp) / "never-reserved").exists())
            evidence = list(Path(tmp).glob("preflight-*.json"))
            self.assertEqual(len(evidence), 1)
            self.assertEqual(read_record(evidence[0])["status"], "failed")
            self.assertEqual(read_record(evidence[0])["stderr"], "permission denied")

    def test_expired_setup_deadline_cannot_dispatch_another_docker_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            with AttemptStore(tmp, {}, Limits(32, 90, 3600)) as store:
                adapter = DockerProbeAdapter(store, {}, {}, "python@sha256:" + "a" * 64, "test-context")
                before = (Path(tmp) / "ledger.json").read_bytes()
                with patch("ivy_acceptance.docker_probe.time.monotonic", side_effect=[0, 16]), patch(
                        "ivy_acceptance.docker_probe.subprocess.run") as command:
                    with self.assertRaises(subprocess.TimeoutExpired):
                        adapter.preflight()
                    command.assert_not_called()
                self.assertEqual((Path(tmp) / "ledger.json").read_bytes(), before)
