---
id: 2026-09-28-talentradar-csvdedupe-build-01
type: build
state: done
claimed_at: 2026-09-28T16:59:02+02:00
repo: tompulsarlabs/talent-radar
lane: workhorse
pool: anthropic
created: 2026-09-28T09:00:00+02:00
created_by: scout
expires: 2026-09-30T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Fix the CSV funding-row de-dupe bug at `src/lib/market/import.ts:44`,
promoted to `build` per the playbook's 3-cycle rule: four separate review
contracts have re-confirmed it unfixed —
`2026-09-17-talentradar-execbeta-review-02` (first found, P2),
`2026-09-23-talentradar-execbeta-review-03` (re-confirmed, upgraded to P1),
`2026-09-25-talentradar-productionpromo-review-01` (re-confirmed, PR #4's
promotion record doesn't acknowledge it), and
`2026-09-26-talentradar-productionpromo-review-02` (re-confirmed again at
PR #4's post-rewrite head) — while `build` has queued no new contract on
this repo since 2026-09-02.

The de-dupe key is currently `[domain, sourceUrl, eventDate]` only, so two
undated funding rows from the same company/provider URL with different
round, amount, currency, or investors silently collapse to one row —
contradicting the "without merging different rounds" intent stated in
`tests/market-signals.test.ts:16`.

Widen the de-dupe key so rows that differ in round, amount, currency, or
investors are never collapsed together, while rows that are genuine
duplicates (same company/provider/date and same round/amount/currency/investors)
still collapse as intended. Add or extend a `tests/market-signals.test.ts`
case that exercises exactly the scenario the four reviews found: two
undated same-company/provider rows with differing round/amount/currency —
assert both survive de-dupe.

## Definition of done

A branch `dispatch/2026-09-28-talentradar-csvdedupe-build-01` pushed to
`tompulsarlabs/talent-radar` with a draft PR containing the fix to
`src/lib/market/import.ts` and the new/extended test case. The PR
description names the four prior review contracts this closes and quotes
the specific finding text being fixed, so the next review can verify
against the claim rather than re-discovering it.

## Verification (cloud-checkable)

A draft PR opened by `tompulsarlabs` on `tompulsarlabs/talent-radar`
exists, created on or after 2026-09-28, referencing this contract id, and
its body names `src/lib/market/import.ts:44` and at least one of the four
prior review contract ids above (PR-body corroboration per `memory/ops.md`
— this repo sits outside this session's direct file access).

## Notes

Attribution gate: `talent-radar`'s tracked local checkouts all show
`author_email_ok: true` in `local-wip.json` as of 2026-09-26 — no
attribution block expected.

outcome:
  requested_model: claude-opus-5
  requested_effort: medium
  effective_model: unknown
  effective_effort: unknown
  harness_version: 2.1.277
  source_revision: 90751fb605db871391d01d14bc59d0ca6d5eeeb2
  runner_sha256: d1dcb91ae9056b12701fe0f4e65a8c9f35f7fd3d1d9e1005df4e7058625b2ce0
  config_sha256: 351a9899ed2a593507305cdda33f838f7197bed09e297a0c2174487b0206c28a
  prompt_sha256: 58f1f618cb0dc34045f3abc9161f47af209053275b0369f1fcb880f1a8fe9fb7
  context_capture: runner_prompt_only
  usage_capture: unavailable
  claimed_at: 2026-09-28T16:59:02+02:00
  finished_at: 2026-09-28T17:04:29+02:00
  harness: claude-code (dispatch-runner)
  model: claude-opus-5
  wall_minutes: 5.4
  exit: 0
  artifacts:
    - dispatch/reports/2026-09-28-talentradar-csvdedupe-build-01.md
