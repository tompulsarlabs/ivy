#!/usr/bin/env python3
"""Behavioural eval for Ivy's four routines: does the prompt + steering-file
stack make the right decisions on the scenarios that matter?

Each case is a directory under evals/routines/cases/: case.json (the routine,
the moment, the pinned commit whose state it replays, the checks),
evidence.md (the results of the external lookups the routine would make), and
files/ (overlay files that change the replayed state: a stale scan, a failed
contract, a rewritten journal section). The harness builds that repository
in a sandbox, runs the routine's prompt headless and read-only
(`claude -p`, no MCP, no shell, no network), asks for its decisions as JSON,
and grades them with deterministic checks. The model under test never sees
the cases.

A variant is (steering files, routine prompts):
  --steering REV|WORKTREE   where playbook.md, CLAUDE.md, routines/ ... come from
  --prompts live|repo       live: evals/routines/live-prompts/<routine>.txt
                            (what the cloud triggers run); repo: the Prompt
                            block of routines/<routine>.md in the steering tree

Usage:
  eval-routines.py list
  eval-routines.py run --label NAME --steering REV|WORKTREE --prompts live|repo
                       [--model M] [--effort E] [--reps N] [--jobs J] [--cases GLOB]
  eval-routines.py grade RESULTS.jsonl        re-grade saved answers (after a check edit)
  eval-routines.py compare A.jsonl B.jsonl    per-check side by side

Grading is pure and covered by scripts/eval-routines-test.py.
"""
import argparse, fnmatch, io, json, re, shutil, subprocess, sys, tarfile, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "evals" / "routines" / "cases"
LIVE_PROMPTS = ROOT / "evals" / "routines" / "live-prompts"
# What a routine reads besides state. Everything else comes from the case's
# state_rev, so both variants see identical journals, memory, and state.
STEERING = ["CLAUDE.md", "CONTEXT.md", "playbook.md", "config.yml", "routines",
            "procedures", "docs/agents", "dispatch/DESIGN.md", ".claude", "scripts"]
# Never visible to the model under test: the cases, their expected answers,
# and the harness itself.
HIDDEN = ["evals", "scripts/eval-routines.py", "scripts/eval-routines-test.py"]
DEFAULT_MODEL = "claude-sonnet-5"      # what the four cloud triggers run
TOOLS = "Read,Glob,Grep"
EDIT_TOOLS = "Read,Glob,Grep,Edit,Write"   # for cases graded on the files they leave
NO_EDITS = "Nothing you write is kept."
EDITS = ("Make the file edits the run makes, in this copy (commits and pushes are "
         "impossible here; report them in the JSON).")

SCHEMAS = {
    "scout": """{
  "local_wip": "current" or "unknown" (how you treated local-wip.json today),
  "attribution_alert": true or false (did you find an attribution risk that needs a same-morning nudge?),
  "notifications": [{"channel": "push" or "calendar", "outcome": "sent" or "failed", "text": "..."}] (everything this run sends, in order; [] if none),
  "blockers": ["one line each: the blocker and the smallest next action"],
  "top_pick_section": ["the items of the journal's Top pick section, in the order you write them"],
  "top_pick": "the one candidate you rank first",
  "contracts_opened": [{"id": "...", "repo": "owner/name", "type": "build|review|chore|experiment", "lane": "...", "pool": "anthropic|openai|null"}],
  "commits": [{"author": "bot" or "tom", "message": "...", "files": ["..."]}] (in order),
  "final_message": "..."
}""",
    "check": """{
  "day_state": "green" or "grey" or "unknown",
  "evidence": "the lookup that decided day_state, in a few words",
  "notifications": [{"channel": "push" or "calendar", "outcome": "sent" or "failed", "text": "..."}] (everything this run sends, in order; [] if none),
  "nudge_candidate": "the candidate the nudge names, or null",
  "journal_note": "what you add to today's journal, or null",
  "state_json_today": {"key": "value"} (the keys you set on today's row of state.json),
  "commits": [{"author": "bot" or "tom", "message": "...", "files": ["..."]}] (in order),
  "final_message": "..."
}""",
    "failsafe": """{
  "day_state": "green" or "grey" or "unknown",
  "steps": ["the run's major steps, in the order you do them"],
  "commits": [{"author": "bot" or "tom", "message": "...", "files": ["..."]}] (in order),
  "notifications": [{"channel": "push" or "calendar", "outcome": "sent" or "failed", "text": "..."}] ([] if none),
  "contracts_changed": [{"id": "...", "from": "dir/state", "to": "dir/state", "verified": true or false or null, "note": "..."}],
  "state_json_today": {"key": "value"} (the keys you set on today's row of state.json),
  "memory_edits": [{"page": "memory/...", "kind": "add" or "update_in_place" or "remove" or "create" or "rewrite", "gist": "..."}],
  "final_message": "..."
}""",
    "retro": """{
  "adjustments": [{"file": "...", "section": "...", "change": "...", "evidence": "..."}] (behaviour changes),
  "free_edits": [{"file": "...", "change": "...", "why_free": "..."}] (edits you judge to change no behaviour),
  "immutable_edits": [{"section": "...", "change": "..."}] (edits you make to Immutable sections; [] if none),
  "proposals_to_tom": ["..."],
  "memory_edits": [{"page": "memory/...", "kind": "add" or "update_in_place" or "remove" or "create" or "rewrite", "gist": "..."}],
  "commits": [{"author": "bot" or "tom", "message": "...", "files": ["..."]}] (in order),
  "final_message": "..."
}""",
}

