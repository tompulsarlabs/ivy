#!/usr/bin/env python3
"""Ivy dispatch runner — executes queued contracts on the Mac (D2).

Runs from launchd every 30 min inside the 09:15-21:00 window (see
config.yml dispatch.runner_window). Operates on its OWN clone of ivy under
~/.ivy-dispatch/ so the human checkout is never mutated. One contract per
tick, oldest first. State changes are bot-authored commits; the repo is the
message bus and the cloud failsafe does verification — this script never
stamps `verified:`.

Flags: --once (ignore the window; single pass)  --dry-run (plan only,
print the exact harness argv, change nothing).

Harness notes: `claude -p` flags are stable; `codex exec` flags are
confirmed during the D2 smoke test — if the argv printed by --dry-run is
wrong for your codex version, fix HARNESS_ARGV below.

A lane's `effort` reaches the harness (`--effort` for Claude Code,
`model_reasoning_effort` for Codex); before 2026-09-23 it was read and
dropped, so frontier and workhorse ran identical commands. An effort Claude
Code does not accept skips the contract as `lane_invalid` before it is
claimed.

The attribution gate tests membership in config.yml `connected_emails`
(2026-09-01: equality against `commit_email` alone failed three build
contracts on a clone correctly configured with the second connected
address). A contract with `blocked_by: [id, ...]` is skipped until every id
sits in dispatch/done/. Pure parts are covered by dispatch-runner-test.py.

The runner execs the copy inside IVY once the sync has run: the launchd entry
point is a dev checkout that only moves when a human pulls, so without this a
pushed runner change lands in IVY while the old code keeps executing.
"""
import fcntl, json, os, re, shlex, shutil, signal, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

WORKROOT = Path.home() / ".ivy-dispatch"
IVY = WORKROOT / "ivy"
WORK = WORKROOT / "work"
IVY_REMOTE = "https://github.com/tompulsarlabs/ivy.git"
BOT = ["-c", "user.name=ivy-bot", "-c", "user.email=bot@ivy.invalid"]
WINDOW = ((9, 15), (21, 0))
STATUS_REL = "dispatch/runner-status.json"
STATUS_HEARTBEAT_HOURS = 6
STATUS_KEYS = ("harness", "lint_ok", "result", "skipped")  # what a reader acts on
MARK_BEGIN, MARK_END = "BEGIN_REPORT", "END_REPORT"
CLAUDE_EFFORTS = ("low", "medium", "high", "xhigh", "max")   # claude --effort choices

def log(msg):
    print(f"[{datetime.now().astimezone().isoformat(timespec='seconds')}] {msg}", flush=True)

def run(args, cwd=None, check=True, capture=True):
    r = subprocess.run(args, cwd=cwd, text=True,
                       capture_output=capture)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, args))} -> {r.returncode}: {(r.stderr or '')[:400]}")
    return r

def in_window(now):
    t = (now.hour, now.minute)
    return WINDOW[0] <= t <= WINDOW[1]

