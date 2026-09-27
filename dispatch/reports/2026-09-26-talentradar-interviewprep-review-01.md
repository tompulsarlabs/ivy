# Report — 2026-09-26-talentradar-interviewprep-review-01

Produced by the workhorse/openai lane, 9.0 wall-minutes.

# PR #5 review — automatic interview preparation

**Decision:** changes requested. Reviewed PR head `7f1262c` read-only; no tests were executed.

PR-body corroboration was fetched with the required cross-repository pull-request search query containing `repo:tompulsarlabs/talent-radar`. The body states that this is a “persistent, leased workflow”, that “Private tracker notes stay outside public search and interviewer context”, that “Notion writes preserve user edits and reconcile interrupted requests”, and that it is “**Not deployed or activated**.”

## 1. Leasing/locking correctness — PARTIAL

The database lease is real, not advisory. The migration serialises observations per owner with `FOR UPDATE`, has a partial unique index for one current preparation, claims work with `FOR UPDATE … SKIP LOCKED`, and assigns a token plus six-minute lease: `supabase/migrations/20260925180000_automatic_interview_preparation.sql:38,43-69,71-82`. Worker checkpoints require the current row, matching token, and unexpired lease; practice creation repeats those checks under a row lock: `src/domain/interview-preparation/worker.ts:25-31`; `supabase/migrations/20260925180000_automatic_interview_preparation.sql:84-97`. Backfill adoption also uses conditional current/state/unleased predicates: `scripts/adopt-preparation.ts:14-27`.

That prevents normal concurrent workers from persisting two Radar revisions or practices for one source revision. It does not fully fence external Notion effects. `publishBrief` validates the lease, then waits and issues the external request: `src/domain/interview-preparation/publish.ts:47-50`. An observation can cancel the old revision and clear its token during that interval: `supabase/migrations/20260925180000_automatic_interview_preparation.sql:55-56`. The stale worker can therefore still create or append externally before its later checkpoint fails; page identity is only saved after creation: `src/domain/interview-preparation/publish.ts:66-82`. A newer revision can then publish its own page, leaving an orphaned competing external pack.

The PR-body claim “Previously prepared interviews can be adopted before backfill to avoid competing packs” holds for the guarded database adoption path, but not for this source-change/lease-expiry external-write race. Renew or hold the lease across each external mutation and make stale publication recovery explicit.

## 2. Private/public boundary — PASS, scoped to `roundContext`

The designated private free-text field is projected structurally, not hidden only in UI. Notion `Interview context`/`Next Action` map to `roundContext`: `src/domain/interview-preparation/observe.ts:21-25`. Public research receives an allowlisted object containing company, role, interviewer, stage, and job URL—not `roundContext`: `src/domain/interview-preparation/worker.ts:39-44`. The saved voice setup likewise omits it: `src/domain/interview-preparation/worker.ts:95-99`; the realtime request serialises only that setup: `src/app/api/interview/call/route.ts:27-30`; `src/lib/interview/prompts.ts:18-20`. The source test specifically checks that the private canary is absent from research arguments and saved setup: `tests/preparation-worker.test.ts:12-13,23-26,34-38`.

The scope matters. `roundContext` remains inside the shared `input jsonb` field, not a separate private column/table: `supabase/migrations/20260925180000_automatic_interview_preparation.sql:16`; it is intentionally passed to the private brief generator: `src/domain/interview-preparation/worker.ts:65-83`. The table is server-only, which is a useful structural access boundary: `supabase/migrations/20260925180000_automatic_interview_preparation.sql:99-104`. Do not generalise this guarantee to arbitrary text entered into `round` or `interviewer`, which have different downstream paths.

## 3. Notion reconciliation — PARTIAL

The no-overwrite property is sound. Publication reads existing blocks, refuses a type/text mismatch, appends rather than replaces, and performs a final readback: `src/domain/interview-preparation/publish.ts:23-41`. The tests cover a sequential lost-acknowledgement retry and an edit already present when retry begins: `tests/preparation-publication.test.ts:26-44`.

A genuine concurrent edit/retry conflict is not atomically reconciled. There is no Notion conditional-write/version mechanism in `notionRequest`: `src/lib/pilot/notion.ts:76-100`. `ensureBlocks` relies on one stale initial snapshot, can append blocks, and only then detects an in-place human edit during final verification: `src/domain/interview-preparation/publish.ts:24-41`. The human content is not overwritten, but prior appends remain and subsequent retries continue to fail until manual intervention. The final check also validates only the wanted prefix, so concurrent appenders can leave duplicate trailing generated blocks without detection.

Thus the PR-body statement “Notion writes preserve user edits and reconcile interrupted requests” is accurate for sequential interruption and fail-closed edit protection, but too broad for a true concurrent conflict. Add publisher-level idempotency/serialisation and a conflict state that records partial publication rather than treating it as reconciled.

## 4. Release boundary — FAIL as an enforceable gate

The migration is additive: it creates new tables, indexes, and functions rather than altering existing records: `supabase/migrations/20260925180000_automatic_interview_preparation.sql:3-105`. The cron route also fails closed when `CRON_SECRET` is absent or wrong: `src/app/api/preparation/worker/route.ts:9-15`; `tests/preparation-api.test.ts:17-20`.

But there is no preparation-specific disabled-by-default gate. The migration itself says “Interview preparation is on by default”: `supabase/migrations/20260925180000_automatic_interview_preparation.sql:1-2`. The change unconditionally adds Vercel schedules every minute and every five minutes: `vercel.json:16-21`, and discovery processes enabled members: `src/app/api/preparation/worker/route.ts:19-26`. Notion setup is not a generation gate: without a connection/destination, the worker still creates the Radar brief/practice and merely marks publication blocked: `src/domain/interview-preparation/worker.ts:105-110`. An authenticated manual check also synchronises and starts preparation without `CRON_SECRET`: `src/app/api/preparation/route.ts:26-47`.

The PR body says: “Apply the additive migration, configure/connect Radar's own Notion integration, select a private destination, adopt existing packs and activate the scheduled worker.” Those are operational steps, not enforced prerequisites. Adoption is manual, while discovery backfills active interviews automatically: `scripts/adopt-preparation.ts:1-29`; `src/domain/interview-preparation/observe.ts:70-75`. The current “not deployed or activated” status is corroborated by the PR body, but static review cannot confirm deployed configuration. Add an explicit default-off preparation feature flag enforced by cron, manual check, pipeline hooks, and worker claim before relying on the stated release boundary.