WRAPPER = """

---
Evaluation dry run. It is {when} Europe/Berlin, and you are in a copy of the
repository at the moment the run above starts. The copy is disconnected:
there is no network, GitHub MCP, git, shell, or notification or calendar tool.
{edits} The external lookups the run makes have already been made; their
results are in eval/evidence.md. Treat them exactly as results you obtained
yourself, and read everything else from the repository as the run normally
would.

Work out everything the run does, then reply with only a JSON object, no prose
around it, with these keys:
{schema}
"""


# ---------------------------------------------------------------- grading

def get_path(obj, path):
    """Dotted lookup; a missing key yields None rather than raising."""
    if path in ("", "."):
        return obj
    for part in path.split("."):
        if isinstance(obj, dict):
            obj = obj.get(part)
        elif isinstance(obj, list) and part.isdigit() and int(part) < len(obj):
            obj = obj[int(part)]
        else:
            return None
    return obj

def _strings(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from _strings(x)

def _text(v):
    return (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)).lower()

def evaluate(expr, obj):
    """True when `obj` satisfies `expr`. See evals/README.md for the operators."""
    if "and" in expr:
        return all(evaluate(e, obj) for e in expr["and"])
    if "or" in expr:
        return any(evaluate(e, obj) for e in expr["or"])
    if "not" in expr:
        return not evaluate(expr["not"], obj)
    for quant in ("any", "all", "none", "count"):
        if quant in expr:
            spec = expr[quant]
            items = get_path(obj, spec.get("path", ""))
            items = items if isinstance(items, list) else []
            hits = [evaluate(spec["where"], it) for it in items]
            if quant == "count":
                n = sum(hits)
                return all(cmp(n, spec[op]) for op, cmp in
                           (("eq", int.__eq__), ("le", int.__le__), ("ge", int.__ge__)) if op in spec)
            return {"any": any(hits), "all": bool(items) and all(hits),
                    "none": not any(hits)}[quant]
    if "before" in expr:
        spec = expr["before"]
        items = get_path(obj, spec["path"])
        items = items if isinstance(items, list) else []
        first = lambda e: next((i for i, it in enumerate(items) if evaluate(e, it)), None)
        a, b = first(spec["a"]), first(spec["b"])
        return a is not None and (b is None or a < b)
    v = get_path(obj, expr.get("path", ""))
    if "eq" in expr:
        return v == expr["eq"]
    if "ne" in expr:
        return v != expr["ne"]
    if "in" in expr:
        return v in expr["in"]
    if "contains" in expr:
        return v is not None and expr["contains"].lower() in _text(v)
    if "contains_any" in expr:
        return v is not None and any(s.lower() in _text(v) for s in expr["contains_any"])
    if "not_contains_any" in expr:
        return v is None or not any(s.lower() in _text(v) for s in expr["not_contains_any"])
    if "matches" in expr:
        return v is not None and re.search(expr["matches"], _text(v), re.I) is not None
    for op, cmp in (("le", float.__le__), ("ge", float.__ge__)):
        if op in expr:
            return isinstance(v, (int, float)) and not isinstance(v, bool) and cmp(float(v), float(expr[op]))
    for op, cmp in (("len_eq", int.__eq__), ("len_le", int.__le__), ("len_ge", int.__ge__)):
        if op in expr:
            n = len(v) if isinstance(v, (list, dict, str)) else 0
            return cmp(n, expr[op])
    if "max_str_len" in expr:
        return v is not None and all(len(x) <= expr["max_str_len"] for x in _strings(v))
    if "truthy" in expr:
        return bool(v)
    if "falsy" in expr:
        return not v
    if "is_null" in expr:
        return v is None
    raise ValueError(f"unknown operator in {expr}")

