# Report — 2026-09-26-ivy-playbookretune-review-03

Produced by the workhorse/openai lane, 12.3 wall-minutes.

# PR #21 review 03 — `c78f8c8`

**Decision: BLOCK.** The cloud green-fallback and blind-comparison findings are closed, but the memory-grader P2 remains open.

| Carried finding | Verdict |
|---|---|
| P1: cloud green fallback | **Closed** |
| P2: memory-grader rigor | **Still open** |
| P2: blind comparison / current steering | **Closed** |
| Immutable byte identity | **Pass** |

## P1 — cloud green fallback: closed

The actual `45abc4d` diff adds a fourth green decision: exact `repo:` plus `head:dispatch/<id>` PR searches for each contract claimed today in `playbook.md:156-161`. It also makes a contract-recorded PR that no search finds an `unknown` day, requiring alert plus journal rather than a false grey at `:169-174`.

Its added cases exercise the real failure shape, not a generic PR: a failed-but-previously-claimed build contract with its dispatch branch and PR #67 URL in the timeout tail. `failsafe-pr-lead-found` requires green, PR provenance, real work, no journal, and promotion; `failsafe-pr-lead-missing` requires unknown, alert, and journal. Both candidate reps pass every check in `evals/routines/results/2026-09-25-candidate-14d3685.jsonl`.

Direct head check: no P1-relevant path changed from `45abc4d` through `c78f8c8`.

## P2 — memory-grader rigor: still open

`14d3685` materially improves the grader: it adds paragraph/block matching in `scripts/eval-routines.py:203-244`, structural account requirements, and mutation tests in `scripts/eval-routines-test.py:212-242`. But `failsafe-ongoing-condition` still accepts an appended restatement.

The case’s duplicate guards only count literal `still dark` and `N missed windows` deltas (`evals/routines/cases/failsafe-ongoing-condition/case.json:9-18,39-52`), while its structural account check is only `account.after >= 1` (`:63-68`), not exactly one.

Against the case’s replay fixture, appending this paragraph before `## Changelog` passes all checks:

> At the 2026-09-23 failsafe, the scanner remains dark since 09-08: 15 calendar days. The outage blocks the clean-tree signal and leaves local work invisible [cite:2026-09-23].

It leaves the two literal counts unchanged (9 → 9 and 9 → 9), creates one matching account block, and adds no changelog entry. Thus it passes despite appending a new outage account instead of rewriting the current one in place, contrary to `playbook.md:357-370`.

The evaluator, test, and affected case are unchanged from `14d3685` at `c78f8c8`. Require exactly one complete current account and add this calendar-day-worded mutation.

## P2 — blind comparison: closed

The actual `4b3a413` diff replaces shared-parent sandboxes with fresh `mkdtemp` directories, invokes Claude with `--restricted`, `--add-dir <sandbox>`, and `--strict-mcp-config`, cleans up after grading, and refuses to run when `--restricted` is unavailable (`scripts/eval-routines.py:345-391,487-490`).

Raw result artifacts establish the full rerun matrix:

- baseline: 58 rows, 29 cases, two reps, old-control steering;
- candidate: 58 rows, 29 cases, two reps, `14d3685` steering;
- transition: 29 rows, 29 cases, one rep, `14d3685` steering.

All 145 rows are `ok`, use distinct opaque sandbox names, and record no absolute, traversal, or transcript path in stored file-read entries. `playbook.md`, `CLAUDE.md`, and `routines/` have no diff from `14d3685` to `c78f8c8`, so later commits did not drift the tested steering.

Caveat: `471336a` corrected one checker after the run, so stored rows retain the old 43/48 candidate score rather than the disclosed regraded 45/48. Regrade before using that headline quantitatively; this does not reopen the confinement/current-steering finding.

## Immutable sections: pass

I directly extracted the bytes from `## Immutable: counting rules` through the end of `## Immutable: dispatch guardrails` from `main` and `c78f8c8`.

- Main: 5,951 bytes, SHA-256 `1ff07cfe1235f507233a6dad628331cc11a9c14cc15f59401da09e687d9c0f03`
- PR head: 5,951 bytes, same SHA-256

Byte comparison is equal; zero bytes differ.

Branch lineage verified: `e2d21c3 → 4b3a413 → 45abc4d → 14d3685 → 471336a → c78f8c8`. All cited branch-head paths were fetched directly from PR head.
