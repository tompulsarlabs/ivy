#!/usr/bin/env python3
"""Native command, pre-claim and provenance controls. No model calls."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("runner", Path(__file__).with_name("dispatch-runner.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class HarnessSettingsTests(unittest.TestCase):
    def claude(self, effort="medium"):
        return {"harness": "claude-code", "model": "claude-opus-5", "effort": effort}

    def codex(self, effort="high"):
        return {"harness": "codex", "model": "gpt-5.6-sol", "effort": effort}

    def test_config_to_claude_commands_preserves_distinct_lane_efforts(self):
        _, _, lanes = runner.load_config(Path(__file__).resolve().parent.parent / "config.yml")
        frontier = runner.harness_argv(lanes["frontier"]["anthropic"], "task", "review")
        workhorse = runner.harness_argv(lanes["workhorse"]["anthropic"], "task", "review")
        self.assertIn("--effort", frontier)
        self.assertEqual(frontier[frontier.index("--effort") + 1], "xhigh")
        self.assertEqual(workhorse[workhorse.index("--effort") + 1], "medium")
        self.assertNotEqual(frontier, workhorse)

    def test_codex_effort_is_a_single_native_config_override(self):
        argv = runner.harness_argv(self.codex(), "task", "review")
        self.assertEqual(argv[argv.index("-c") + 1], 'model_reasoning_effort="high"')
        self.assertEqual(argv[-1], "task")

    def test_unset_effort_remains_unset(self):
        entry = self.codex()
        del entry["effort"]
        self.assertNotIn("-c", runner.harness_argv(entry, "task", "review"))

    def test_unknown_model_harness_and_effort_are_rejected(self):
        entries = [self.claude("typo"), self.codex("high\nmalicious=true"),
                   {"harness": "other", "model": "gpt-5.6-sol"},
                   {"harness": "codex", "model": "latest"},
                   {"harness": "codex", "model": "claude-opus-5"}]
        for entry in entries:
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                runner.harness_argv(entry, "task", "review")

    def test_haiku_has_no_effort_and_rejects_explicit_effort(self):
        entry = {"harness": "claude-code", "model": "claude-haiku-4-5"}
        self.assertNotIn("--effort", runner.harness_argv(entry, "task", "review"))
        with self.assertRaises(ValueError):
            runner.harness_argv({**entry, "effort": "low"}, "task", "review")

    def test_permissions_are_not_broadened_by_effort(self):
        for entry in (self.claude(), self.codex()):
            review = runner.harness_argv(entry, "task", "review")
            build = runner.harness_argv(entry, "task", "build")
            self.assertNotIn("acceptEdits", review)
            self.assertNotIn("workspace-write", review)
            self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", build)
            self.assertNotIn("bypassPermissions", build)
            self.assertIn("acceptEdits" if entry["harness"] == "claude-code" else "workspace-write", build)

    def test_explicit_claude_effort_overrides_inherited_effort_only(self):
        parent = {"CLAUDE_CODE_EFFORT_LEVEL": "low", "PATH": "fixture", "UNRELATED": "keep"}
        child = runner.harness_environment(self.claude("xhigh"), parent)
        self.assertEqual(child["CLAUDE_CODE_EFFORT_LEVEL"], "xhigh")
        self.assertEqual(child["UNRELATED"], "keep")
        self.assertEqual(parent["CLAUDE_CODE_EFFORT_LEVEL"], "low")
        self.assertEqual(runner.harness_environment(self.codex(), parent), parent)

    def test_route_preview_does_not_execute_or_touch_runner_workspace(self):
        config = Path(__file__).resolve().parent.parent / "config.yml"
        with patch.object(runner.subprocess, "run") as run, patch.object(runner, "ensure_clone") as clone, \
             patch.object(runner, "publish_status") as publish, \
             patch.object(sys, "argv", ["runner", "--preview-routes", "--config", str(config)]), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(runner.main(), 0)
        run.assert_not_called()
        clone.assert_not_called()
        publish.assert_not_called()
        profiles = json.loads(output.getvalue())
        self.assertEqual(len(profiles), 5)
        self.assertTrue(all(p["status"] == "valid_configuration" for p in profiles))
        self.assertTrue(all(p["availability"] == "not_checked" for p in profiles))

    def test_invalid_preview_exits_nonzero_without_fallback(self):
        lanes = {"workhorse": {"openai": {"harness": "codex", "model": "unregistered"}}}
        with patch.object(runner, "load_config", return_value=("", [], lanes)), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(runner.preview_routes(Path("fixture")), 1)
        profile = json.loads(output.getvalue())[0]
        self.assertEqual(profile["status"], "invalid_configuration")
        self.assertNotIn("argv", profile)

    def test_failed_preview_never_publishes_a_runner_error(self):
        with patch.object(sys, "argv", ["runner", "--preview-routes", "--config", "/missing/fixture.yml"]), \
             patch.object(runner, "publish_status") as publish, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.guarded_main(), 1)
        publish.assert_not_called()

    def test_empty_and_duplicate_effort_cannot_silently_use_defaults(self):
        original = (Path(__file__).resolve().parent.parent / "config.yml").read_text()
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / "config.yml"
            for replacement in ("effort:", "effort: high, effort: medium"):
                config.write_text(original.replace("effort: xhigh", replacement))
                with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                    runner.load_config(config)

    def test_version_capture_is_bounded_and_only_accepts_version_output(self):
        for output, expected in [("2.1.277 (Claude Code)\n", "2.1.277"),
                                 ("codex-cli 0.155.1\n", "0.155.1"),
                                 ("token=secret /Users/person/config", "unknown")]:
            with self.subTest(output=output), patch.object(runner.subprocess, "run", return_value=Mock(returncode=0, stdout=output)) as run:
                self.assertEqual(runner.harness_version("fixture"), expected)
                self.assertEqual(run.call_args.kwargs["timeout"], 5)
                self.assertEqual(run.call_args.args[0], ["fixture", "--version"])

    def test_version_failure_or_timeout_is_unknown(self):
        for error in (OSError(), subprocess.TimeoutExpired("fixture", 5)):
            with patch.object(runner.subprocess, "run", side_effect=error):
                self.assertEqual(runner.harness_version("fixture"), "unknown")

    def test_provenance_hashes_inputs_but_never_claims_effective_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "config.yml").write_text("private: fixture\n")
            with patch.object(runner, "IVY", root), patch.object(runner, "run", return_value=Mock(stdout="a" * 40)), \
                 patch.object(runner, "harness_version", return_value="0.155.1"):
                first = runner.execution_metadata(self.codex(), "secret prompt", root, "fixture")
                second = runner.execution_metadata(self.codex(), "changed prompt", root, "fixture")
        fields = dict(line.split(": ", 1) for line in first)
        self.assertEqual(fields["requested_effort"], "high")
        self.assertEqual(fields["effective_effort"], "unknown")
        self.assertEqual(fields["effective_model"], "unknown")
        self.assertEqual(fields["context_capture"], "runner_prompt_only")
        self.assertNotEqual(first, second)
        self.assertNotIn("secret prompt", "\n".join(first))
        self.assertNotIn("private: fixture", "\n".join(first))
        self.assertFalse(any(line.startswith("verified:") for line in first))

    def test_invalid_route_is_skipped_before_claim_or_project_clone(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            queue = root / "dispatch" / "queue"
            queue.mkdir(parents=True)
            contract = queue / "fixture.md"
            contract.write_text("unchanged contract")
            fm = {"id": "fixture", "state": "open", "repo": "owner/repo", "type": "review", "lane": "workhorse", "pool": "openai", "expires": "2099-01-01T00:00:00+00:00"}
            lanes = {"workhorse": {"openai": {"harness": "codex", "model": "unregistered"}}}
            # Keep the test-owned handle alive and close it explicitly; production
            # main's historical lock handle is closed when its process exits.
            with (root / "test-lock").open("w") as lock, \
                 patch.object(runner, "WORKROOT", root), patch.object(runner, "IVY", root), \
                 patch.object(runner, "WORK", root / "work"), \
                 patch("builtins.open", return_value=lock), \
                 patch.object(runner, "ensure_clone") as clone, \
                 patch.object(runner, "synced_runner", return_value=None), \
                 patch.object(runner, "run", return_value=Mock(returncode=0)), \
                 patch.object(runner, "load_config", return_value=("", [], lanes)), \
                 patch.object(runner, "parse_frontmatter", return_value=(fm, "task")), \
                 patch.object(runner, "set_state") as claim, \
                 patch.object(runner, "publish_status") as status, \
                 patch.object(runner.subprocess, "Popen") as worker, \
                 patch.object(sys, "argv", ["runner", "--once"]), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.main(), 0)
            claim.assert_not_called()
            worker.assert_not_called()
            clone.assert_called_once_with(root, runner.IVY_REMOTE)
            self.assertEqual(status.call_args.args[1][0]["reason"], "invalid_harness_config")
            self.assertEqual(contract.read_text(), "unchanged contract")

    def test_fixed_worker_receives_effort_and_completion_retains_unknowns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for relative in ("dispatch/queue", "dispatch/reports", "work/repo"):
                (root / relative).mkdir(parents=True)
            (root / "config.yml").write_text("fixture: true\n")
            contract = root / "dispatch/queue/fixture.md"
            contract.write_text("---\nstate: open\n---\ntask\n")
            worker = root / "fixture-worker"
            worker.write_text(f"#!{sys.executable}\n" + '''import os, sys
if '--version' in sys.argv:
    print('2.1.277 (Claude Code)')
    sys.exit(0)
assert sys.argv[sys.argv.index('--effort') + 1] == 'xhigh'
assert os.environ['CLAUDE_CODE_EFFORT_LEVEL'] == 'xhigh'
print('BEGIN_REPORT\\nFixed fixture result\\nEND_REPORT')
''')
            worker.chmod(0o700)
            fm = {"id": "fixture", "state": "open", "repo": "owner/repo", "type": "review", "lane": "frontier", "pool": "anthropic", "expires": "2099-01-01T00:00:00+00:00", "wall_minutes": 1}
            lanes = {"frontier": {"anthropic": self.claude("xhigh")}}
            with (root / "test-lock").open("w") as lock, \
                 patch.object(runner, "WORKROOT", root), patch.object(runner, "IVY", root), \
                 patch.object(runner, "WORK", root / "work"), \
                 patch("builtins.open", return_value=lock), \
                 patch.object(runner, "ensure_clone"), \
                 patch.object(runner, "synced_runner", return_value=None), \
                 patch.object(runner, "run", return_value=Mock(returncode=0, stdout="a" * 40)), \
                 patch.object(runner, "load_config", return_value=("", [], lanes)), \
                 patch.object(runner, "parse_frontmatter", return_value=(fm, "task")), \
                 patch.object(runner, "resolve_harness", side_effect=lambda argv: [str(worker)] + argv[1:]), \
                 patch.object(runner, "bot_commit_push", return_value=True), \
                 patch.object(runner, "finalize") as finalize, \
                 patch.object(runner, "publish_status"), \
                 patch.dict(os.environ, {"CLAUDE_CODE_EFFORT_LEVEL": "low"}), \
                 patch.object(sys, "argv", ["runner", "--once"]), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.main(), 0)
            outcome = finalize.call_args.args[4]
            self.assertEqual(finalize.call_args.args[2:4], ("done", "done"))
            self.assertIn("requested_effort: xhigh", outcome)
            self.assertIn("effective_effort: unknown", outcome)
            self.assertIn("harness_version: 2.1.277", outcome)
            self.assertFalse(any(line.startswith("verified:") for line in outcome))
            self.assertIn("Fixed fixture result", (root / "dispatch/reports/fixture.md").read_text())


if __name__ == "__main__":
    unittest.main()
