#!/usr/bin/env python3
"""Unit checks for the pure parts of dispatch-runner.py — the parts that cost
contracts when wrong and that only ever run on the Mac.

Red on 2026-09-01: the attribution gate compared `git var GIT_AUTHOR_IDENT`
against `commit_email` alone, so a clone correctly configured with the
second connected address (`tom@pulsarlabsai.com`) failed three build
contracts with `exit: attribution`. This file locks the fix down.

Run: python3 scripts/dispatch-runner-test.py   (exit 0 = green)
"""
import importlib.util, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("runner", HERE / "dispatch-runner.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

CONFIG = """\
commit_email: 249609836+tompulsarlabs@users.noreply.github.com
commit_name: tompulsarlabs
connected_emails:
  - 249609836+tompulsarlabs@users.noreply.github.com
  - tom@pulsarlabsai.com
lanes:
  frontier:
    anthropic: { harness: claude-code, model: claude-opus-5, effort: xhigh }
    openai:    { harness: codex, model: gpt-5.6-sol }
  workhorse:
    anthropic: { harness: claude-code, model: claude-opus-5, effort: medium }
pools:
  anthropic: { auth: mac-local }
"""

CONTRACT = """\
---
id: 2026-09-02-example-01
type: build
state: open
repo: tompulsarlabs/example
lane: workhorse
created: 2026-09-02T09:00:00+02:00
created_by: tom
expires: 2026-09-04T09:00:00+02:00
budget: { wall_minutes: 25 }
blocked_by: [2026-09-02-example-00, 2026-09-01-other-03]
---

## Task
x
"""

failures = []
def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        failures.append(name)

with tempfile.TemporaryDirectory() as tmp:
    runner.IVY = Path(tmp)
    (runner.IVY / "config.yml").write_text(CONFIG)
    commit_email, connected, lanes = runner.load_config()
    check("commit_email parsed", commit_email.endswith("@users.noreply.github.com"))
    check("connected_emails parsed as a list of two", connected == [
        "249609836+tompulsarlabs@users.noreply.github.com", "tom@pulsarlabsai.com"])
    check("lanes parsed", lanes["frontier"]["openai"]["model"] == "gpt-5.6-sol")

    # Red until 2026-09-23: harness_argv read `effort` and dropped it, so the
    # frontier and workhorse lanes ran the identical Claude command.
    fr = runner.harness_argv(lanes["frontier"]["anthropic"], "p", "review")
    wh = runner.harness_argv(lanes["workhorse"]["anthropic"], "p", "review")
    check("frontier and workhorse commands differ", fr != wh)
    flag = lambda argv, f: argv[argv.index(f) + 1] if f in argv else None
    check("claude gets the lane's effort", flag(fr, "--effort") == "xhigh" and flag(wh, "--effort") == "medium")
    check("no effort configured -> no --effort flag",
          "--effort" not in runner.harness_argv({"harness": "claude-code", "model": "m"}, "p", "review"))
    cx = runner.harness_argv({"harness": "codex", "model": "m", "effort": "high"}, "p", "build")
    check("codex gets effort as a config override", flag(cx, "-c") == 'model_reasoning_effort="high"')
    check("codex prompt stays last", cx[-1] == "p")
    check("codex without effort has no override",
          "-c" not in runner.harness_argv(lanes["frontier"]["openai"], "p", "review"))
    check("a configured lane runs", runner.lane_problem(lanes["workhorse"]["anthropic"]) is None)
    check("a missing lane is unresolved", runner.lane_problem(None) == "lane_unresolved")
    check("a VERIFY model is unresolved", runner.lane_problem({"harness": "codex", "model": "VERIFY"}) == "lane_unresolved")
    check("an effort claude refuses is caught before the claim",
          runner.lane_problem({"harness": "claude-code", "model": "m", "effort": "xHigh"}) == "lane_invalid")

    # The 2026-09-01 failure: a clone using the second connected address.
    ident_ok = "tompulsarlabs <tom@pulsarlabsai.com> 1756738878 +0200"
    ident_bad = "Tom Green <tom@C2-LAP32-TomGreen.local> 1756738878 +0200"
    check("gate passes the second connected address", runner.author_connected(ident_ok, connected))
    check("gate refuses an invented hostname identity", not runner.author_connected(ident_bad, connected))

    fm, body = runner.parse_frontmatter(CONTRACT)
    check("blocked_by parsed as a list", fm.get("blocked_by") == ["2026-09-02-example-00", "2026-09-01-other-03"])
    check("wall_minutes parsed", fm["wall_minutes"] == 25)
    check("no blocked_by -> empty list", runner.parse_frontmatter(
        CONTRACT.replace("blocked_by: [2026-09-02-example-00, 2026-09-01-other-03]\n", ""))[0].get("blocked_by") == [])
    check("blocked while a blocker is not done",
          runner.open_blockers(fm, {"2026-09-02-example-00"}) == ["2026-09-01-other-03"])
    check("unblocked once every blocker is done",
          runner.open_blockers(fm, {"2026-09-02-example-00", "2026-09-01-other-03"}) == [])

    # Red on 2026-09-02: the launchd entry point (~/Build/ivy) and the synced
    # checkout (~/.ivy-dispatch/ivy) are different working copies, so a pushed
    # gate fix sat unexecuted while the old gate refused four contracts.
    a, b = Path(tmp) / "a.py", Path(tmp) / "b.py"
    a.write_text("old\n")
    b.write_text("new\n")
    check("differing synced copy is exec'd", runner.synced_runner(a, b) == b)
    b.write_text("old\n")
    check("identical synced copy is not exec'd", runner.synced_runner(a, b) is None)
    check("same path is never exec'd (no loop)", runner.synced_runner(a, a) is None)
    check("missing synced copy is tolerated", runner.synced_runner(a, Path(tmp) / "nope.py") is None)

    # Red on 2026-09-02: `claude` is in ~/.local/bin, absent from launchd's PATH.
    # Popen raised FileNotFoundError after the claim was pushed, stranding two
    # contracts in `claimed`. Resolve before claiming; exec an absolute path.
    argv = ["claude", "-p", "prompt", "--model", "claude-opus-5"]
    check("harness resolved to an absolute path",
          runner.resolve_harness(argv, which=lambda b: "/Users/x/.local/bin/" + b)
          == ["/Users/x/.local/bin/claude", "-p", "prompt", "--model", "claude-opus-5"])
    check("missing harness resolves to None (contract stays open)",
          runner.resolve_harness(argv, which=lambda b: None) is None)
    check("resolution keeps every argument after argv[0]",
          len(runner.resolve_harness(argv, which=lambda b: "/bin/" + b)) == len(argv))
    check("empty argv is tolerated", runner.resolve_harness([], which=lambda b: "/bin/x") is None)

    # Red on 2026-09-03: three contracts open all day, no claim, and nothing in
    # the repo said why. The heartbeat commits only when a reader-facing part
    # changes, or once per heartbeat window, and carries no path or hostname.
    from datetime import datetime, timedelta
    t0 = datetime.fromisoformat("2026-09-03T11:00:00+02:00")
    h = {"claude": True, "codex": True}
    s1 = runner.build_status(None, "idle", [], True, t0, harness=h, sha="abc1234")
    check("first status starts its own since", s1["since"] == s1["last_tick"])
    check("status carries no path or hostname", not any(
        "/" in str(v) or ".local" in str(v) for v in [s1["harness"], s1["result"], s1["skipped"]]))
    s2 = runner.build_status(s1, "idle", [], True, t0 + timedelta(minutes=30), harness=h, sha="def5678")
    check("unchanged status keeps since", s2["since"] == s1["since"])
    check("sha alone does not count as change", not runner.status_changed(s1, s2))
    check("no commit within the heartbeat", not runner.status_commit_needed(s1, s2, t0 + timedelta(minutes=30)))
    check("commit once the heartbeat is due", runner.status_commit_needed(s1, s2, t0 + timedelta(hours=6)))
    s3 = runner.build_status(s1, "idle", [{"id": "x-01", "reason": "harness_missing"}], True,
                             t0 + timedelta(minutes=30), harness={"claude": False, "codex": True}, sha="abc1234")
    check("a missing harness is a change", runner.status_changed(s1, s3))
    check("a change resets since", s3["since"] == s3["last_tick"])
    check("a change commits at once", runner.status_commit_needed(s1, s3, t0 + timedelta(minutes=30)))
    check("no previous status commits", runner.status_commit_needed(None, s1, t0))

    # Red on 2026-09-03 10:53 -> 09-04: copy-02's worker was killed at budget on
    # its own branch with edits in the tree; `git checkout main` then refused,
    # the exception escaped, and every tick since died before claiming or
    # writing a heartbeat. ensure_clone must recover any state a worker leaves.
    import subprocess
    def git(*args, cwd):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                              cwd=cwd, text=True, capture_output=True, check=True).stdout.strip()
    remote = Path(tmp) / "remote.git"; seed = Path(tmp) / "seed"; clone = Path(tmp) / "work" / "repo"
    git("init", "--quiet", "--bare", "-b", "main", str(remote), cwd=tmp)
    git("clone", "--quiet", str(remote), str(seed), cwd=tmp)
    (seed / "a.txt").write_text("v1\n"); (seed / ".gitignore").write_text("node_modules/\n")
    git("add", ".", cwd=seed); git("commit", "-q", "-m", "v1", cwd=seed); git("push", "-q", "origin", "HEAD:main", cwd=seed)
    git("symbolic-ref", "HEAD", "refs/heads/main", cwd=remote)
    head = runner.ensure_clone(clone, str(remote))
    check("fresh clone lands on the default branch", head == "main" and git("rev-parse", "--abbrev-ref", "HEAD", cwd=clone) == "main")
    # what a killed worker leaves behind
    git("checkout", "-q", "-b", "dispatch/x-01", cwd=clone)
    (clone / "a.txt").write_text("edited by worker\n")
    (clone / "untracked.json").write_text("{}\n")
    (clone / "node_modules").mkdir(); (clone / "node_modules" / "keep").write_text("x")
    git("commit", "-q", "-am", "worker wip", cwd=clone); (clone / "a.txt").write_text("dirty again\n")
    head = runner.ensure_clone(clone, str(remote))
    check("dirty clone on a worker branch recovers to main", git("rev-parse", "--abbrev-ref", "HEAD", cwd=clone) == "main")
    check("tree is pinned to origin", (clone / "a.txt").read_text() == "v1\n" and git("status", "--porcelain", cwd=clone) == "")
    check("untracked worker files are gone", not (clone / "untracked.json").exists())
    check("ignored install survives", (clone / "node_modules" / "keep").exists())

    # An unexpected exception must surface as a heartbeat, never a silent death.
    published = {}
    real_main, real_publish = runner.main, runner.publish_status
    runner.main = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    runner.publish_status = lambda result, skipped, lint_ok, now: published.update(result=result)
    try:
        rc = runner.guarded_main()
    finally:
        runner.main, runner.publish_status = real_main, real_publish
    check("guarded_main returns 1 on an exception", rc == 1)
    check("and publishes runner_error with the type only", published.get("result") == "runner_error: RuntimeError")

    review = runner.build_prompt("c1", "o/r", "review", "## Task\nx\n")
    build = runner.build_prompt("c2", "o/r", "build", "## Task\nx\n")
    check("review prompt names the code-review skill", "code-review" in review)
    check("build prompt names tdd and code-review", "tdd" in build and "code-review" in build)
    check("review prompt stays read-only", "read-only" in review)
    check("review prompt asks for coverage with severity and confidence",
          "every issue" in review and "severity" in review and "confidence" in review)
    check("build prompt names its branch and a draft PR", "dispatch/c2" in build and "draft pull request" in build)
    check("build prompt keeps the configured git identity", "leave user.name and user.email" in build)
    check("both prompts say the run is unattended", all("unattended" in p for p in (review, build)))
    check("both prompts carry the report markers", all(runner.MARK_BEGIN in p and runner.MARK_END in p
                                                       for p in (review, build)))

print()
print("dispatch-runner-test: " + ("ok" if not failures else f"{len(failures)} failing"))
sys.exit(1 if failures else 0)
