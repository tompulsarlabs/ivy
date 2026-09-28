# Report — 2026-09-27-ivy-playbookretune-review-04

Produced by the workhorse/openai lane, 14.8 wall-minutes.

# PR #21 review 04 — `e466bb3`

Scope: reviewed `c78f8c8...e466bb3` (`cdd97b2`, `e466bb3`) as requested. The PR branch has since advanced to `afdfefe`; `e466bb3` remains an ancestor.

## Overall verdict: PASS

No blocking finding. All four requested checks hold.

| Check | Verdict | Severity | Confidence |
|---|---|---:|---:|
| Memory-grader P2 closure | Pass | — | High |
| `grade` re-run | Pass, with test-coverage caveat | — | High |
| Immutable byte identity | Pass | — | High |
| `e466bb3` corrections | Pass, with temporal clarification | — | High |

## 1. Memory-grader finding: closed

`cdd97b2` exercises the exact review-03 paragraph (`scripts/eval-routines-test.py:230-234`) both appended before `## Changelog` and inside the existing account for both failsafe cases (`:236-250`). It also adds the no-count, confirmation, and second-account variants (`:251-256`) plus the retro older-count case (`:264-277`).

The fixed cases add broad window/day measures and structural account/current-day checks: `failsafe-ongoing-condition/case.json:14-102` and `failsafe-ongoing-collapsed/case.json:18-93`. The test asserts both the exact rejected check set and diff-based remeasurement equivalence (`scripts/eval-routines-test.py:198-216`).

Read-only replay of the exact fixtures and mutations produced 10 mismatched expectations under `cdd97b2^` and 0/28 under `e466bb3`. In particular, review-03’s calendar-day paragraph and its inside-account form passed the old condition grader but fail `no_restatement` under the fixed one. P2 is closed.

## 2. `grade` re-run claim: accurate

`apply_diff` validates and applies hunks (`scripts/eval-routines.py:386-408`); `remeasured` rebuilds each case fixture and applies stored diffs (`:410-423`); and `grade` invokes it for measured rows (`:552-563`).

I replayed all 55 stored memory diffs from the ten 2026-09-24/25 JSONL artifacts: 23 condition, 19 collapsed, and 13 retro rows. All reconstructed without an apply error and round-tripped to their stored unified diff. No memory-row pass/fail outcome changes.

The only full-regrade changes are the three already-disclosed `471336a` scout corrections—one 2026-09-24 transition row and two 2026-09-25 candidate rows—as documented in `evals/routines/results/2026-09-25.md:100-110`. This supports the `cdd97b2` claim that it adds no pass/fail changes; the reproduced candidate result is 45/48 preserve and 218/224 checks (`:323-327`).

Caveat, not a finding: checked-in tests cover synthetic inversion/malformed diffs and fixture remeasurement (`scripts/eval-routines-test.py:171-216`), not an external `patch(1)` run over all 55 artifacts. The actual corpus replay validates the shipped regrade behavior.

## 3. Immutable sections: byte-identical

Extracting bytes from `## Immutable: counting rules` through immediately before `## Tunable` gives identical results for `main`, `c78f8c8`, `cdd97b2`, and `e466bb3`:

- 5,951 bytes
- SHA-256 `1ff07cfe1235f507233a6dad628331cc11a9c14cc15f59401da09e687d9c0f03`
- Zero differing bytes

At `e466bb3`, the checked block is `playbook.md:10-120`.

## 4. `e466bb3` corrections: accurate

The baseline correction is correct. The results table identifies baseline steering as `2aa1829` from `main` before v10, while candidate and transition use `14d3685` (`evals/routines/results/2026-09-25.md:59-63`). All 58 stored baseline rows carry `2aa1829`; sandbox construction extracts the requested steering revision (`scripts/eval-routines.py:296-312`).

The retro-count correction is historically correct: at the original `14d3685`/`c78f8c8` test, the retro had four negative variants (`c78f8c8:scripts/eval-routines-test.py:235-242`). `cdd97b2` adds the fifth, “older count in other words,” at `e466bb3:scripts/eval-routines-test.py:272-273`. The results text distinguishes the historical four (`evals/routines/results/2026-09-25.md:147-149`) from the current five (`:160-161`). It would be inaccurate to describe the current `e466bb3` test as having four, but the correction itself is scoped to the original run-time test and is accurate.

## Standards

No documented-standard or actionable smell finding. `CLAUDE.md:6-17` keeps behavior in the playbook and requires evaluation for behavioral changes; this diff changes evaluator, cases, tests, and results only. The small unified-diff applicator is narrowly scoped and tested, not speculative generality.

## Spec

No finding. The diff satisfies the four contract checks: it closes the prior P2 with a sensitive regression test, rebuilds old memory pages from stored diffs, preserves Immutable bytes, and corrects the results narrative with the required historical distinction.

Axis summary: Standards 0 findings; Spec 0 findings.

Per the explicit read-only rule, this report is printed rather than written or committed at `dispatch/reports/2026-09-27-ivy-playbookretune-review-04.md`.
