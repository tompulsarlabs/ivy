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

import tempfile
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

print()
print("eval-routines-test: " + ("ok" if not failures else f"{len(failures)} failing"))
sys.exit(1 if failures else 0)
