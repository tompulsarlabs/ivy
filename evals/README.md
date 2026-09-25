# Evals

## The routine eval

`evals/routines/` replays real days against Ivy's four routines and grades the
decisions they report. It is the regression check for any change to how a
routine decides: `playbook.md`, `CLAUDE.md`, `routines/*.md`, and the files
they point at.

Each case is a directory in `evals/routines/cases/`:

- `case.json`: the routine, the moment (`when`), the commit whose repository
  state it replays (`state_rev`, always a commit from just before that
  routine really ran), whether it guards existing behaviour
  (`intent: preserve`) or checks a deliberate change (`intent: change`), and
  the checks.
- `evidence.md`: what the routine's external lookups return (GitHub MCP
  searches, `check.sh`, whether a push notification gets through). The
  sandbox has no network, so this file stands in for the tools.
- `files/`: overlay files that make the one change the case is about (a stale
  scan, a failed contract, a rewritten journal section). In `case.json`,
  `json_merge` patches a JSON file instead and `delete` removes paths from
  the replayed state.

`scripts/eval-routines.py` builds the sandbox (the `state_rev` tree, the
variant's steering files, the overlay, `eval/evidence.md`, and never
`evals/`), runs the routine's prompt headless with `claude -p` and only the
Read, Glob, and Grep tools, and asks for the run's decisions as JSON. Checks
are deterministic assertions over that JSON; nothing is graded by a model.

A case with `measures` is graded on the files it leaves instead of its own
account, because a routine can label an append "update in place". Its run
also gets Edit and Write. Each measure reads one file, optionally only
above `above_heading` or below `below_heading`, before and after the run.
It counts a regex (`count`), or the paragraphs and list items that match
every regex in `blocks`: that is how a case asks for one paragraph holding
an ongoing condition's start, count, citation, and consequence together.
Checks read `_measures.<name>.before`, `.after`, and `.delta`. The row keeps
a unified diff of each measured file under `diffs`, so a result can be
read, not only counted. `scripts/eval-routines-test.py` grades each memory
case's real page after wrong edits (a restatement appended or reworded, a
changelog entry, today's citation beside a stale account, the account
deleted) and after the right one. A run whose writes were denied is recorded
as `denied`, not scored.

The model sees its working directory, so each sandbox is a fresh temporary
directory with a random name, outside the work directory: no case id or
variant label appears in any path the run can see. The run is
`--restricted`, which keeps the file tools inside the sandbox, so the
work directory's transcripts and results, named by case and variant, stay
out of reach. Restricted mode also ignores every settings file,
so a machine's allow rules, hooks, and personal CLAUDE.md reach no run.
It skips the sandbox's own CLAUDE.md too; `--add-dir` of the sandbox
restores it, and the model's context is then byte for byte an unrestricted
run's. A sandbox is deleted once its run is graded; the row keeps the answer
and the diffs. `IVY_EVAL_LIVE=1 python3 scripts/eval-routines-test.py` checks
the confinement with two real runs, for a few cents.

## Run it

```bash
python3 scripts/eval-routines-test.py          # grader and case-set checks, free
python3 scripts/eval-routines.py list

# the prompts the triggers ran before this version, against main's steering files
python3 scripts/eval-routines.py run --label baseline --steering origin/main --prompts live --reps 2
# the routines/*.md prompts against your working tree
python3 scripts/eval-routines.py run --label candidate --steering WORKTREE --prompts repo --reps 2
python3 scripts/eval-routines.py compare <baseline results.jsonl> <candidate results.jsonl>
```

`run` needs a Claude Code with `--restricted` (2.1.282 has it) and stops
before spending anything without it. Scope a run with `--cases 'check-*'`.
The default model (`DEFAULT_MODEL` in the script) is the one the four
triggers run; pass `--model` to try another and `--effort` only if the
trigger sets one. A full pass is 29 runs per rep, $0.15 to $1.70 each at
list price (about $24 a rep for the candidate) and about 25 minutes a rep
at `--jobs 5`. `grade` re-scores saved answers after a check is edited,
without re-running anything.

Results rows carry the served model (a run served by a different model is
not scored), cost, turns, the files the routine read, and its full answer;
transcripts stay in the work directory. A committed summary of each
comparison lives in `evals/routines/results/`.

## Read the numbers

Two reps per case is a smoke test, not a benchmark: with 29 cases a
difference of one or two cases is inside the noise. Read the per-check table,
and open the answer of any check that flips between variants before believing
it. A case passes only when every check passes, and every case fails on an
empty answer (`eval-routines-test.py` enforces that), so "passed" never means
"did nothing".

The eval measures decisions given the evidence, not tool use: it cannot tell
whether a routine would have made the right GitHub query, only what it
concludes from the results. The sandbox cannot commit, push, or notify, so it
grades the commits and notifications a routine reports; only a `measures`
case is graded on edits it really made.

## Add a case

Copy the closest case directory, pick the `state_rev` just before the real
routine ran that day (`git log --format='%h %ad %s' --date=iso`), make one
change through `files/` or `json_merge`, and write checks for the outcome
rather than the path to it. Include at least one check that an empty answer
fails, then run `eval-routines-test.py`. A new failure mode seen in a journal
is the best source of a case.

Operators: `eq`, `ne`, `in`, `contains`, `contains_any`, `not_contains_any`,
`matches`, `len_eq`, `len_le`, `len_ge`, `max_str_len`, `truthy`, `falsy`,
`is_null` on a `path`; `any`, `all`, `none`, and `count` (with `eq`, `le`,
`ge`) over a list with a `where`; `before` for order within a list; and `and`,
`or`, `not`. Text matching is case-insensitive.
