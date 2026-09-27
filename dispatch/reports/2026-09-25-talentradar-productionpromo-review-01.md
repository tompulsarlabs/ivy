# Report — 2026-09-25-talentradar-productionpromo-review-01

Produced by the workhorse/openai lane, 3.4 wall-minutes.

# PR #4 review — 25 September 2026

Reviewed PR #4 head `6534feec0f8c74eeca6c60c8ec8a12f3894caa84`, based on merged `main` `90751fb`.

**Result: the CSV-dedupe P1 is not acknowledged in the promotion record.** PR #4 reads as a private-production promotion with clean validation, while the known data-loss defect remains unchanged.

PR-body corroboration, fetched via `search_pull_requests` with `repo:tompulsarlabs/talent-radar`:

> “Records the authorised promotion of merged main (`90751fb`) to private production…”

> “Updates beta readiness to distinguish deployed existing-member access from the still-closed approval cohort… No runtime code or schema changes in this PR.”

## Findings

### P1 — Production-promotion record omits the known CSV data-loss defect

`docs/HANDOFF.md:3-13`  
`src/lib/market/import.ts:44`

The promotion record says the application was “checked, then promoted” and reports passing validation, but does not disclose the known unfixed import defect. The full fetched PR body likewise contains no mention of CSV, funding, deduplication, rounds, amounts, currencies, investors, or this limitation.

The defect remains verbatim at `src/lib/market/import.ts:44`: its identity key is only `[domain, sourceUrl, eventDate]`. Rows differing only in persisted funding fields such as round, amount, currency, investors, announcement URL, or summary silently overwrite one another. `tests/market-signals.test.ts:16-18` still varies only the event date despite claiming different rounds are retained.

Because PR #4 changes only documentation, it cannot resolve this runtime defect. The production record should explicitly name the open P1, its impact, and the remediation/acceptance condition rather than presenting promotion as clean.

### P3 — Remaining beta gates omit the documented-but-unreachable row-level provider fallback

`docs/BETA-READINESS.md:11-15`  
`docs/BETA-READINESS.md:13`  
`docs/MARKET-DATA.md:7`  
`src/app/api/pilot/market/route.ts:5`

The stated gate list is incomplete. Its only CSV-related gate says to “test a licensed funding export through the existing CSV importer”; it does not require resolving the existing provider-contract mismatch.

`docs/MARKET-DATA.md:7` promises that each CSV row may supply `provider`, but `src/app/api/pilot/market/route.ts:5` requires a non-empty top-level `provider` before the parser can read row values. A row-only provider therefore fails despite the documented path.

The PR body frames the remaining limitation as the “still-closed approval cohort” and an owner-login passkey step, with no provider-fallback acknowledgement. Add a gate to either support row-level provider fallback or correct the documentation, with a regression/acceptance case for that input.

No files, commits, or remote state were changed.
