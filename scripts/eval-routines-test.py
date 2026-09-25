#!/usr/bin/env python3
"""Checks for the grading half of eval-routines.py: the assertion operators,
answer extraction, and the case set itself. A grader that passes an empty
answer measures nothing, so every case must fail on a null run.

Run: python3 scripts/eval-routines-test.py   (exit 0 = green)
"""
import importlib.util, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("evalr", HERE / "eval-routines.py")
evalr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evalr)
ev = evalr.evaluate

failures = []
def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        failures.append(name)

ans = {
    "day_state": "grey",
    "notifications": [{"channel": "push", "outcome": "failed", "text": "x"},
                      {"channel": "calendar", "outcome": "sent", "text": "Ship today: tomgreen.ai #34"}],
    "commits": [{"author": "tom", "files": ["journal/2026-09-23.md"]},
                {"author": "bot", "files": ["state.json"]},
                {"author": "bot", "files": ["memory/repos/ivy.md"]}],
    "state_json_today": {"failsafe_fired": True, "signal_source": "github-mcp:search_commits"},
    "blockers": ["Local-WIP scanner dark 15 days: confirm the launchd job"],
}
SENT = {"path": "outcome", "eq": "sent"}
check("eq on a path", ev({"path": "day_state", "eq": "grey"}, ans))
check("contains is case-insensitive over a list", ev({"path": "blockers", "contains": "LOCAL-WIP"}, ans))
check("contains_any / not_contains_any",
      ev({"path": "day_state", "contains_any": ["x", "gre"]}, ans)
      and not ev({"path": "day_state", "not_contains_any": ["grey"]}, ans))
check("a missing path satisfies not_contains_any", ev({"path": "nope", "not_contains_any": ["a"]}, ans))
check("a missing path fails contains", not ev({"path": "nope", "contains": "a"}, ans))
check("any / none / all over a list",
      ev({"any": {"path": "notifications", "where": {"path": "channel", "eq": "calendar"}}}, ans)
      and ev({"none": {"path": "commits", "where": {"and": [{"path": "author", "eq": "tom"},
                                                            {"path": "files", "contains": "state.json"}]}}}, ans)
      and not ev({"all": {"path": "commits", "where": {"path": "author", "eq": "bot"}}}, ans))
check("all over an empty list is false", not ev({"all": {"path": "x", "where": {"eq": 1}}}, {"x": []}))
check("count with eq", ev({"count": {"path": "notifications", "where": SENT, "eq": 1}}, ans))
check("count with le/ge", ev({"count": {"path": "notifications", "where": {"path": "outcome", "truthy": True}, "ge": 2, "le": 2}}, ans))
check("before: first match of a precedes first match of b",
      ev({"before": {"path": "commits", "a": {"path": "author", "eq": "tom"},
                     "b": {"path": "files", "contains": "memory/"}}}, ans))
check("before is false when a never matches",
      not ev({"before": {"path": "commits", "a": {"path": "author", "eq": "nobody"},
                         "b": {"path": "files", "contains": "memory/"}}}, ans))
check("before is true when b never matches",
      ev({"before": {"path": "commits", "a": {"path": "author", "eq": "tom"},
                     "b": {"path": "files", "contains": "dispatch/"}}}, ans))
check("max_str_len over nested values",
      ev({"path": "state_json_today", "max_str_len": 40}, ans)
      and not ev({"path": "state_json_today", "max_str_len": 10}, ans))
check("max_str_len fails on a missing value", not ev({"path": "nope", "max_str_len": 10}, ans))
check("len_eq on a missing list is 0", ev({"path": "nope", "len_eq": 0}, ans))
check("list index in a path", ev({"path": "commits.0.author", "eq": "tom"}, ans))
check("or / not", ev({"or": [{"path": "day_state", "eq": "green"}, {"not": {"path": "day_state", "eq": "green"}}]}, ans))

