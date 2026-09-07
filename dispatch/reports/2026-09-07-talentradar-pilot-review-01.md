# Report — 2026-09-07-talentradar-pilot-review-01

Produced by the workhorse/openai lane, 2.9 wall-minutes.

# PR #2 adversarial review

Reviewed current head `066c62125c876367344097a479f440702be81b7c`.

## Finding

### P2 — Interview “evaluation” is an unscored capture harness and does not exercise the production interview contract

- Locations: `scripts/eval-interviews.ts:5`, `scripts/eval-interviews.ts:31-55`, `src/lib/pilot/model.ts:37-67`, `src/app/api/pilot/route.ts:494-508`
- The case `expect` text is parsed and copied into results but never assessed. Each variant is marked `pending human review`; there is no rubric result, pass/fail criterion, blinded comparison, or aggregation. Further, the harness uses `responses.create()` with a raw transcript, while production uses `responses.parse()` with the `Turn` schema and application-provided `context`, `state`, `control`, and command-specific `outputRules`. It therefore cannot demonstrate that the adapted prompt behaves correctly in the runtime users receive.
- The documentation accurately avoids a false quality-pass claim: `docs/PILOT.md:47-49` says human review is required and the live evaluation was not run. This is not a self-reported pass, but it is not yet a completed comparative evaluation either.
- Proposed fix: run both variants through the same structured `Turn` path and session inputs as production; define a version-blinded review rubric for every case expectation, record reviewer verdicts and comparative results, and require the resulting artifact before making a model-quality claim. Add deterministic assertions for observable controls where possible.

## Confirmations

### Owner-scoped RLS

Sound on the reviewed PR head. `pilot_records` applies an authenticated, enabled-owner predicate to every record kind, so confirmed profiles and editable outreach drafts receive the same owner isolation: `supabase/migrations/20260906120000_executive_pilot.sql:101-117`. Authenticated users receive only `SELECT`, while connections and usage receive no authenticated grant. Server reads and writes derive `owner` from the validated bearer token and re-scope record access to that owner: `src/lib/pilot/server.ts:28-51`, `src/lib/pilot/server.ts:66-110`. The migration test exercises Alice/Bob record isolation, denied client writes, denied connection reads, and disabled-member denial: `tests/pilot.test.ts:110-137`.

### Encrypted Notion token and read-only outreach path

Sound in the reviewed code. Tokens are AES-256-GCM sealed with a validated 32-byte key and random IV, retrieved only by server-only code, and never returned by an API response: `src/lib/pilot/notion.ts:10-33`, `src/lib/pilot/notion.ts:62-69`. The OAuth callback stores only the sealed token, after signed-state, cookie, and active-membership checks: `src/app/api/pilot/notion/route.ts:10-35`, `src/app/api/pilot/notion/route.ts:63-70`.

No reachable application path issues a Notion content write: the fixed call sites are search, page fetch, block-child fetch, and database query (`src/app/api/pilot/route.ts:186-200`, `src/lib/pilot/notion.ts:115-180`). The POST calls are Notion read/query endpoints; there is no PATCH, PUT, or page/block creation/update endpoint. Direct authenticated reads of `pilot_connections` are denied by the migration and covered by `tests/pilot.test.ts:126-127`.
