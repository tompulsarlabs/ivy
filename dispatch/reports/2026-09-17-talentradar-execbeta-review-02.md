# Report — 2026-09-17-talentradar-execbeta-review-02

Produced by the workhorse/openai lane, 20.1 wall-minutes.

# PR #2 review

## Change since the 09-05 review

This is a substantive update, not just PR metadata: the prior-review head is `a7bf289` (2026-09-05), while the current PR head is `1395d45` (2026-09-16 12:40:20Z), 38 seconds before the reported `updated_at`. There are 33 intervening commits.

They add the executive pilot, knowledge/evidence and grounded-evaluation paths, capped approval/admission and private funding CSV import on 11 September, then the 16 September workspace/Notion UI revisions. The current tip itself adds the Notion preview-verification record; its parent changes the Notion UI states.

## Findings

### P2 — CSV import silently drops distinct undated funding events

`src/lib/market/import.ts:44` de-duplicates on only `[domain, sourceUrl, eventDate]`, although `eventDate` is optional. Two legitimate funding rows from the same provider/company profile URL with no funding date but different round, amount, currency, or investors collapse to one record. This contradicts the intended “without merging different rounds” behaviour in `tests/market-signals.test.ts:16`.

Proposed fix: include stable event attributes such as round, amount, currency and investors in the deduplication identity, or retain all rows unless a provider event ID is available. Add a regression case with two same-URL, no-date, different-round rows.

### P3 — Readiness documentation presents obsolete test totals as current

`docs/BETA-READINESS.md:1` calls 297 tests “Current,” and `docs/BETA-READINESS.md:45` reports 279, while the current-head validation record says 332 at `docs/HANDOFF.md:21` and `:31`. The document is dated 10 September, but its present-tense wording makes the current PR validation state ambiguous.

Proposed fix: change those counts to explicitly historical “as of 10 September” figures, or update the readiness document with the current 332-test evidence and its limits.

## Confirmations

- Admission is correctly gated in the activated path: `src/components/BetaEntry.tsx:63-69` initiates Google OAuth, `:81` withholds children until admission succeeds, and `src/app/api/beta/admission/route.ts:34-38` derives identity from Supabase and requires a confirmed Google identity. Owner approval is separately limited to configured owner emails at `src/lib/beta/admin.ts:9-12`.

- Capacity reservation is soundly serialized: `supabase/migrations/20260911100000_beta_approval.sql:33`, `:64-67`, and `:79-91` share the cohort lock and count both activated admissions and outstanding approvals. The migration test covers competing approvals and release of a declined unused reservation at `tests/beta-approval.test.ts:24-29`.

- The approval-migration compatibility path fails closed for new users. If `beta_seats_used` is absent, `src/app/api/beta/admission/route.ts:44-50` returns `closed` before invoking the old admission RPC for an uninvited user, while preserving existing/configured-owner entry. `docs/BETA-ADMISSION.md:20-24` accurately states that the approval migration remains unapplied and requests must remain paused.

- CSV provenance claims are appropriately limited to retained, member-supplied attribution, not provider verification. The parser requires HTTPS source URLs and valid dates at `src/lib/market/import.ts:3-4,38-40`; saved imports are owner-scoped and labelled `provider_reported` at `src/app/api/pilot/market/route.ts:10-14`. `docs/MARKET-DATA.md:3-5,11-15` explicitly says this is not a provider integration and raw imports do not become confirmed facts, vacancies, or live jobs.

- The private evaluator keeps internal criterion IDs, guidance and rationales behind the release boundary: `src/lib/pilot/private/evaluation.ts:94-128` releases only fixed labels and quotations that are present in candidate turns. The recorded evaluator review also correctly limits its model-quality evidence to small synthetic runs at `evals/interview-evaluator-review-2026-09-10.md:3-5,24-28`.

- The 332 deterministic-test count is statically consistent with the current suite: 309 direct `it` cases plus six parameterized suites expanding to 23 cases. CI is configured to run test, typecheck, lint, and build at `.github/workflows/ci.yml:28-39`. The browser claims are properly scoped: `docs/HANDOFF.md:21` says the checks used isolated auth/API doubles and did not exercise hosted Google auth, microphone flow, candidate data, or model quality.

No checks were re-executed: `node_modules` is absent, and the requested read-only mode forbids installing dependencies or producing build/test artefacts. No file was written, committed, or pushed under that rule.