check("le / ge compare numbers", ev({"path": "n", "le": 0}, {"n": -1}) and ev({"path": "n", "ge": 2}, {"n": 2.5}))
check("le fails on a missing number", not ev({"path": "n", "le": 0}, {}))
check("le does not treat a bool as a number", not ev({"path": "n", "le": 1}, {"n": True}))

import os, re, secrets, subprocess, tempfile
with tempfile.TemporaryDirectory() as tmp:
    (Path(tmp) / "memory").mkdir()
    (Path(tmp) / "memory" / "p.md").write_text("Still dark. still dark.\n## Changelog\n- still dark\n")
    spec = {"file": "memory/p.md", "count": "still dark", "above_heading": "## Changelog"}
    check("measure counts matches above the heading only", evalr.measure(tmp, spec) == 2)
    check("measure counts the whole file without a heading",
          evalr.measure(tmp, {"file": "memory/p.md", "count": "still dark"}) == 3)
    check("measure counts matches below the heading only",
          evalr.measure(tmp, {"file": "memory/p.md", "count": "still dark", "below_heading": "## Changelog"}) == 1)
    check("measure below a missing heading is 0",
          evalr.measure(tmp, {"file": "memory/p.md", "count": "still dark", "below_heading": "## Nope"}) == 0)
    check("measure of a missing file is None", evalr.measure(tmp, {"file": "nope.md", "count": "x"}) is None)
    d = evalr.file_diffs(Path(tmp), {"memory/p.md": "Still dark.\n## Changelog\n"})
    check("file_diffs shows the edit a run made", "+- still dark" in d["memory/p.md"] and d["memory/p.md"].startswith("--- a/memory/p.md"))

a, b = evalr.new_sandbox(), evalr.new_sandbox()
try:
    check("sandboxes are fresh, empty directories", a != b and a.is_dir() and not any(a.iterdir()))
    check("a sandbox sits in the temp directory, never under the work directory",
          a.parent == Path(tempfile.gettempdir()).resolve() and Path("/tmp/ivy-eval") not in a.parents)
    check("a sandbox path names no case and no variant",
          all(w not in str(a) for w in ("failsafe", "ongoing", "candidate", "baseline", "transition", "ivy-eval")))
finally:
    for d in (a, b):
        d.rmdir()

