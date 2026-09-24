# Report — 2026-09-24-ivy-playbookretune-review-01

Produced by the frontier/openai lane, 16.9 wall-minutes.

# PR #21 adversarial review — `5937264`

**Verdict: block.** One P1 and three P2 findings. The Immutable byte-identity and reported arithmetic hold, but the rewritten green path can misclassify an already-green day and the eval overstates its behavioral coverage.

## Findings

### P1 — The cloud green path can fire the failsafe on an already-green day

`playbook.md:25-26` says opened PRs, issues, and PR reviews count. The fallback at `playbook.md:142-153` omits reviews entirely and relies on searches that the committed fixture demonstrates can miss opened PRs.

Specifically, `evals/routines/cases/failsafe-timeout-promote/evidence.md:19-20` reports zero same-day PRs, while `:48-52` records PR #67 opened by `tompulsarlabs` that same day. Because dispatch verification happens only after securing the day (`playbook.md:287-316`), both candidate runs classified the day grey, created a Tom-authored journal contribution, then discovered PR #67 afterward (`evals/routines/results/2026-09-23-candidate.jsonl:21-22`). The case still passes because `failsafe-timeout-promote/case.json:8-33` checks only contract promotion.

This silently misrecords real-work days, fires unnecessary failsafes, and corrupts streak/conversion evidence.

**Proposed fix:** until Tom provides and names an authoritative cloud-capable check, treat an incomplete zero-result MCP search as unknown rather than grey. Include same-day contract-linked PR discovery before the grey decision and support PR reviews explicitly. Add deterministic cases requiring an already-opened PR—and a review-only day—to remain green with no Tom-authored journal commit.

### P2 — The 4/4 change score does not prove the transformations claimed

The results claim exact in-place date/count/citation updates and a single consolidated current-state line at `evals/routines/results/2026-09-23.md:92-97`.

However:

- `evals/routines/cases/failsafe-ongoing-condition/case.json:8-69` checks only generic occurrence counts. It permits deleting every “still dark” line, placing today’s citation elsewhere, and retaining an unrelated “scanner” mention.
- `evals/routines/cases/retro-collapse-sediment/case.json:8-35` permits zero outage restatements plus any generic scanner mention; it does not require one valid current-state line or preservation of first/latest citations.
- Although `evals/README.md:31-36` says measured cases grade edited files, the committed JSONL retains only counts and model self-report, not the final file or diff.

Thus 4/4 is arithmetically true under the current graders, but the cited behavior is not reproducible from committed evidence.

**Proposed fix:** retain each run’s final file or unified diff and assert the exact consolidated/current-state structure, including began date, latest confirmation, counts, current citation, blocked condition, and required first/latest citations. Then rerun and regenerate the comparison.

### P2 — The comparison is neither blind nor run at the reviewed head

`scripts/eval-routines.py:12-13` says the model never sees cases, but `:317-320` places the answer-bearing case ID and `baseline`/`candidate`/`transition` label in its working-directory name, and `:341-342` runs Claude there. Concrete leakage appears at `evals/routines/results/2026-09-23-candidate.jsonl:1`, whose first tool path contains `check-blocker-nudge-cap.candidate.r1`.

Additionally, the candidate and transition used steering commit `3ac7b33`, not `5937264`, as disclosed at `evals/routines/results/2026-09-23.md:12-25`. Nearly every candidate run read `config.yml`, which changed afterward.

**Proposed fix:** use opaque randomized sandbox names, keep case/variant mappings only in the harness, and rerun baseline, candidate, and transition against the exact merge candidate.

### P2 — PR #18’s Ivy cases are not all covered by runnable equivalents

Only 3 of PR #18’s 10 Ivy cases have full deterministic equivalents. Examples:

- `scout-parked-repo/case.json:23-30` excludes the parked repo but does not require choosing the active alternative.
- `check-green-silent/case.json:8-64` never requires an evidence source or `state_json_today.signal_source`.
- `failsafe-grey-journal/evidence.md:31-46` supplies uncheckable PR-head paths, but `failsafe-grey-journal/case.json:8-136` contains no contract-verification assertion.
- `failsafe-timeout-promote/case.json:8-33` does not require preservation of the timeout observation.
- `retro-no-thin-lane-move/case.json:8-42` does not test excluding unverified/skipped-path outcomes from the sample.
- `retro-cap-and-evidence/case.json:8-58` permits zero to two changes rather than requiring a justified no-change outcome.

**Proposed fix:** port each missing criterion as a deterministic runnable assertion and rerun, or narrow the PR-body claim to the subset actually covered.

## Confirmed claims

- **Immutable section:** byte-identical. The complete seven-section block is 110 LF-terminated lines and 5,946 bytes on both `main` (`776e515`) and `5937264`, with SHA-256 `292c1e83511eb72b3f9dbae511f7581fbe94e6327871a49a0333612bbe4856e3`. No P1 boundary violation exists.

- **Eval arithmetic:** full regrading of all 125 stored rows reproduces `evals/routines/results/2026-09-23.md:31-40` exactly: baseline 35/46 preserve and 0/4 change; candidate 45/46 and 4/4; transition 21/23 and 1/2. The no-regression statement at `:74-75` is true under the committed assertions. Candidate’s sole failure is the 171-character `green_by` value described at `:77-82`.

- **PR #23 conflict:** real. Both PRs modify the Haiku effort configuration around `config.yml:73-80` and implement lane-effort validation/CLI arguments around `scripts/dispatch-runner.py:218-244` and `:336-340`. A three-way merge produces conflicts in both files.

- **`check.sh` open question:** honestly disclosed, not hidden. `playbook.md:30-33` still names `scripts/check.sh`; `playbook.md:142-159` explicitly describes the fallback; `scripts/check.sh` is unchanged; and `retro-immutable-proposal/case.json:10-44` requires proposing the Immutable correction to Tom. A restricted run exits 2 as stated. The fallback’s correctness problem is the P1 above.

- **PR #18 overlap:** real, including conflicts across the playbook, four routine prompts, eval documentation, and runner. Only the blanket coverage claim fails.

- **Commit signatures:** exact. GitHub reports commits 1–19 (`ac6c8f9` through `51bbdc0`) as unverified with `unknown_key`, and commits 20–26 (`7055d40` through `5937264`) as valid. The committer changes to `Claude <noreply@anthropic.com>` at `7055d40`, while the signing-key fingerprint remains the same, supporting the stated explanation. A squash merge creates one new mainline commit without making the 19 unverified source commits ancestors of `main`.

## Scope and verification note

No `code-review` skill was installed, so this was a manual adversarial review. The checkout remained clean and unmodified.

GitHub now reports PR #21 at `1142d8b`, one commit beyond the contracted `5937264`. That additional commit is validly signed and changes only runner effort quoting and the skip-reason name; it does not resolve the findings above. This report remains anchored to the explicitly requested `5937264`.