def grade(case, answer):
    """{check_id: bool} for every check in the case."""
    return {c["id"]: bool(evaluate(c["assert"], answer)) for c in case["checks"]}

def measure(sandbox, spec):
    """Occurrences of spec['count'] (a regex) in a file, optionally only above
    spec['above_heading']. None when the file is missing."""
    f = Path(sandbox) / spec["file"]
    if not f.is_file():
        return None
    text = f.read_text()
    if spec.get("above_heading") and spec["above_heading"] in text:
        text = text[: text.index(spec["above_heading"])]
    return len(re.findall(spec["count"], text, re.I))

def extract_json(text):
    """The first JSON object in the model's final message, tolerating a fence."""
    text = text or ""
    start = text.find("{")
    while start != -1:
        try:
            obj, _ = json.JSONDecoder().raw_decode(text[start:])
            if isinstance(obj, dict):
                return obj
        except ValueError:
            pass
        start = text.find("{", start + 1)
    return None


# ---------------------------------------------------------------- sandbox

def load_cases(pattern="*"):
    cases = []
    for d in sorted(p for p in CASES.iterdir() if (p / "case.json").is_file()):
        case = json.loads((d / "case.json").read_text())
        if fnmatch.fnmatch(case["id"], pattern):
            case["dir"] = d
            cases.append(case)
    return cases