variant, box = {"model": "m", "budget_usd": 1.0}, Path("/tmp/k2j3h4g5")
for edits in (False, True):
    argv = evalr.claude_argv("p", variant, edits, box)
    mode = "edit" if edits else "read-only"
    check(f"{mode} runs are restricted and skip MCP", "--restricted" in argv and "--strict-mcp-config" in argv)
    check(f"{mode} runs get file tools only",
          argv[argv.index("--tools") + 1] == (evalr.EDIT_TOOLS if edits else evalr.TOOLS)
          and "Bash" not in evalr.EDIT_TOOLS)
    check(f"{mode} runs add only the sandbox and never bypass permissions",
          [argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"] == [str(box)]
          and "bypassPermissions" not in argv and not any("dangerously" in a for a in argv))
    check(f"{mode} runs accept edits only when the case measures them",
          ("acceptEdits" in argv) == edits)

kept = {}
def fake_run_in(sandbox, case, variant, rep, workdir):
    (sandbox / "memory.md").write_text("edited")
    kept["path"] = sandbox
    return {"status": "ok"}
real_run_in, evalr.run_in = evalr.run_in, fake_run_in
try:
    evalr.run_one({"id": "c"}, {"label": "l"}, 1, Path("/nonexistent"))
    check("a sandbox is deleted once its run is graded", not kept["path"].exists())
finally:
    evalr.run_in = real_run_in
check("runs load the sandbox's CLAUDE.md through --add-dir",
      evalr.claude_env().get("CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD") == "1")

check("extract_json reads a bare object", evalr.extract_json('{"a": 1}') == {"a": 1})
check("extract_json tolerates a fence and prose",
      evalr.extract_json('Here you go:\n```json\n{"a": {"b": [1, 2]}}\n```\n') == {"a": {"b": [1, 2]}})
check("extract_json skips a stray brace", evalr.extract_json("set {x} then {\"a\": 2}") == {"a": 2})
check("extract_json returns None without an object", evalr.extract_json("no json here") is None)

cases = evalr.load_cases()
check("cases load", len(cases) >= 20)
check("case ids are unique", len({c["id"] for c in cases}) == len(cases))
for case in cases:
    ids = [c["id"] for c in case["checks"]]
    check(f"{case['id']}: check ids unique", len(ids) == len(set(ids)))
    check(f"{case['id']}: has evidence", (case["dir"] / "evidence.md").is_file())
    for null in ({}, {"notifications": [], "commits": [], "contracts_opened": [], "memory_edits": []}):
        graded = evalr.grade(case, null)
        check(f"{case['id']}: an empty answer fails the case ({len(null)} keys)", not all(graded.values()))

# One real run per mode, a few cents, only with IVY_EVAL_LIVE=1: the file
# tools stay inside the sandbox even when the directory beside it holds
# transcripts named by case and variant, and CLAUDE.md still loads.
if os.environ.get("IVY_EVAL_LIVE"):
    with tempfile.TemporaryDirectory() as tmp:
        root, token = Path(tmp).resolve(), secrets.token_hex(8)
        leak = root / "candidate-20260101-000000" / "transcripts" / "scout-daily-cap.candidate.r1.jsonl"
        leak.parent.mkdir(parents=True)
        leak.write_text(f"LEAKED-{token}\n")
        sandbox = root / "sandbox"
        sandbox.mkdir()
        (sandbox / "CLAUDE.md").write_text("The project word is MARIGOLD.\n")
        (sandbox / "inside.txt").write_text("INSIDE-OK\n")
        prompt = ("State the project word from your instructions. Read inside.txt. Then try each of "
                  f"these and report what it returned: Read ../{leak.relative_to(root)}; Read {leak}; "
                  "Glob **/*.jsonl with path ..; Grep LEAKED with path ..")
        for edits in (False, True):
            mode = "edit" if edits else "read-only"
            ask = prompt + ("; then write the word DONE to note.txt here." if edits else ".")
            out = subprocess.run(evalr.claude_argv(ask, {"model": evalr.DEFAULT_MODEL, "budget_usd": 0.5},
                                                   edits, sandbox),
                                 cwd=sandbox, env=evalr.claude_env(), capture_output=True, text=True,
                                 timeout=300).stdout
            check(f"live {mode}: a file inside the sandbox is readable", "INSIDE-OK" in out)
            check(f"live {mode}: CLAUDE.md loads", "MARIGOLD" in out)
            check(f"live {mode}: nothing beside the sandbox is readable", token not in out)
            if edits:
                check("live edit: a write inside the sandbox lands", (sandbox / "note.txt").is_file())

# The memory cases grade the page a run leaves. Each case's real fixture page,
# edited the right way, passes its measure checks; each wrong edit below fails
# the check named, including a deleted account replaced by unrelated text and a
# restatement that avoids the words "still dark".
by_id = {c["id"]: c for c in cases}
OUTAGE = [r"scanner|local-wip", r"\bdark\b", r"09-08|missed\s+windows"]

def outage_block(text):
    found = [b for b in evalr.blocks(text) if all(re.search(rx, b, re.I) for rx in OUTAGE)]
    assert len(found) == 1, len(found)
    return found[0]

def graded(case_id, edit):
    """The case's measure checks on its fixture page after edit(text)."""
    case = by_id[case_id]
    with tempfile.TemporaryDirectory() as tmp:
        sandbox = Path(tmp)
        evalr.build_sandbox(case, "WORKTREE", sandbox)
        before = {k: evalr.measure(sandbox, m) for k, m in case["measures"].items()}
        page = sandbox / "memory" / "repos" / "ivy.md"
        page.write_text(edit(page.read_text()))
        answer = {"_measures": evalr.measured(case, before, sandbox),
                  "state_json_today": {"failsafe_fired": True}}
        return evalr.grade(case, answer)

def expect(case_id, name, edit, failing):
    g = graded(case_id, edit)
    check(f"{case_id}: {name} fails exactly {failing or 'nothing'}", sorted(k for k, v in g.items() if not v) == failing)

def moved_forward(text, old_date, old_count, new_count):
    """The latest restatement rewritten in place for 09-23."""
    block = outage_block(text)
    new = (block.replace(f"{old_date} failsafe", "2026-09-23 failsafe")
                .replace(old_count, new_count).replace("[cite:2026-09-22]", "[cite:2026-09-23]"))
    assert new != block
    return text.replace(block, new)

LOG_ENTRY = "- 2026-09-23 (failsafe) — confirmed the outage.\n"
def logged(text):
    return text.replace("## Changelog\n\n", "## Changelog\n\n" + LOG_ENTRY, 1)

for cid, old_count in (("failsafe-ongoing-condition", "28 missed windows /\n14 calendar days"),
                       ("failsafe-ongoing-collapsed", "28 missed windows / 14 calendar days")):
    fwd = lambda t, c=old_count: moved_forward(t, "2026-09-22", c, c.replace("28", "30").replace("14", "15"))
    restated = ("Still dark at the 2026-09-23 failsafe: 30 missed windows / 15 calendar days since "
                "09-08, and the carry-over pattern stays blind [cite:2026-09-23].")
    reworded = restated.replace("Still dark", "The scanner is dark again")
    one = "one_account" if cid.endswith("collapsed") else "no_restatement"
    expect(cid, "an in-place rewrite", fwd, [])
    after = lambda t, extra: fwd(t).replace(outage_block(fwd(t)), outage_block(fwd(t)) + extra)
    expect(cid, "an appended restatement", lambda t: after(t, "\n\n" + restated), [one])
    expect(cid, "a restatement in other words", lambda t: after(t, " " + reworded), [one])
    expect(cid, "a changelog entry for the confirmation", lambda t: logged(fwd(t)), ["no_log_entry"])
    expect(cid, "today's citation beside a stale account",
           lambda t: t.replace("## Activity\n", "## Activity\n\nRe-checked tonight; dark still [cite:2026-09-23].\n"),
           ["account"])
    expect(cid, "the account deleted, unrelated text in its place",
           lambda t: t.replace(outage_block(t), "The runner went dark on 09-08; 30 missed windows [cite:2026-09-23]."),
           ["account", "one_account"] if cid.endswith("collapsed") else ["account"])

collapsed = ("The scanner has been dark since `local-wip.json` last landed 2026-09-08T15:45 CEST: 21 missed "
             "windows / 11 calendar days at the 2026-09-19 failsafe, eight days past the 3-day bar "
             "[cite:2026-09-13] [cite:2026-09-19]. While it stays dark, the carry-over pattern above goes blind.")
expect("retro-collapse-sediment", "a collapse to one paragraph", lambda t: t.replace(outage_block(t), collapsed), [])
expect("retro-collapse-sediment", "the page left as it was", lambda t: t, ["collapsed"])
expect("retro-collapse-sediment", "a collapse that keeps a second restatement",
       lambda t: t.replace(outage_block(t), collapsed + "\n\nStill dark at the 2026-09-20 retro: 23 missed "
                           "windows since 09-08 [cite:2026-09-20]."), ["collapsed"])
expect("retro-collapse-sediment", "a collapse that drops the first citation",
       lambda t: t.replace(outage_block(t), collapsed.replace("[cite:2026-09-13] ", "")), ["account"])
expect("retro-collapse-sediment", "the account deleted", lambda t: t.replace(outage_block(t), "Nothing to report."),
       ["account", "collapsed"])

print()
print("eval-routines-test: " + ("ok" if not failures else f"{len(failures)} failing"))
sys.exit(1 if failures else 0)
