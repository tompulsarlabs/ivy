# Report — 2026-09-23-talentradar-execbeta-review-03

Produced by the workhorse/openai lane, 101.1 wall-minutes.

# PR #2 review — 23 September 2026

Reviewed head `520de91` against prior review head `1395d45`.

## Change audit

There are 16 commits after `1395d45`; this is not just a PR-body rewrite. `c487bfa` adds the confirmed-profile discovery implementation, API/query behavior, UI, and six tests; `ae4bbe8` changes Safari menu/sign-out behavior; `803105a` is visual-only. The remaining commits are handoff/docs/archive work. The four-destination navigation itself predates the prior review (`840a272`), so its new PR-body description does not represent a new post-review navigation implementation.

## Findings

### P1 — CSV dedupe still drops distinct funding events

`src/lib/market/import.ts:44`

The dedupe key is only `[domain, sourceUrl, eventDate]`. Same-company/provider rows with the same source/date but different round, amount, currency, investors, announcement URL, or summary collapse, with the later row silently replacing the earlier one. This is unchanged from `1395d45`.

`tests/market-signals.test.ts:16` claims distinct rounds are retained, but its differing-row case at `:18` changes only the event date.

Proposed fix: dedupe only exact normalized duplicate signals, or include provider and every persisted event/provenance field in the key. Add regression cases that differ solely in round, amount, currency, and investors.

### P3 — Per-row provider fallback is documented but unreachable

`docs/MARKET-DATA.md:7`  
`src/app/api/pilot/market/route.ts:5`

The documentation says a CSV row may supply `provider`, but the API requires a nonempty top-level `provider` even when every row supplies one.

Proposed fix: either make the top-level provider optional and let `parseMarketCSV` require a row or fallback provider, or amend the documentation to describe it as a required form-level default.

## Confirmations

- Google entry is source-confirmed: verified Google identity and server-only invite allowlists are enforced in `src/app/api/beta/admission/route.ts:31-51`; owner preapproval is restricted in `src/lib/beta/admin.ts:3-13`.

- Atomic capacity reservation is source-confirmed: `supabase/migrations/20260911100000_beta_approval.sql:72-91` locks the cohort before counting/reserving, while `:43-52` converts approved reservations once. The concurrent 20-approval coverage is in `tests/beta-approval.test.ts:24-29`.

- The migration compatibility path fails closed for new users when `beta_seats_used` is absent, while preserving configured invited/existing access through the legacy RPC: `src/app/api/beta/admission/route.ts:19-25,44-50`. The live migration remains explicitly unapplied, so this is code/CI evidence rather than a fresh hosted acceptance result.

- The bounded private CSV provenance claim otherwise holds: parser-required provider/source/date fields are at `src/lib/market/import.ts:5-10,38-40`; saves are authenticated and owner-scoped as `provider_reported` at `src/app/api/pilot/market/route.ts:7-14`; only owner-scoped source URLs are forwarded for independent research at `src/lib/market/sources.ts:4-10`.

- “Known live now” holds in source: `src/app/api/pilot/route.ts:162-186` reads only the authenticated owner’s saved profile; `src/lib/pilot/job-search.ts:35-41` requires confirmation and reads only `functions`; `src/lib/pilot/jobs.ts:5-41` is a read-only title query with no ranking or model call. Forged request context and unconfirmed profiles are covered by `tests/job-search-api.test.ts:35-53` and `tests/job-search.test.ts:80-118`. The six live-feed checks are recorded, but not independently rerun, in `docs/HANDOFF.md:21-23`.

- `docs/BETA-READINESS.md:17` correctly states the current 338-test count. Its 279 count at `:57` is explicitly historical. Current PR CI reports 41 passing files and 338 passing tests, plus typecheck, lint, and build success.

No files, commits, or remote state were changed, per the read-only rule.
