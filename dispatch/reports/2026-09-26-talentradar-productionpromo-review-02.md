# Report — 2026-09-26-talentradar-productionpromo-review-02

Produced by the workhorse/openai lane, 7.0 wall-minutes.

# Report — 2026-09-26-talentradar-productionpromo-review-02

Reviewed PR #4’s current draft head `8a66eda` after its 2026-09-26T02:41:15Z update.

## Verdict

- **Sign-in recovery: passes source review.** It addresses the actual Supabase Site URL fallback as documented, not just the retry UI. No callback-parameter open redirect was found.
- **Inherited production-promotion record: fails.** The known CSV-dedupe P1 is still not acknowledged. **Changes requested.**

## PR-body corroboration

Fetched via `search_pull_requests` using `repo:tompulsarlabs/talent-radar is:pr is:open`.

> “The Supabase fallback now points to production; this patch consumes failed callback parameters, shows a clear recovery message and lets the user start a fresh Google sign-in.”

> “Includes the production promotion record from 24 September and the verified owner login from 25 September.”

> “Validation: 382 tests, typecheck, lint and production build pass.”

## Sign-in recovery assessment

`docs/HANDOFF.md:23` records the substantive root-cause correction: Supabase’s Site URL changed from localhost to the production origin. The code then makes a failed callback recoverable:

- `src/lib/auth/callback-error.ts:4-29` removes only `error`, `error_code`, and `error_description`, returns a relative pathname/query/fragment, and calls `history.replaceState` rather than a navigation API.
- It never renders provider-controlled error text (`:17-19,27-29`).
- Fresh OAuth starts use the fixed `${window.location.origin}/interview` destination in `src/components/BetaEntry.tsx:69` and `src/components/InterviewBeta.tsx:195`; no callback parameter selects a destination.
- `BetaEntry` consumes the failure before auth setup (`:20-24`), offers its normal fresh Google sign-in (`:95-99`), and releases busy state on startup failure (`:63-72`). `InterviewBeta` has the parallel recovery path (`:63-68,191-198`).
- `tests/auth-callback-error.test.ts:4-32` covers query and fragment cleanup, raw-description suppression, successful-token-fragment preservation, and one-time history replacement.

Thus the callback cleanup has no open-redirect path and the UI no longer relies on reloading the failed URL.

The external Supabase setting cannot be independently verified from this read-only checkout. Also, the current head records that Vercel protection changed on 26 September and that a fresh owner browser sign-in was not rerun afterward (`docs/HANDOFF.md:7-11`). The hosted post-hardening journey therefore remains documentary evidence, not a fresh acceptance result. The legacy ungated `Pilot` route does not consume callback errors when `BETA_ADMISSION_ENABLED` is false (`src/app/page.tsx:4`, `src/components/Pilot.tsx:161-220`); no evidence establishes that configuration is active in production, so this is a coverage caveat rather than a confirmed defect.

## Findings

### P1 — inherited promotion record omits known CSV funding-row data loss

`src/lib/market/import.ts:44`  
`tests/market-signals.test.ts:16-18`  
`docs/HANDOFF.md:31-41`

The importer’s dedupe key is only `[domain, sourceUrl, eventDate]`. Rows for the same company/provider/date but with different persisted round, amount, currency, investors, announcement URL, or summary silently collapse; the test claiming different rounds are retained changes only the date.

`memory/repos/talent-radar.md:163-179` records this as an unfixed P1 across the 17 and 23 September review cycles. PR #4’s diff does not change the importer, yet its current body explicitly incorporates the 24 September promotion record and asserts passing validation. The promotion record says the application was “checked, then promoted” and reports passing CI/build (`docs/HANDOFF.md:35,41`), without disclosing the defect.

The PR body contains no CSV, funding, dedupe, round, amount, currency, investor, or data-loss acknowledgement. `docs/BETA-READINESS.md:13` only calls for testing a licensed funding export; it neither identifies nor remediates the silent-collapse risk.

Update the inherited promotion record to name the open P1, its impact, and its acceptance condition. Then fix the dedupe identity to retain distinct events and add regression cases varying round, amount, currency, and investors independently.

## Verification

- Re-fetched the current PR body through the required cross-repo search path.
- `git diff --check 90751fb..8a66eda` passed.
- The reported 382 tests, typecheck, lint, build, and external configuration checks were not rerun in this read-only review.
- No files, commits, or remote state were modified.
