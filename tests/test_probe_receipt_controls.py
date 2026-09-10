"""Synthetic evidence controls. These tests never constitute a Docker run."""
import io
import json
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ivy_acceptance.canonical import InvalidManifest
from ivy_acceptance.docker_probe import DockerProbeAdapter, pack_image_context
from ivy_acceptance.probe_cli import verify_probe
from ivy_acceptance.storage import file_sha256, read_record, write_record


class ImagePreparationControls(unittest.TestCase):
    def test_all_commands_share_remaining_operation_time(self):
        adapter = DockerProbeAdapter(None, {}, {}, "python@sha256:" + "a" * 64, "test-context")
        adapter.operation_deadline = 100
        with patch("ivy_acceptance.docker_probe.time.monotonic", return_value=98), patch(
                "ivy_acceptance.docker_probe.subprocess.run") as run:
            adapter._cmd(["build"], timeout=60)
            self.assertEqual(run.call_args.kwargs["timeout"], 2)
        with patch("ivy_acceptance.docker_probe.time.monotonic", return_value=101), patch(
                "ivy_acceptance.docker_probe.subprocess.run") as run:
            with self.assertRaises(subprocess.TimeoutExpired):
                adapter._cmd(["create"])
            run.assert_not_called()

    def test_cleanup_has_one_grace_and_does_not_reopen_execution(self):
        adapter = DockerProbeAdapter(None, {}, {}, "python@sha256:" + "a" * 64, "test-context")
        adapter.operation_deadline, adapter.cleanup_deadline = 100, 115
        with patch("ivy_acceptance.docker_probe.time.monotonic", return_value=110), patch(
                "ivy_acceptance.docker_probe.subprocess.run") as run:
            adapter._cmd(["kill", "owned"], cleanup=True)
            self.assertEqual(run.call_args.kwargs["timeout"], 5)
            with self.assertRaises(subprocess.TimeoutExpired):
                adapter._cmd(["start", "owned"])
        with patch("ivy_acceptance.docker_probe.time.monotonic", return_value=116), patch(
                "ivy_acceptance.docker_probe.subprocess.run") as run:
            with self.assertRaises(subprocess.TimeoutExpired):
                adapter._cmd(["container", "inspect", "owned"], cleanup=True)
            run.assert_not_called()

    def test_build_context_contains_only_fixed_recipe_and_selected_bytes(self):
        files = {"fixture/head/code.py": b"print(1)\n", "instructions/AGENTS.md": b"Review only.\n"}
        image = "sha256:" + "a" * 64
        body = pack_image_context(files, image)
        self.assertEqual(body, pack_image_context(files, image))
        with tarfile.open(fileobj=io.BytesIO(body)) as archive:
            entries = {entry.name: entry for entry in archive if entry.isfile()}
            self.assertEqual(set(entries), {"Dockerfile", *("worker/" + name for name in files)})
            self.assertEqual(archive.extractfile("Dockerfile").read(),
                             ("FROM " + image + "\nCOPY worker/ /worker/\n").encode())
            for name, expected in files.items():
                self.assertEqual(archive.extractfile("worker/" + name).read(), expected)
                self.assertEqual(entries["worker/" + name].mode, 0o444)

    def test_recipe_rejects_mutable_or_injected_base_identity(self):
        for base in ("python:latest", "sha256:" + "a" * 64 + "\nRUN false"):
            with self.assertRaises(InvalidManifest):
                pack_image_context({}, base)

    def test_subprocess_error_retains_diagnostic_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = DockerProbeAdapter(None, {}, {}, "python@sha256:" + "a" * 64, "test-context")
            adapter.path = Path(tmp)
            failure = subprocess.CalledProcessError(1, ["docker"], output=b"partial", stderr=b"builder unavailable")
            with patch("ivy_acceptance.docker_probe.subprocess.run", side_effect=failure):
                with self.assertRaises(subprocess.CalledProcessError):
                    adapter._cmd(["build"], data=b"synthetic-context")
            records = list(adapter.path.glob("command-error-*.json"))
            self.assertEqual(len(records), 1)
            record = read_record(records[0])
            self.assertEqual(record["returncode"], 1)
            self.assertEqual(record["stderr"], "builder unavailable")
            self.assertEqual(record["stdout"], "partial")


class SyntheticReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.base = "python@sha256:" + "a" * 64
        self.derived = "sha256:" + "b" * 64
        runtime = {"image": self.base, "derived_image": self.derived}
        binding = {"purpose": "synthetic_test_only"}
        records = {
            "preparation.json": {"binding": binding, "runtime_id": "synthetic", "runtime": runtime},
            "prepared.json": {"container": {"Image": self.derived}},
            "image-input.json": {"base_image": self.base, "base_id": "sha256:" + "a" * 64,
                                 "context_sha256": "c" * 64},
            "stop-synthetic.json": {"runtime_id": "synthetic", "termination_confirmed": True},
        }
        records["image-build.json"] = {**records["image-input.json"], "derived_image": self.derived}
        for name, record in records.items():
            write_record(self.path / name, record)
        (self.path / "events.jsonl").write_text('{"kind":"synthetic_test_only"}\n')
        self.receipt = {
            "schema_version": 1, "evidence_kind": "infrastructure_probe_not_model_evaluation",
            "runtime": runtime, "binding": binding, "runtime_id": "synthetic",
            "execution_state": "completed", "termination_confirmed": True,
            "capture_complete": True, "stop_evidence": "stop-synthetic.json",
            "capture_sha256": file_sha256(self.path / "events.jsonl"),
            "artifact_sha256": {name: file_sha256(self.path / name)
                                for name in (*records, "events.jsonl")},
        }
        self.save_receipt()

    def save_receipt(self):
        write_record(self.path / "receipt.json", self.receipt)

    def test_complete_synthetic_receipt_cannot_award_benchmark_pass(self):
        result = verify_probe(self.path)
        self.assertEqual(result["integrity"], "verified")
        self.assertFalse(result["model_evaluation"])
        self.assertEqual(result["benchmark_status"], "evidence_incomplete")

    def test_partial_cancel_and_timeout_stay_partial(self):
        for state in ("canceled", "timed_out"):
            with self.subTest(state=state):
                self.receipt.update(execution_state=state, capture_complete=False)
                self.save_receipt()
                result = verify_probe(self.path)
                self.assertEqual(result["execution_state"], state)
                self.assertFalse(result["capture_complete"])
                self.assertEqual(result["benchmark_status"], "evidence_incomplete")

    def test_raw_receipt_tamper_is_rejected(self):
        path = self.path / "receipt.json"
        envelope = json.loads(path.read_text())
        envelope["record"]["execution_state"] = "canceled"
        path.write_text(json.dumps(envelope))
        with self.assertRaisesRegex(InvalidManifest, "record integrity mismatch"):
            verify_probe(self.path)

    def test_changed_capture_and_missing_capture_are_rejected(self):
        path = self.path / "events.jsonl"
        path.write_text("changed\n")
        with self.assertRaisesRegex(InvalidManifest, "bound probe artifact changed"):
            verify_probe(self.path)
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            verify_probe(self.path)

    def test_missing_image_evidence_binding_is_rejected(self):
        del self.receipt["artifact_sha256"]["image-build.json"]
        self.save_receipt()
        with self.assertRaisesRegex(InvalidManifest, "incomplete artifact bindings"):
            verify_probe(self.path)

    def test_inconsistent_image_identity_is_rejected_even_with_valid_checksums(self):
        path = self.path / "image-build.json"
        record = read_record(path)
        record["derived_image"] = "sha256:" + "d" * 64
        write_record(path, record)
        self.receipt["artifact_sha256"][path.name] = file_sha256(path)
        self.save_receipt()
        with self.assertRaisesRegex(InvalidManifest, "probe image provenance mismatch"):
            verify_probe(self.path)
