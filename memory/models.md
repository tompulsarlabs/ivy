---
subject: execution-lane routing evidence
type: evidence
updated: 2026-09-05
---

# Models: lane × task-class outcomes

Routing evidence for the dispatch layer ([[ops]] for environment limits;
policy lives in `playbook.md` and `config.yml`, never here). One row per
**verified** contract — claimed-done never lands on this page. Quota events
(throttles, refusals) are observations too: record them per pool.

## Verified outcomes

| Contract | Type | Lane / pool | First-pass | Wall min | Note |
|----------|------|-------------|------------|----------|------|
| 2026-08-27-ivy-nudge-audit-01 | chore | workhorse / anthropic | yes | 8 | Memory reconciliation; interactive D1 manual run [cite:2026-08-27] |
| 2026-08-27-c2cm-review-01 | review | frontier / openai | yes | 9.7 | D2 runner's first live execution (2026-09-01); six real findings, request-changes verdict [cite:2026-09-02] |
| 2026-09-02-countersign-review-01 | review | frontier / openai | yes | 9.6 | Second D2 execution; keep-in-draft verdict, late-webhook race as top finding [cite:2026-09-02] |
| 2026-09-02-tomgreenai-context-01 | build | workhorse / anthropic | yes | 14.5 | First verified `build`; CONTEXT.md glossary, draft PR #14, exactly the one file specified [cite:2026-09-04] |
| 2026-09-02-tomgreenai-copy-02 | build | frontier / anthropic | yes | 40.0 | Draft PR #15 opened before the 40-min budget hit; runner recorded `exit: timeout` and never printed the report, verified done retroactively — see [[ops]] on the misclassification [cite:2026-09-04] |
| 2026-09-03-tomgreenai-vfx-review-01 | review | frontier / openai | yes | 5.7 | Third D2 review execution; PR #13's "review gate, not a site change" claim held, but four real defects found in the asset-generation tooling itself [cite:2026-09-04] |
| 2026-09-05-talentradar-review-01 | review | frontier / openai | yes | 7.8 | First review of `talent-radar`; PR #1's Supabase fetch layer and Radar UI, findings file:line-tied; verified via PR-body corroboration since PR #1 is still open (see [[ops]] on the search_code default-branch limit) [cite:2026-09-05] |
| 2026-09-05-tomgreenai-planetary-review-01 | review | frontier / openai | yes | 14.5 | Fourth `tomgreen.ai` review; PR #16 merged before the review even finished, so verified directly via `search_code` against 3 sampled paths [cite:2026-09-05] |

## Pool health

No throttle or refusal events recorded on either pool yet [cite:2026-08-27].

## Fleet metrics (weekly, retro-computed)

| Week ending | Verified done | Failed / waste min | Expired | Throttles | Note |
|-------------|--------------|--------------------|---------|-----------|------|
| 2026-08-28 (partial) | 1 | 0 / 0 | 0 | 0 | D1-D2 bring-up week; first contract 8 wall-min first-pass [cite:2026-08-27] |
| 2026-08-30 | 1 | 0 / 0 | 0 | 0 | No new verified outcomes this week — 3 contracts still queued unclaimed, D2 runner not yet live [cite:2026-08-29][cite:2026-08-30] |
| 2026-09-06 | 7 | 1 / 45 | 1 | 0 | D2 runner live all week: 7 new verified (5 review, 2 build), all first-pass; `review` class cleared the ≥3-verified-outcomes Pareto bar (5 straight frontier/openai first-pass) — retro stepped its default lane to `workhorse` [cite:2026-09-06]; `build` still n=2, short of the bar. First real waste (`layout-02`, 45 wall-min, no output) and first expired-unexecuted contract (`photo-02`), both `tomgreen.ai` build [cite:2026-09-04] |

## Reading

n=8 now (1 chore, 5 review, 2 build), all first-pass. `review` has run
frontier/openai five times straight, all first-pass, clearing the Pareto
bar (≥3 verified outcomes) for a lane-move trial — **retro decision,
2026-09-06:** `playbook.md`'s scout section now defaults new `review`
contracts to `lane: workhorse`, watching whether first-pass verdict
quality holds there; `frontier` stays available as an explicit per-contract
pin. `build` has its first two data points (workhorse/anthropic and
frontier/anthropic, both first-pass) —
still short of the bar, and confounded by lane: `copy-02` ran frontier
only because it was hand-pinned there after the runner-bug re-queue, not
by routing policy, so it is not yet evidence that `build` needs the
frontier tier [cite:2026-09-04].

**First real waste of the fleet, 2026-09-04:** `2026-09-02-tomgreenai-layout-02`
spent its full 45-minute budget (frontier/anthropic) and produced no PR and
no report — genuine waste, not a runner fault this time, since the runner
itself ticked correctly (contrast `copy-02` above, same failure mode by
outcome record but confirmed to have actually finished). `2026-09-02-tomgreenai-photo-02`
expired unclaimed (0 wall-minutes spent, so 0 waste-minutes, but still an
expired-unexecuted event for the weekly waste count) [cite:2026-09-04].
Prior to today, zero waste among verified contracts; 2026-09-02's four
tomgreen.ai build contracts that failed at the attribution gate and were
returned to `queue/` (not `failed/`, no worker claimed, no budget spent)
remain a runner-reliability incident, not routing waste — see [[ops]] for
the stale-checkout/PATH root causes, fixed same day [cite:2026-09-02].

## Changelog

- 2026-09-06 (retro) — `review` class cleared the Pareto bar (5 straight
  verified first-pass frontier/openai outcomes); stepped its default lane
  to `workhorse` in `playbook.md` (one of the week's two tuning
  adjustments). Added the week's fleet-metrics row: 7 newly verified, first
  real waste (45 wall-min) and first expired-unexecuted contract, both
  `tomgreen.ai` `build`.
- 2026-09-05 — two more `review` contracts verified done (`talentradar-review-01`,
  `tomgreenai-planetary-review-01`); n=6→8; `review` now has 5 straight
  first-pass frontier/openai outcomes, a stronger basis for a retro lane-move
  trial.
- 2026-09-04 — three more contracts verified (`context-01`, `copy-02` both
  `build`; `vfx-review-01` review) via the new cross-repo query-string
  technique [[ops]]; n=3→6; `review` class cleared the Pareto
  verified-outcomes bar. First real fleet waste recorded: `layout-02`
  (45 wall-min, no output) and `photo-02` (expired unclaimed).
- 2026-09-02 — both queued review contracts verified done (request-changes
  on c2-client-matrix, keep-in-draft on countersign); n=1→3, still under
  the per-class Pareto bar.
- 2026-08-30 (retro) — weekly fleet-metrics row added; still n=1, still no
  lane move (Pareto bar unmet); flagged runner capacity, not policy, as the
  binding constraint.
- 2026-08-27 — page created with the D1 proof contract as first entry.
