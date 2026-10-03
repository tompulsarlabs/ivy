#!/usr/bin/env python3
"""Deterministic scanner controls. Uses temporary Git repositories, never GitHub."""
import contextlib
import fcntl
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("wip", Path(__file__).with_name("local-wip.py"))
wip = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wip)

IDENTITY = "fixture@example.invalid"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ivy-wip-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "Build"
        self.root.mkdir()
        # Keep developer signing/hooks/config and Git identity out of fixtures.
        self.environment = patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": IDENTITY,
            "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": IDENTITY,
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def repo(self, name="project", commit=True):
        repo = self.root / name
        repo.mkdir(parents=True)
        git(repo, "init", "--quiet", "-b", "main")
        git(repo, "config", "user.name", "Fixture")
        git(repo, "config", "user.email", IDENTITY)
        if commit:
            (repo / "file.txt").write_text("original\n")
            git(repo, "add", "file.txt")
            git(repo, "commit", "--quiet", "-m", "initial")
        return repo

    def remote(self):
        source = self.repo("ivy")
        origin = self.base / "origin.git"
        git(self.base, "clone", "--quiet", "--bare", str(source), str(origin))
        git(source, "remote", "add", "origin", str(origin))
        git(source, "fetch", "--quiet", "origin")
        return source, origin

    def payload(self, date="2026-09-23T12:00:00Z", repos=None):
        return {"generated_at": date, "repos": repos or []}

    def test_external_linked_worktree_and_dirty_work_are_discovered(self):
        repo = self.repo()
        linked = self.base / "external worktree"
        git(repo, "worktree", "add", "--quiet", "-b", "feature", str(linked))
        (linked / "new.txt").write_text("work\n")
        self.assertEqual(wip.discover_repos([self.root]), sorted([repo, linked]))
        self.assertEqual(wip.scan_repo(linked, [IDENTITY])["dirty_files"], 1)

    def test_nested_repositories_and_git_files_are_discovered_once(self):
        repo = self.repo("group/project")
        linked = self.root / "linked"
        git(repo, "worktree", "add", "--quiet", "-b", "feature", str(linked))
        self.assertEqual(wip.discover_repos([self.root, self.root / "group", repo]), sorted([repo, linked]))

    def test_deleted_registered_worktree_is_skipped_without_pruning(self):
        repo = self.repo()
        linked = self.base / "gone"
        git(repo, "worktree", "add", "--quiet", "-b", "feature", str(linked))
        shutil.rmtree(linked)
        self.assertEqual(wip.discover_repos([self.root]), [repo])
        self.assertIn(str(linked), git(repo, "worktree", "list", "--porcelain"))

    def test_missing_root_refuses_fresh_empty_snapshot(self):
        with self.assertRaises(RuntimeError):
            wip.discover_repos([self.base / "missing"])

    def test_unborn_repository_is_not_a_git_error(self):
        row = wip.scan_repo(self.repo(commit=False), [IDENTITY])
        self.assertEqual((row["unpushed_commits"], row["last_commit"]), (0, ""))

    def test_orphan_branch_does_not_count_other_branches(self):
        repo = self.repo()
        git(repo, "checkout", "--quiet", "--orphan", "empty")
        row = wip.scan_repo(repo, [IDENTITY])
        self.assertEqual(row["checkout_unpushed_commits"], 0)
        self.assertEqual(row["unpushed_commits"], 1)

    def test_unchecked_out_local_branch_remains_visible(self):
        repo, _ = self.remote()
        git(repo, "checkout", "--quiet", "-b", "pending")
        (repo / "file.txt").write_text("pending\n")
        git(repo, "commit", "-qam", "unpublished work")
        git(repo, "checkout", "--quiet", "main")
        row = wip.scan_repo(repo, [IDENTITY])
        self.assertEqual(row["unpushed_commits"], 1)
        self.assertEqual(row["checkout_unpushed_commits"], 0)

    def test_counts_current_worktree_head_including_detached_commits(self):
        repo, _ = self.remote()
        linked = self.base / "linked"
        git(repo, "worktree", "add", "--quiet", "--detach", str(linked))
        (linked / "file.txt").write_text("changed\n")
        git(linked, "commit", "-qam", "detached work")
        self.assertEqual(wip.scan_repo(repo, [IDENTITY])["unpushed_commits"], 0)
        self.assertEqual(wip.scan_repo(linked, [IDENTITY])["unpushed_commits"], 1)

    def test_git_failure_is_not_zero_dirty_files(self):
        repo = self.repo()
        real = wip.git
        with patch.object(wip, "git", side_effect=lambda path, *args, **kwargs: None if args[0] == "status" else real(path, *args, **kwargs)):
            with self.assertRaises(RuntimeError):
                wip.scan_repo(repo, [IDENTITY])

    def test_github_remote_is_sanitized_and_identity_is_boolean(self):
        repo = self.repo()
        git(repo, "remote", "add", "upstream", "https://github.com/owner/repo.git")
        row = wip.scan_repo(repo, [IDENTITY])
        self.assertEqual(row["remote"], "owner/repo")
        self.assertTrue(row["author_email_ok"])
        git(repo, "remote", "set-url", "upstream", "https://secret@github.com/owner/repo.git")
        row = wip.scan_repo(repo, [IDENTITY])
        self.assertEqual(row["remote"], "other")
        self.assertNotIn("secret", json.dumps(row))
        self.assertNotIn(str(self.base), json.dumps(row))
        self.assertNotIn(IDENTITY, json.dumps(row))

    def test_inherited_git_repository_cannot_redirect_a_scan(self):
        target = self.repo("target")
        other = self.repo("other")
        git(other, "checkout", "-qb", "wrong-checkout")
        with patch.dict(os.environ, {"GIT_DIR": str(other / ".git"),
                                     "GIT_WORK_TREE": str(other),
                                     "GIT_INDEX_FILE": str(other / ".git/index")}):
            row = wip.scan_repo(target, [IDENTITY])
        self.assertEqual(row["branch"], "main")
        self.assertEqual(row["dirty_files"], 0)

    def test_publication_ignores_inherited_checkout_and_commit_identity(self):
        source, remote = self.remote()
        (source / "file.txt").write_text("staged human work\n")
        git(source, "add", "file.txt")
        before = (git(source, "rev-parse", "HEAD"), (source / ".git/index").read_bytes())
        with patch.dict(os.environ, {"GIT_DIR": str(source / ".git"),
                                     "GIT_WORK_TREE": str(source),
                                     "GIT_INDEX_FILE": str(source / ".git/index"),
                                     "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
                                     "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z"}):
            self.assertTrue(wip.publish_snapshot(self.payload(), str(remote)))
        self.assertEqual(before, (git(source, "rev-parse", "HEAD"), (source / ".git/index").read_bytes()))
        self.assertEqual(git(remote, "log", "-1", "--format=%an|%ae|%cn|%ce"),
                         "ivy-bot|bot@ivy.invalid|ivy-bot|bot@ivy.invalid")
        self.assertNotIn("2000-01-01", git(remote, "log", "-1", "--format=%aI|%cI"))

    def test_unchanged_snapshot_refreshes_at_six_hours(self):
        previous = self.payload("2026-09-23T06:00:00Z")
        self.assertTrue(wip.should_publish(previous, self.payload()))
        self.assertFalse(wip.should_publish(previous, self.payload("2026-09-23T11:59:59Z")))

    def test_changed_snapshot_publishes_before_heartbeat(self):
        self.assertTrue(wip.should_publish(self.payload(), self.payload(repos=[{"name": "new"}])))

    def test_missing_or_malformed_snapshot_refreshes(self):
        for previous in (None, [], {}, {"generated_at": "bad"}, {"generated_at": "2026-09-23T12:00:00"}):
            with self.subTest(previous=previous):
                self.assertTrue(wip.should_publish(previous, self.payload()))

    def test_newer_remote_snapshot_cannot_be_overwritten(self):
        with self.assertRaises(RuntimeError):
            wip.should_publish(self.payload("2026-09-23T13:00:00Z"), self.payload())

    def test_invalid_new_timestamp_is_refused(self):
        with self.assertRaises(RuntimeError):
            wip.should_publish(None, self.payload("bad"))

    def test_publication_leaves_staged_dirty_and_unpushed_work_untouched(self):
        source, remote = self.remote()
        (source / "local-only.txt").write_text("private work\n")
        git(source, "add", "local-only.txt")
        git(source, "commit", "--quiet", "-m", "unpublished human change")
        (source / "file.txt").write_text("staged\n")
        git(source, "add", "file.txt")
        (source / "file.txt").write_text("unstaged\n")
        before = (git(source, "rev-parse", "HEAD"), git(source, "diff"), git(source, "diff", "--cached"))
        self.assertTrue(wip.publish_snapshot(self.payload(), str(remote)))
        self.assertEqual(before, (git(source, "rev-parse", "HEAD"), git(source, "diff"), git(source, "diff", "--cached")))
        self.assertEqual(git(remote, "diff-tree", "--no-commit-id", "--name-only", "-r", "main"), "local-wip.json")
        self.assertNotIn("local-only.txt", git(remote, "ls-tree", "--name-only", "main"))
        self.assertEqual(git(remote, "log", "-1", "--format=%ae"), "bot@ivy.invalid")

    def test_repeated_publication_inside_heartbeat_creates_no_commit(self):
        _, remote = self.remote()
        self.assertTrue(wip.publish_snapshot(self.payload(), str(remote)))
        head = git(remote, "rev-parse", "main")
        self.assertFalse(wip.publish_snapshot(self.payload(), str(remote)))
        self.assertEqual(head, git(remote, "rev-parse", "main"))

    def test_branch_race_preserves_remote_change_and_retries_snapshot(self):
        source, remote = self.remote()
        real = wip.git
        races = []

        def racing(path, *args, **kwargs):
            if args[0] == "push" and not races:
                races.append(True)
                (source / "cloud.txt").write_text("routine update\n")
                git(source, "add", "cloud.txt")
                git(source, "commit", "-qm", "cloud update")
                git(source, "push", "--quiet", "origin", "main")
            return real(path, *args, **kwargs)

        with patch.object(wip, "git", side_effect=racing):
            self.assertTrue(wip.publish_snapshot(self.payload(), str(remote)))
        self.assertEqual(git(remote, "show", "main:cloud.txt"), "routine update")
        self.assertIn("local-wip.json", git(remote, "ls-tree", "--name-only", "main"))

    def test_failed_push_is_reported_and_future_run_can_publish(self):
        _, remote = self.remote()
        real = wip.git
        with patch.object(wip, "git", side_effect=lambda path, *args, **kwargs: None if args[0] == "push" else real(path, *args, **kwargs)):
            with self.assertRaises(RuntimeError):
                wip.publish_snapshot(self.payload(), str(remote))
        self.assertTrue(wip.publish_snapshot(self.payload(), str(remote)))

    def test_preview_has_no_publication_or_lock(self):
        with patch.object(wip, "collect_snapshot", return_value=self.payload()), \
             patch.object(wip, "publish_snapshot") as publish, \
             patch.object(wip, "LOCK", self.base / "no-lock"), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(wip.main(["--dry-run"]), 0)
        publish.assert_not_called()
        self.assertFalse((self.base / "no-lock").exists())
        self.assertEqual(json.loads(output.getvalue()), self.payload())

    def test_concurrent_scan_cannot_publish(self):
        lock_path = self.base / "lock"
        with lock_path.open("a") as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with patch.object(wip, "LOCK", lock_path), patch.object(wip, "collect_snapshot") as collect, \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(wip.main([]), 0)
            collect.assert_not_called()

    def test_old_lock_file_does_not_block_a_new_scan(self):
        lock_path = self.base / "lock"
        lock_path.write_text("999999")
        with patch.object(wip, "LOCK", lock_path), patch.object(wip, "collect_snapshot", return_value=self.payload()), \
             patch.object(wip, "required_git", return_value="fixture"), \
             patch.object(wip, "publish_snapshot", return_value=True) as publish, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(wip.main([]), 0)
        publish.assert_called_once()

    def test_remote_symlink_cannot_write_outside_clone(self):
        source, remote = self.remote()
        outside = self.base / "outside.json"
        outside.write_text("preserve")
        (source / "local-wip.json").symlink_to(outside)
        git(source, "add", "local-wip.json")
        git(source, "commit", "-qm", "symlink fixture")
        git(source, "push", "--quiet", "origin", "main")
        with self.assertRaises(RuntimeError):
            wip.publish_snapshot(self.payload(), str(remote))
        self.assertEqual(outside.read_text(), "preserve")