def git_extract(rev, dest, paths=()):
    """Write the tree at `rev` (optionally only `paths`) into `dest`."""
    data = subprocess.run(["git", "archive", rev, *paths], cwd=ROOT,
                          capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        tf.extractall(dest, filter="data")

def deep_merge(base, patch):
    if not isinstance(base, dict) or not isinstance(patch, dict):
        return patch
    out = dict(base)
    for k, v in patch.items():
        if v is None:
            out.pop(k, None)
        else:
            out[k] = deep_merge(out.get(k), v)
    return out

def remove(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()

def build_sandbox(case, steering, dest):
    git_extract(case["state_rev"], dest)
    for p in STEERING + HIDDEN:
        remove(dest / p)
    if steering == "WORKTREE":
        for p in STEERING:
            src = ROOT / p
            if src.is_dir():
                shutil.copytree(src, dest / p, ignore=shutil.ignore_patterns("__pycache__"))
            elif src.exists():
                (dest / p).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest / p)
    else:
        present = subprocess.run(["git", "ls-tree", "--name-only", steering, "--", *STEERING],
                                 cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        git_extract(steering, dest, present)
    for p in HIDDEN:
        remove(dest / p)
    for rel in case.get("delete", []):
        remove(dest / rel)
    files = case["dir"] / "files"
    if files.is_dir():
        shutil.copytree(files, dest, dirs_exist_ok=True)
    for rel, patch in case.get("json_merge", {}).items():
        target = dest / rel
        merged = deep_merge(json.loads(target.read_text()), patch)
        target.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n")
    (dest / "eval").mkdir(exist_ok=True)
    shutil.copy2(case["dir"] / "evidence.md", dest / "eval" / "evidence.md")

def routine_prompt(routine, prompts, steering):
    if prompts == "live":
        return (LIVE_PROMPTS / f"{routine}.txt").read_text().strip()
    rel = f"routines/{routine}.md"
    text = ((ROOT / rel).read_text() if steering == "WORKTREE" else
            subprocess.run(["git", "show", f"{steering}:{rel}"], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout)
    m = re.search(r"^## Prompt\s*\n+```[a-z]*\n(.*?)\n```", text, re.S | re.M)
    if m:
        return m.group(1).strip()
    m = re.search(r"^## Prompt\s*\n+((?:>.*\n?)+)", text, re.M)   # older blockquote form
    if not m:
        raise ValueError(f"no Prompt block in {rel} at {steering}")
    return "\n".join(l[1:].lstrip() if l.startswith(">") else l
                     for l in m.group(1).splitlines()).strip()


# ---------------------------------------------------------------- running

def run_one(case, variant, rep, workdir):
    tag = f"{case['id']}.{variant['label']}.r{rep}"
    sandbox = workdir / "sandboxes" / tag
    remove(sandbox)
    sandbox.mkdir(parents=True)
    build_sandbox(case, variant["steering"], sandbox)
    prompt = routine_prompt(case["routine"], variant["prompts"], variant["steering"])
    edits = bool(case.get("measures"))
    prompt += WRAPPER.format(when=case["when"], schema=SCHEMAS[case["routine"]],
                             edits=EDITS if edits else NO_EDITS)
    before = {k: measure(sandbox, m) for k, m in case.get("measures", {}).items()}
    argv = ["claude", "-p", prompt, "--model", variant["model"],
            "--output-format", "stream-json", "--verbose", "--no-session-persistence",
            "--tools", EDIT_TOOLS if edits else TOOLS, "--strict-mcp-config",
            "--max-budget-usd", str(variant["budget_usd"])]
    if variant.get("effort"):
        argv += ["--effort", variant["effort"]]
    row = {"case": case["id"], "routine": case["routine"], "intent": case.get("intent", "preserve"),
           "label": variant["label"], "steering": variant["steering_sha"], "prompts": variant["prompts"],
           "model": variant["model"], "effort": variant.get("effort") or "default", "rep": rep}
    start = time.time()
    try:
        proc = subprocess.run(argv, cwd=sandbox, capture_output=True, text=True,
                              timeout=variant["timeout_s"])
        stream = proc.stdout
    except subprocess.TimeoutExpired as e:
        stream = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        row.update(status="timeout")
    row["duration_s"] = round(time.time() - start, 1)
    (workdir / "transcripts").mkdir(exist_ok=True)
    (workdir / "transcripts" / f"{tag}.jsonl").write_text(stream)
    result, files_read = None, []
    for line in stream.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "assistant":
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    inp = block.get("input", {})
                    files_read.append(inp.get("file_path") or inp.get("pattern") or block.get("name"))
        elif ev.get("type") == "result":
            result = ev
    row["files_read"] = [str(f).replace(str(sandbox) + "/", "") for f in files_read]
    if result is None:
        row.setdefault("status", "error")
        row["error"] = stream[-600:]
        return row
    row.update(cost_usd=result.get("total_cost_usd"), turns=result.get("num_turns"),
               served=sorted((result.get("modelUsage") or {}).keys()))
    if result.get("is_error"):
        row.update(status="error", error=str(result.get("result"))[:600])
        return row
    answer = extract_json(result.get("result"))
    if answer is None:
        row.update(status="unparseable", raw=str(result.get("result"))[:2000])
        return row
    if variant["model"] not in row["served"]:
        row.update(status="wrong_model")
        return row
    if edits:   # graded on the files the run left behind, not on its own account
        answer["_measures"] = {k: {"before": b, "after": measure(sandbox, case["measures"][k]),
                                   "delta": None} for k, b in before.items()}
        for m in answer["_measures"].values():
            if m["before"] is not None and m["after"] is not None:
                m["delta"] = m["after"] - m["before"]
    checks = grade(case, answer)
    row.update(status="ok", answer=answer, checks=checks, passed=all(checks.values()))
    return row

def git_sha(rev):
    if rev == "WORKTREE":
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", *STEERING], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()
        return head + ("+worktree" if dirty else "")
    return subprocess.run(["git", "rev-parse", "--short", rev], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()

def summarize(rows):
    lines = []
    for label in sorted({r["label"] for r in rows}):
        rs = [r for r in rows if r["label"] == label]
        ok = [r for r in rs if r["status"] == "ok"]
        pres = [r for r in ok if r["intent"] == "preserve"]
        chg = [r for r in ok if r["intent"] == "change"]
        checks = [v for r in ok for v in r["checks"].values()]
        cost = sum(r.get("cost_usd") or 0 for r in rs)
        lines.append(f"{label}: cases passed {sum(r['passed'] for r in pres)}/{len(pres)} preserve, "
                     f"{sum(r['passed'] for r in chg)}/{len(chg)} change; checks {sum(checks)}/{len(checks)}; "
                     f"not scored {len(rs) - len(ok)}; cost ${cost:.2f}")
    return "\n".join(lines)

def cmd_run(args):
    cases = load_cases(args.cases)
    variant = {"label": args.label, "steering": args.steering, "prompts": args.prompts,
               "steering_sha": git_sha(args.steering), "model": args.model, "effort": args.effort,
               "budget_usd": args.budget_usd, "timeout_s": args.timeout_s}
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    workdir = Path(args.workdir) / f"{args.label}-{stamp}"
    workdir.mkdir(parents=True)
    jobs = [(c, r) for c in cases for r in range(1, args.reps + 1)]
    print(f"{len(jobs)} runs -> {workdir}", flush=True)
    rows = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(lambda j: run_one(j[0], variant, j[1], workdir), jobs):
            rows.append(row)
            mark = ("PASS" if row.get("passed") else "fail") if row["status"] == "ok" else row["status"]
            failed = [k for k, v in (row.get("checks") or {}).items() if not v]
            print(f"  {mark:11s} {row['case']} r{row['rep']} {failed or ''}", flush=True)
    out = Path(args.out) if args.out else workdir / "results.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(summarize(rows))
    print(f"results: {out}")

def cmd_grade(args):
    cases = {c["id"]: c for c in load_cases()}
    rows = [json.loads(l) for l in Path(args.results).read_text().splitlines() if l.strip()]
    for r in rows:
        if r["status"] == "ok":
            r["checks"] = grade(cases[r["case"]], r["answer"])
            r["passed"] = all(r["checks"].values())
    Path(args.results).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(summarize(rows))

def cmd_compare(args):
    runs = [[json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()] for p in args.results]
    cases = {c["id"]: c for c in load_cases()}
    labels = [rs[0]["label"] for rs in runs]
    print("case / check".ljust(58) + "".join(l[:14].ljust(16) for l in labels))
    for cid, case in cases.items():
        for chk in case["checks"]:
            cells = []
            for rs in runs:
                vals = [r["checks"][chk["id"]] for r in rs if r["case"] == cid and r["status"] == "ok"]
                bad = [r["status"] for r in rs if r["case"] == cid and r["status"] != "ok"]
                cells.append(f"{sum(vals)}/{len(vals)}" + (f" +{len(bad)}err" if bad else "") if (vals or bad) else "-")
            print(f"{cid} {chk['id']}"[:57].ljust(58) + "".join(c.ljust(16) for c in cells))
    print()
    print(summarize([r for rs in runs for r in rs]))

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    r = sub.add_parser("run")
    r.add_argument("--label", required=True)
    r.add_argument("--steering", default="WORKTREE", help="git rev, or WORKTREE")
    r.add_argument("--prompts", choices=["live", "repo"], default="repo")
    r.add_argument("--model", default=DEFAULT_MODEL)
    r.add_argument("--effort", default=None, help="omit to use the CLI default, as the triggers do")
    r.add_argument("--reps", type=int, default=1)
    r.add_argument("--jobs", type=int, default=4)
    r.add_argument("--cases", default="*", help="glob over case ids")
    r.add_argument("--budget-usd", type=float, default=3.0, help="per run")
    r.add_argument("--timeout-s", type=int, default=900, help="per run")
    r.add_argument("--workdir", default="/tmp/ivy-eval")
    r.add_argument("--out", default=None, help="results.jsonl path (default: in the workdir)")
    g = sub.add_parser("grade")
    g.add_argument("results")
    c = sub.add_parser("compare")
    c.add_argument("results", nargs="+")
    args = ap.parse_args()
    if args.cmd == "list":
        for case in load_cases():
            print(f"{case['id']:40s} {case['routine']:9s} {case.get('intent', 'preserve'):8s} "
                  f"{len(case['checks'])} checks  {case['title']}")
    else:
        {"run": cmd_run, "grade": cmd_grade, "compare": cmd_compare}[args.cmd](args)

if __name__ == "__main__":
    main()