def ensure_clone(path, remote):
    if not (path / ".git").exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--quiet", remote, str(path)])
    run(["git", "fetch", "--quiet", "origin"], cwd=path)
    head = run(["git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], cwd=path,
               check=False).stdout.strip().rsplit("/", 1)[-1] or "main"
    # A worker killed at its budget leaves the clone on its branch with edits
    # in the tree. A plain `checkout` then refuses to switch, the exception
    # escapes, and every later tick dies at the same line before it can claim
    # or even write a heartbeat (2026-09-03 10:53 -> 09-04, after copy-02).
    # These clones are disposable by contract ("a fresh checkout"): force the
    # switch, pin to origin, drop untracked files. Ignored files (node_modules)
    # stay, so a repo's install survives between contracts.
    run(["git", "checkout", "--force", "--quiet", head], cwd=path)
    run(["git", "reset", "--hard", "--quiet", f"origin/{head}"], cwd=path)
    run(["git", "clean", "-fd", "--quiet"], cwd=path)
    return head

def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, ""
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    b = re.search(r"wall_minutes:\s*(\d+)", m.group(1))
    fm["wall_minutes"] = int(b.group(1)) if b else 30
    raw = fm.get("blocked_by", "").strip().strip("[]")
    fm["blocked_by"] = [x.strip() for x in raw.split(",") if x.strip()]
    return fm, m.group(2)

def load_config():
    cfg = (IVY / "config.yml").read_text()
    commit_email = re.search(r"^commit_email:\s*(\S+)", cfg, re.M).group(1)
    block = re.search(r"^connected_emails:[^\n]*\n((?:[ \t]+-[^\n]*\n?)*)", cfg, re.M)
    connected = re.findall(r"-\s*(\S+)", block.group(1)) if block else []
    connected = connected or [commit_email]
    lanes = {}
    lane_block = re.search(r"^lanes:[^\n]*\n((?:[ \t]+.*\n?)*)", cfg, re.M).group(1)
    current = None
    for line in lane_block.splitlines():
        m = re.match(r"^  ([a-z-]+):\s*$", line)
        if m:
            current = m.group(1); lanes[current] = {}
        m = re.match(r"^    ([a-z]+):\s*\{(.*)\}", line)
        if m and current:
            pool, inner = m.group(1), m.group(2)
            entry = dict(re.findall(r"([a-z_-]+):\s*([^,}\s]+)", inner))
            lanes[current][pool] = entry
    return commit_email, connected, lanes

def author_connected(ident, connected):
    """True if `git var GIT_AUTHOR_IDENT` names any verified address — the
    author field is what GitHub counts, and more than one address is verified."""
    return any(f"<{e}>" in ident for e in connected)

def open_blockers(fm, done_ids):
    """Ids in blocked_by that are not yet in dispatch/done/ (order kept)."""
    return [b for b in fm.get("blocked_by", []) if b not in done_ids]

def resolve_harness(argv, which=shutil.which):
    """argv with argv[0] resolved to an absolute path, or None if not found.

    launchd hands the runner a PATH built only from /etc/paths(.d); `claude`
    lives in ~/.local/bin, which only ~/.zshrc adds. On 2026-09-02 that raised
    FileNotFoundError inside Popen *after* two contracts were claimed and the
    claim commits pushed, stranding both in `claimed` with no outcome. Resolve
    before claiming, and exec an absolute path so PATH cannot matter twice.
    """
    if not argv:
        return None
    found = which(argv[0])
    return [found] + list(argv[1:]) if found else None

def synced_runner(current, synced):
    """The synced runner to exec into, or None to carry on with this one.

    The entry point (launchd points at a dev checkout) and the checkout the
    runner syncs are different working copies, so a pushed runner change does
    not reach the running code: on 2026-09-02 a fixed attribution gate sat in
    IVY while the pre-fix gate executed from ~/Build/ivy and refused four
    contracts. Exec the synced copy, never argv[0] — argv[0] is the stale file.
    """
    try:
        if synced.resolve() == current.resolve() or not synced.is_file():
            return None
        return synced if synced.read_bytes() != current.read_bytes() else None
    except OSError:
        return None

def status_changed(prev, cur):
    """True when a part of the status a reader acts on differs. Timestamps and
    the synced sha are informational and never justify a commit on their own."""
    return any((prev or {}).get(k) != cur.get(k) for k in STATUS_KEYS)

def status_commit_needed(prev, cur, now, heartbeat_hours=STATUS_HEARTBEAT_HOURS):
    """Commit on change, and otherwise at most once per heartbeat so the cloud
    can tell an idle runner from a dead one."""
    if status_changed(prev, cur):
        return True
    try:
        last = datetime.fromisoformat((prev or {})["last_tick"])
    except (KeyError, TypeError, ValueError):
        return True
    return (now - last) >= timedelta(hours=heartbeat_hours)

def build_status(prev, result, skipped, lint_ok, now, harness=None, sha=""):
    """The runner's heartbeat. Booleans and fixed reason strings only: the file
    is public, so never a path, a hostname, or a PATH."""
    cur = {"last_tick": now.isoformat(timespec="seconds"), "runner_sha": sha,
           "harness": harness if harness is not None
                      else {h: shutil.which(h) is not None for h in ("claude", "codex")},
           "lint_ok": lint_ok, "result": result, "skipped": skipped}
    cur["since"] = (prev or {}).get("since") if prev and not status_changed(prev, cur) else cur["last_tick"]
    return cur

def publish_status(result, skipped, lint_ok, now):
    """Write STATUS_REL and commit it bot-authored when it changed or the
    heartbeat is due. The cloud scout reads it under `## Blockers`: without it
    a runner that cannot find its harness, or never ticks, is indistinguishable
    from one with nothing to do (2026-09-03: three contracts open all day,
    no claim, no way to tell why from the cloud)."""
    path = IVY / STATUS_REL
    try:
        prev = json.loads(path.read_text())
    except (OSError, ValueError):
        prev = None
    sha = run(["git", "rev-parse", "--short", "HEAD"], cwd=IVY, check=False).stdout.strip()
    cur = build_status(prev, result, skipped, lint_ok, now, sha=sha)
    path.write_text(json.dumps(cur, indent=2, sort_keys=True) + "\n")
    if status_commit_needed(prev, cur, now):
        if not bot_commit_push(f"dispatch: runner status — {result}", [path]):
            log("status push lost a race; next tick retries")

def bot_commit_push(msg, paths):
    run(["git", "add", "--"] + [str(p) for p in paths], cwd=IVY)
    run(["git"] + BOT + ["commit", "--quiet", "-m", msg], cwd=IVY)
    for attempt in range(3):
        p = run(["git", "push", "--quiet", "origin", "HEAD"], cwd=IVY, check=False)
        if p.returncode == 0:
            return True
        run(["git", "pull", "--rebase", "--quiet", "origin"], cwd=IVY, check=False)
    return False

def set_state(path, new_state, extra_fm=None):
    text = path.read_text()
    text = re.sub(r"^state: .*$", f"state: {new_state}", text, count=1, flags=re.M)
    if extra_fm:
        text = re.sub(r"^(state: .*)$", r"\1\n" + extra_fm, text, count=1, flags=re.M)
    path.write_text(text)

def lane_problem(entry):
    """Why a lane entry cannot run, or None. Checked before the claim, so a bad
    config costs a skip rather than a contract."""
    if not entry or entry.get("model") == "VERIFY":
        return "lane_unresolved"
    if entry.get("harness") == "claude-code" and entry.get("effort") not in (None, *CLAUDE_EFFORTS):
        return "lane_invalid"
    return None

def harness_argv(entry, prompt, ctype):
    h, model, effort = entry.get("harness"), entry.get("model"), entry.get("effort")
    if h == "claude-code":
        argv = ["claude", "-p", prompt, "--model", model]
        if effort:
            argv += ["--effort", effort]
        if ctype in ("build", "chore"):
            # acceptEdits alone denies git push / gh pr create in -p mode
            # (verified 2026-08-28); the worker needs the shell for its DoD.
            argv += ["--permission-mode", "acceptEdits", "--allowedTools", "Bash"]
        return argv
    if h == "codex":
        argv = ["codex", "exec", "--model", model]
        if effort:
            argv += ["-c", f'model_reasoning_effort="{effort}"']
        if ctype in ("build", "chore"):
            argv += ["-s", "workspace-write"]  # exec defaults to read-only sandbox
        return argv + [prompt]
    raise RuntimeError(f"unknown harness {h}")

def build_prompt(cid, repo, ctype, body):
    head = (f"You are an Ivy dispatch worker executing contract {cid} in a fresh checkout of "
            f"{repo}. The run is unattended: nobody can answer questions, so make routine "
            "judgment calls yourself, and if something only a person can decide blocks part of "
            "the task, finish the rest and say what is missing. The contract's Definition of done "
            "and Verification sections are the bar the work has to meet.\n\n")
    if ctype == "review":
        tail = ("\n\nReview: report every finding that could cause incorrect behaviour, a failing "
                "test, a security or data problem, or a claim the code does not back, each with a "
                "severity and your confidence; leave out pure style preferences. Tie each finding "
                "to file:line on the head you reviewed, with a proposed fix, and confirm plainly the "
                "claims that hold. The review is read-only: leave the checkout, its branches, and "
                "the pull request as they are.\n"
                "Skills: if a `code-review` skill is installed in this harness, drive the review "
                "with it (the Task above is the spec axis); otherwise review without it.\n"
                "Output: print the complete findings as markdown between two lines containing "
                f"exactly {MARK_BEGIN} and {MARK_END}, and nothing after {MARK_END}.")
    else:
        tail = ("\n\nBuild: deliver what the Task asks, at the scope it intends; if you think the "
                "Task is mistaken, say so in your summary and still do what it asks. Work on a new "
                f"branch named dispatch/{cid}, commit with the clone's configured git identity "
                "(already a connected address, so leave user.name and user.email as they are), "
                "push that branch, and open a draft pull request. The default branch is Tom's: "
                "never push to it.\n"
                "Skills: if `tdd` and `code-review` skills are installed in this harness, build "
                "test-first at the seams the Task names and review the diff against the Task "
                "before opening the PR; otherwise proceed without them.\n"
                "Output: when finished, print a short summary of what you did and what you "
                "verified (the tests you ran and their result, anything skipped and why) between "
                f"two lines containing exactly {MARK_BEGIN} and {MARK_END}.")
    return head + body.strip() + tail

def finalize(qpath, cid, dest, state, outcome_lines, msg, extra_paths=()):
    set_state(qpath, state)
    with qpath.open("a") as f:
        f.write("\noutcome:\n" + "".join(f"  {l}\n" for l in outcome_lines))
    target = IVY / "dispatch" / dest / qpath.name
    run(["git", "mv", str(qpath), str(target)], cwd=IVY)
    lint = run(["bash", "scripts/dispatch-lint.sh"], cwd=IVY, check=False)
    if lint.returncode != 0:
        log(f"LINT FAILED after finalize: {lint.stderr or lint.stdout}")
    bot_commit_push(msg, [target] + list(extra_paths))
    log(f"{cid}: {state} -> dispatch/{dest}/")

def main():
    once = "--once" in sys.argv
    dry = "--dry-run" in sys.argv
    now = datetime.now().astimezone()
    if not once and not in_window(now):
        return 0
    WORKROOT.mkdir(exist_ok=True)
    lockf = open(WORKROOT / "lock", "w")
    try:
        fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("another runner instance holds the lock; exiting"); return 0

    ensure_clone(IVY, IVY_REMOTE)
    fresh = synced_runner(Path(__file__), IVY / "scripts" / "dispatch-runner.py")
    if fresh and not os.environ.get("IVY_RUNNER_REEXEC"):
        log(f"runner differs from {IVY} — exec'ing the synced copy")
        os.environ["IVY_RUNNER_REEXEC"] = "1"
        lockf.close()          # flock released; the exec'd process re-acquires
        os.execv(sys.executable, [sys.executable, str(fresh), *sys.argv[1:]])

    lint = run(["bash", "scripts/dispatch-lint.sh"], cwd=IVY, check=False)
    if lint.returncode != 0:
        log(f"queue not lint-clean, refusing to run: {lint.stderr or lint.stdout}")
        if not dry:
            publish_status("lint_failed", [], False, now)
        return 1
    commit_email, connected, lanes = load_config()
    done_ids = {p.stem for p in (IVY / "dispatch" / "done").glob("*.md")}
    skipped = []

    for qpath in sorted((IVY / "dispatch" / "queue").glob("*.md")):
        fm, body = parse_frontmatter(qpath.read_text())
        if not fm or fm.get("state") != "open":
            continue
        cid, repo, ctype = fm["id"], fm["repo"], fm["type"]
        if datetime.fromisoformat(fm["expires"]) <= now:
            log(f"{cid}: past expiry, leaving for the failsafe to expire")
            skipped.append({"id": cid, "reason": "expired"}); continue
        blockers = open_blockers(fm, done_ids)
        if blockers:
            log(f"{cid}: blocked by {', '.join(blockers)} (not in dispatch/done/) — skipping")
            skipped.append({"id": cid, "reason": "blocked_by"}); continue
        entry = lanes.get(fm["lane"], {}).get(fm.get("pool") or "anthropic")
        problem = lane_problem(entry)
        if problem:
            log(f"{cid}: lane {fm['lane']}/{fm.get('pool') or 'anthropic'} {problem} — skipping")
            skipped.append({"id": cid, "reason": problem}); continue

        clone = WORK / repo.split("/")[-1]
        ensure_clone(clone, f"https://github.com/{repo}.git")
        if ctype == "build":
            ident = run(["git", "var", "GIT_AUTHOR_IDENT"], cwd=clone).stdout
            if not author_connected(ident, connected):
                finalize(qpath, cid, "failed", "failed",
                         [f"claimed_at: {now.isoformat(timespec='seconds')}",
                          "exit: attribution",
                          f"note: next commit would author '{ident.split('>')[0].strip()}>' — not a connected address (config.yml connected_emails)"],
                         f"dispatch: failed {cid} — attribution gate")
                skipped.append({"id": cid, "reason": "attribution_gate"}); continue

        prompt = build_prompt(cid, repo, ctype, body.split("outcome:")[0])
        argv = harness_argv(entry, prompt, ctype)
        resolved = resolve_harness(argv)
        if not resolved:
            # An environment fault, not a fault in the contract: leave it open
            # so it runs untouched once the binary is reachable, rather than
            # burning a good contract on a bad PATH.
            log(f"{cid}: harness binary '{argv[0]}' not found on PATH — leaving open; "
                f"PATH={os.environ.get('PATH', '')}")
            skipped.append({"id": cid, "reason": "harness_missing"}); continue
        argv = resolved
        if dry:
            log(f"{cid}: DRY RUN — would claim, then exec in {clone}:")
            log("  " + " ".join(shlex.quote(a if len(a) < 120 else a[:117] + "...") for a in argv))
            return 0

        set_state(qpath, "claimed", f"claimed_at: {now.isoformat(timespec='seconds')}")
        if not bot_commit_push(f"dispatch: claim {cid}", [qpath]):
            log(f"{cid}: claim push lost a race; next tick retries")
            publish_status("claim_race", skipped, True, now); return 0

        log(f"{cid}: executing via {entry['harness']} ({entry['model']}, effort "
            f"{entry.get('effort') or 'default'}), budget {fm['wall_minutes']}m")
        start = datetime.now()
        try:
            proc = subprocess.Popen(argv, cwd=clone, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, start_new_session=True)
        except OSError as e:
            # The contract is already claimed and pushed; an unhandled raise here
            # would strand it in `claimed` until expiry (2026-09-02: twice).
            finalize(qpath, cid, "failed", "failed",
                     [f"claimed_at: {now.isoformat(timespec='seconds')}",
                      "exit: harness_error", f"note: could not start {argv[0]}: {e}"],
                     f"dispatch: failed {cid} — harness would not start")
            publish_status(f"finished {cid}", skipped, True, now)
            return 0
        try:
            out, _ = proc.communicate(timeout=fm["wall_minutes"] * 60)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            out, code = (proc.communicate()[0] or ""), "timeout"
        wall = round((datetime.now() - start).total_seconds() / 60, 1)

        m = re.search(re.escape(MARK_BEGIN) + r"\n(.*?)\n" + re.escape(MARK_END), out or "", re.S)
        report_rel = f"dispatch/reports/{cid}.md"
        base = [f"claimed_at: {now.isoformat(timespec='seconds')}",
                f"finished_at: {datetime.now().astimezone().isoformat(timespec='seconds')}",
                f"harness: {entry['harness']} (dispatch-runner)",
                f"model: {entry['model']}", f"effort: {entry.get('effort') or 'default'}",
                f"wall_minutes: {wall}", f"exit: {code}"]
        if code == 0 and m:
            (IVY / report_rel).write_text(
                f"# Report — {cid}\n\nProduced by the {fm['lane']}/{fm.get('pool') or 'anthropic'} "
                f"lane, {wall} wall-minutes.\n\n{m.group(1).strip()}\n")
            finalize(qpath, cid, "done", "done",
                     base + ["artifacts:", f"  - {report_rel}"],
                     f"dispatch: done {cid} — awaiting failsafe verification",
                     extra_paths=[IVY / report_rel])
        else:
            reason = "timeout" if code == "timeout" else ("no_report" if code == 0 else "harness_error")
            tail = (out or "")[-1500:]
            (IVY / "dispatch" / "failed").mkdir(exist_ok=True)
            finalize(qpath, cid, "failed", "failed",
                     base + [f"note: {reason}; last output lines follow", "output_tail: |",
                             *("    " + l for l in tail.splitlines()[-12:])],
                     f"dispatch: failed {cid} — {reason}")
        publish_status(f"finished {cid}", skipped, True, now)
        return 0
    log("no executable contract in queue")
    if not dry:
        publish_status("idle", skipped, True, now)
    return 0

def guarded_main():
    """Never die silently: an unexpected exception is logged and, where the
    synced clone exists, published as a heartbeat so the cloud sees it."""
    try:
        return main()
    except Exception as e:  # noqa: BLE001 — the point is to catch everything
        log(f"runner error: {e!r}")
        try:
            publish_status(f"runner_error: {type(e).__name__}", [], True,
                           datetime.now().astimezone())
        except Exception as e2:  # noqa: BLE001
            log(f"status publish failed too: {e2!r}")
        return 1

if __name__ == "__main__":
    sys.exit(guarded_main())