class PullRequestHeadTests(unittest.TestCase):
    """Pull-request heads come from refs/pull/N/head on local bare fixtures."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ivy-wip-heads-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.environment = patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": IDENTITY,
            "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": IDENTITY,
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        remotes = self.base / "remotes"
        self.template = patch.object(wip, "PR_REMOTE", f"file://{remotes}/{{repo}}.git")
        self.template.start()
        self.addCleanup(self.template.stop)

    def hosted(self, slug, pulls=()):
        """A bare repo standing in for github.com/<slug>, with PR head refs."""
        bare = self.base / "remotes" / f"{slug}.git"
        bare.parent.mkdir(parents=True, exist_ok=True)
        git(self.base, "init", "--quiet", "--bare", str(bare))
        work = self.base / "work" / slug
        work.mkdir(parents=True)
        git(work, "init", "--quiet", "-b", "main")
        heads = {}
        for number in pulls:
            (work / "file.txt").write_text(f"pull {number}\n")
            git(work, "add", "file.txt")
            git(work, "commit", "--quiet", "-m", f"pull {number}")
            git(work, "push", "--quiet", str(bare), f"HEAD:refs/pull/{number}/head")
            heads[str(number)] = git(work, "rev-parse", "HEAD")
        return heads

    def test_pull_request_heads_are_read_from_pull_refs(self):
        expected = self.hosted("owner/app", pulls=(1, 7))
        self.assertEqual(wip.pull_request_heads("owner/app"), expected)

    def test_repo_without_pull_requests_is_empty_not_absent(self):
        self.hosted("owner/quiet")
        self.assertEqual(wip.collect_pr_heads(["owner/quiet"]), {"owner/quiet": {}})

    def test_unreachable_repo_is_absent_not_empty(self):
        self.hosted("owner/app", pulls=(2,))
        heads = wip.collect_pr_heads(["owner/app", "owner/missing"])
        self.assertIn("owner/app", heads)
        self.assertNotIn("owner/missing", heads)

    def test_slow_repo_past_the_pass_budget_is_absent(self):
        def answer(repo):
            if repo == "owner/slow":
                import time
                time.sleep(1)
            return {"1": "a" * 40}
        with patch.object(wip, "pull_request_heads", side_effect=answer), \
             patch.object(wip, "PR_PASS_BUDGET", 0.3):
            heads = wip.collect_pr_heads(["owner/fast", "owner/slow"])
        self.assertEqual(heads, {"owner/fast": {"1": "a" * 40}})

    def test_only_well_formed_pull_head_lines_are_kept(self):
        output = "\n".join([
            "a" * 40 + "\trefs/pull/3/head",
            "b" * 40 + "\trefs/pull/0/head",
            "not-a-sha\trefs/pull/4/head",
            "c" * 40 + "\trefs/pull/5/merge",
            "d" * 40 + "\trefs/pull/6/head; rm -rf /",
        ])
        done = subprocess.CompletedProcess([], 0, stdout=output, stderr="")
        with patch.object(wip.subprocess, "run", return_value=done):
            self.assertEqual(wip.pull_request_heads("owner/app"), {"3": "a" * 40})

    def test_git_is_never_allowed_to_prompt(self):
        done = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with patch.object(wip.subprocess, "run", return_value=done) as run:
            wip.pull_request_heads("owner/app")
        env = run.call_args.kwargs["env"]
        self.assertEqual((env["GIT_TERMINAL_PROMPT"], env["GCM_INTERACTIVE"]), ("0", "never"))
        self.assertIs(run.call_args.kwargs["stdin"], subprocess.DEVNULL)

    def config(self, watchlist=True):
        root = self.base / "Build"
        root.mkdir(exist_ok=True)
        text = (f"connected_emails:\n  - {IDENTITY}\n\n"
                f"local_wip:\n  roots:\n    - {root}\n")
        if watchlist:
            text += ("\nwatchlist:\n  source: auto\n  parked:\n    - owner/parked\n"
                     "  repos:\n    - owner/app\n    - owner/quiet\n    - not a slug\n\nlanes:\n")
        (self.base / "config.yml").write_text(text)
        return self.base / "config.yml"

    def test_watchlist_repos_are_read_without_parked_or_invalid_entries(self):
        self.assertEqual(wip.read_watchlist(self.config()), ["owner/app", "owner/quiet"])
        self.assertIsNone(wip.read_watchlist(self.config(watchlist=False)))

    def test_snapshot_carries_heads_only_when_asked(self):
        self.config()
        expected = self.hosted("owner/app", pulls=(4,))
        self.hosted("owner/quiet")
        with patch.object(wip, "IVY", self.base):
            self.assertNotIn("pr_heads", wip.collect_snapshot())
            heads = wip.collect_snapshot(with_pr_heads=True)["pr_heads"]
        self.assertEqual(heads, {"owner/app": expected, "owner/quiet": {}})

    def test_missing_watchlist_omits_heads_instead_of_publishing_none(self):
        self.config(watchlist=False)
        with patch.object(wip, "IVY", self.base), contextlib.redirect_stderr(io.StringIO()):
            self.assertNotIn("pr_heads", wip.collect_snapshot(with_pr_heads=True))


class ScanErrorTests(unittest.TestCase):
    """A failed scan reaches the cloud as a code on the last good snapshot."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ivy-wip-error-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.environment = patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": IDENTITY,
            "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": IDENTITY,
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        source = self.base / "ivy"
        source.mkdir()
        git(source, "init", "--quiet", "-b", "main")
        (source / "README.md").write_text("ivy\n")
        git(source, "add", "README.md")
        git(source, "commit", "--quiet", "-m", "initial")
        self.remote = self.base / "origin.git"
        git(self.base, "clone", "--quiet", "--bare", str(source), str(self.remote))

    def good(self):
        return {"generated_at": "2026-10-01T06:45:00Z", "repos": [{"name": "app"}],
                "pr_heads": {"owner/app": {"1": "a" * 40}}}

    def published(self):
        return json.loads(git(self.remote, "show", "main:local-wip.json"))

    def test_failed_scan_keeps_the_last_good_snapshot_and_timestamp(self):
        self.assertTrue(wip.publish_snapshot(self.good(), str(self.remote)))
        self.assertTrue(wip.publish_scan_error("root_unavailable", str(self.remote), now="2026-10-01T15:45:00Z"))
        self.assertEqual(self.published(), {**self.good(), "scanner_error": "root_unavailable",
                                            "scanner_error_at": "2026-10-01T15:45:00Z"})
        self.assertEqual(git(self.remote, "log", "-1", "--format=%ae|%s"),
                         "bot@ivy.invalid|wip: local scan failed — root_unavailable")

    def test_failed_scan_without_a_previous_snapshot_publishes_nothing(self):
        head = git(self.remote, "rev-parse", "main")
        self.assertFalse(wip.publish_scan_error("config_missing", str(self.remote)))
        self.assertEqual(head, git(self.remote, "rev-parse", "main"))

    def test_same_error_is_republished_only_after_the_heartbeat(self):
        previous = {**self.good(), "scanner_error": "git_failed", "scanner_error_at": "2026-10-01T09:00:00Z"}
        self.assertIsNone(wip.with_scanner_error(previous, "git_failed", "2026-10-01T14:59:59Z"))
        self.assertIsNotNone(wip.with_scanner_error(previous, "git_failed", "2026-10-01T15:00:00Z"))
        self.assertIsNotNone(wip.with_scanner_error(previous, "root_unavailable", "2026-10-01T10:00:00Z"))

    def test_successful_scan_clears_a_published_error(self):
        previous = {**self.good(), "scanner_error": "git_failed", "scanner_error_at": "2026-10-01T09:00:00Z"}
        self.assertTrue(wip.should_publish(previous, {**self.good(), "generated_at": "2026-10-01T09:30:00Z"}))

    def test_heads_only_change_publishes_and_unchanged_heads_do_not(self):
        later = {**self.good(), "generated_at": "2026-10-01T07:00:00Z"}
        moved = {**later, "pr_heads": {"owner/app": {"1": "b" * 40}}}
        self.assertFalse(wip.should_publish(self.good(), later))
        self.assertTrue(wip.should_publish(self.good(), moved))

    def test_collection_failure_publishes_its_code_and_still_fails(self):
        lock = self.base / "lock"
        failure = wip.ScanError("root_unavailable", "configured scan root unavailable; snapshot not published")
        with patch.object(wip, "LOCK", lock), patch.object(wip, "required_git", return_value="fixture"), \
             patch.object(wip, "collect_snapshot", side_effect=failure), \
             patch.object(wip, "publish_scan_error") as report:
            with self.assertRaises(wip.ScanError):
                wip.main([])
        report.assert_called_once_with("root_unavailable", "fixture")

    def test_dry_run_reads_no_pull_requests_unless_asked(self):
        with patch.object(wip, "collect_snapshot", return_value=self.good()) as collect, \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            wip.main(["--dry-run"])
            wip.main(["--dry-run", "--pr-heads"])
        self.assertEqual([c.kwargs for c in collect.call_args_list],
                         [{"with_pr_heads": False}, {"with_pr_heads": True}])


if __name__ == "__main__":
    unittest.main()
