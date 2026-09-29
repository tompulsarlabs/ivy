---
subject: tompulsarlabs/talent-radar
type: repo
updated: 2026-09-29
---

# talent-radar

**Private.** First seen in the 2026-08-26 watchlist sync, created the day
before [cite:2026-08-26]. Dormant from the 2026-08-25 scaffold until PR #1
opened 2026-09-03 — then became a substantial feature build, merged
2026-09-24 (21 days open) [cite:2026-09-24].

## PR #1 and PR #2 merged, 2026-09-24

Both landed the same day, same merge-commit timestamp (17:24 CEST), each
preserving its branch's individual commits rather than squashing — which
is why `search_commits` also surfaces a run of `talent-radar` docs/feat
commits timestamped hours earlier (10:53–13:19 CEST): authored on the
branch, only default-branch-reachable once the merge landed.

- **PR #1** (opened 09-03) — the Session 1 Supabase fetch layer, live with
  38 boards / 4,271 postings polled, plus the read-only Radar UI. Reviewed
  once, 09-05 ([[models]]).
- **PR #2** (opened 09-06) — the private executive beta: confirmed intake,
  company-fit research, outreach drafts, interview practice. Reviewed
  twice (09-17, 09-23) with one finding surviving both cycles — see
  below.

A new PR #4 opened same evening (19:19 CEST, still open at the 22:30
failsafe) records the beta's production promotion.

## PR #4 — reviewed, then rewritten past the review, 2026-09-25

`2026-09-25-talentradar-productionpromo-review-01` reviewed PR #4 at head
`6534feec` (title then "Record Radar production promotion and remaining
beta gates"): the promotion record does **not** acknowledge the still-open
CSV-dedupe P1 (`src/lib/market/import.ts:44`, unfixed across two prior
review cycles [cite:2026-09-23]), and the stated "remaining beta gates"
list omits the documented-but-unreachable row-level CSV provider fallback
(`docs/MARKET-DATA.md:7` vs `src/app/api/pilot/market/route.ts:5`).
**Same day, after the review ran**, PR #4's title and body were both
replaced wholesale — now "Recover expired Google sign-ins and record
production verification," a live sign-in bug fix that mentions the
promotion record only in passing (`updated_at` moved to
2026-09-25T16:35:40Z, well past the review's 08:16:58Z finish). The
failsafe could not confirm the reviewed findings still describe the
PR's current content and stamped the contract **unverified**
[cite:2026-09-25] — the third time this repo's fast-moving PRs have
outrun a same-day review (see PR #3, 2026-09-08, below). The CSV-dedupe
P1 itself is unaffected either way — it lives in `main`, not this PR, and
stays open regardless of what PR #4 says.

Two more PRs opened later the same evening, both draft, both stacked:
**PR #5** ("Prepare interviews automatically when the pipeline reaches
Interviewing," 19:15:57 CEST) — explicitly **not deployed or activated**
per its own body, stacked on PR #4. **PR #6** ("Make Radar personal and
native, with optional Notion," 19:46:39 CEST) [cite:2026-09-25].

As with [[repos/countersign]], private status means a green day resting on
this repo alone is not independently confirmable — it depends on the profile's
"private contributions" toggle. Public repos have carried the confirmation on
every recorded day [[patterns]].

## Activity

`4633ba0`, 2026-08-25 14:05:57 — "chore: scaffold Talent Radar repo,"
correctly attributed to the connected address [cite:2026-08-25]. Clean tree,
0 unpushed commits on the 2026-08-26 scan [cite:2026-08-26]; no further
activity until PR #1.

**PR #1** ("Restore Cowork history, build the Session 1 fetch layer, take it
live on Supabase, and add the Radar UI"), opened 2026-09-03, still open and
drafting as of 2026-09-05: a `talent_radar` Postgres schema (7 tables) live
on Supabase, a Greenhouse/Lever/Ashby polling layer behind one interface
(`fetch-jobs` fired by pg_cron), a read-only Radar UI, 126 vitest tests, and
CI wired to gstack. First full poll run completed clean (38 boards, 4,271
postings, 0 board errors) per the PR body [cite:2026-09-05]. Reviewed
2026-09-05 by `2026-09-05-talentradar-review-01` (verified done) [[models]].

## Verification note

PR #1's files exist only on its own branch, not `main` — `search_code`
(cross-repo, default-branch only) cannot confirm them directly; the PR's
own body text is the fallback corroboration [[ops]]. This will resolve
itself the day the PR merges.

## PR #2 and #3 — a second and third unmerged draft, both stacked

**PR #2** ("Build the private executive opportunity and interview
pilot"), opened 2026-09-03: RLS, encrypted per-user Notion tokens,
server-side Astra Responses calls. Reviewed 2026-09-05 by
`2026-09-05-talentradar-review-01` (verified done, PR-body corroboration)
[[models]] [cite:2026-09-05].

**PR #3**, opened 2026-09-07, stacked on PR #2. Reviewed 2026-09-08 by
`2026-09-08-talentradar-voicepractice-review-01` at head `a8a4cf4`
(branch `codex/rad-interview-beta`), titled at review time "Add
configurable voice interview practice for invited users" — the report
found the Google-sign-in + allowlist gate sound, private notes correctly
excluded from model requests, and no code path promoting the beta beyond
its preview branch. **But the PR changed after the review completed**:
by the 22:30 failsafe pass the same day, its title had become "Connect
Sybil intake to private Radar and invited voice practice" and
`updated_at` had moved to 14:20 UTC — over three hours past the review's
10:56 CEST finish. The failsafe could not confirm the reviewed findings
still hold against whatever the new head actually contains (`talent-radar`
sits outside this session's direct repo access [[ops]]), so the contract
was left **unverified** rather than assumed carried-over [cite:2026-09-08].
**Open finding for the next scout/dispatch pass:** PR #3 needs a fresh
review contract against its current head before it can be treated as
verified-done.

**Resolved 2026-09-09:** `2026-09-09-talentradar-sybilintake-review-01`
reviewed PR #3 at its current head `23724a0`, unchanged since the
09-08T14:20:25Z drift (confirmed stable — no further scope change).
Six findings, three P1: the three-phase interview contract can be
bypassed by a forced-ready fallback at 25 turns
(`src/app/api/intake/route.ts:57`); client-controlled candidate/company
fields are interpolated directly into the system prompt that also holds
the hidden rubric, with no role/data boundary
(`src/lib/intake/sybil-prompts.ts:12-25`); and a shared-browser
account-switch can transiently leak one user's voice interview data to
another because in-flight requests aren't bound to an auth epoch
(`src/components/InterviewBeta.tsx:60-96`). Current-head CI is also red
(`tsc --noEmit` failures in `tests/sybil-intake.test.ts`). Confirmed
still sound: the Google-sign-in + allowlist voice gate, private-notes
exclusion, owner-scoped intake/upload state, and the PR's own
draft/no-merge claim [cite:2026-09-09] [[models]].

## PR #2 — fresh review at the 09-16 head (2026-09-17)

`updated_at` moved 2026-09-16 for the first time since the 09-05 review
(now titled "Build Radar's private executive beta with grounded interview
evaluation") — 33 intervening commits since the reviewed head `a7bf289`,
landing to tip `1395d45`: the executive pilot, knowledge/evidence and
grounded-evaluation paths, capped approval/admission, private funding CSV
import (09-11), then a workspace/Notion UI pass (09-16).
`2026-09-17-talentradar-execbeta-review-02` reviewed the new head. Two
real findings: **P2** — `src/lib/market/import.ts:44` de-dupes CSV funding
rows on `[domain, sourceUrl, eventDate]` only, so two undated rows from the
same company/provider URL with different round/amount/currency/investors
silently collapse to one, contradicting the "without merging different
rounds" intent in `tests/market-signals.test.ts:16`. **P3** —
`docs/BETA-READINESS.md` still presents a 10-September, present-tense 297
test count as current while the head's own validation record
(`docs/HANDOFF.md:21,31`) is 332. Confirmed sound: Google-OAuth admission
gating, atomic capacity-reservation locking, the fail-closed approval-
migration compatibility path, CSV provenance scoping (not a live
Crunchbase feed), the private evaluator's server-side criteria boundary,
and the 332-test count's internal consistency. Verified via PR-body
corroboration (`talent-radar` sits outside this session's direct repo
access [[ops]]) — same method as the 09-05 review [cite:2026-09-17]
[[models]].

## PR #2 — second fresh review at the 09-21 head (2026-09-23)

`updated_at` settled at 2026-09-21T16:51:46Z, two full days stable, and
the PR body's validation count moved again (332 → 338 tests) —
`2026-09-23-talentradar-execbeta-review-03` reviewed the new head
`520de91` (16 commits past the 09-17 head `1395d45`). The 09-17 review's
**P3 stale-test-count finding is resolved**: `docs/BETA-READINESS.md:17`
now correctly states 338. The 09-17 review's **P1 CSV-dedupe finding is
still open, unchanged**: `src/lib/market/import.ts:44` still de-dupes on
`[domain, sourceUrl, eventDate]` only, so same-company/provider rows
differing in round/amount/currency/investors still silently collapse — the
report re-flags it as P1 (upgraded from the 09-17 P2) since it has now
survived a second review cycle without a fix. New P3: `docs/MARKET-DATA.md`
documents a per-row CSV `provider` fallback that the API code makes
unreachable (`src/app/api/pilot/market/route.ts:5` requires a top-level
provider regardless). New surface since 09-17 — a "Known live now" feature
deriving confirmed target functions from the authenticated member's own
saved profile — confirmed read-only with no ranking or extra model call
(`src/app/api/pilot/route.ts:162-186`, `src/lib/pilot/job-search.ts:35-41`,
`src/lib/pilot/jobs.ts:5-41`). Also confirmed sound, unchanged from 09-17:
Google-entry admission gating, atomic capacity-reservation locking, the
fail-closed migration-compatibility path, and CSV provenance scoping.
Verified via PR-body corroboration (still outside this session's direct
repo access) [cite:2026-09-23] [[models]].

## PR #4, #5, #6 — three fresh reviews, 2026-09-26

`2026-09-26-talentradar-productionpromo-review-02` reviewed PR #4 at its
post-rewrite head `8a66eda` (Google sign-in recovery, not the old
documentation-only scope): the sign-in recovery fix itself passes source
review (no open-redirect path, callback cleanup sound), but the
**CSV-dedupe P1 is still unacknowledged** in the inherited promotion
claim this PR folds in — the same finding that has now survived three
review cycles (09-17, 09-23, and this one) without a fix
[cite:2026-09-26].

`2026-09-26-talentradar-interviewprep-review-01` reviewed PR #5 (first
review, "automatic interview preparation"): the database lease is real
(not advisory) and blocks normal concurrent workers, but does not fully
fence external Notion effects — a stale worker can still publish before
its lease-expiry checkpoint fails, leaving an orphaned competing page.
The private/public boundary (`roundContext`) is structurally sound.
Notion reconciliation handles sequential interruption but not a genuine
concurrent edit/retry conflict. The "not deployed or activated" release
claim does not hold as an enforceable gate: no preparation-specific
disabled-by-default flag exists, and Vercel cron schedules are added
unconditionally [cite:2026-09-26].

`2026-09-26-talentradar-personalworkspace-review-01` reviewed PR #6
(first review, "personal entrance and native workspace"): the new
voice-intake route requires an enabled member but does **not** check a
verified Google identity, unlike every other admission-gated route in
this repo — an enabled email-only member could reach it directly.
Profile-extraction and call-ID-privacy claims both pass. The
`INTAKE_VOICE_ENABLED` preview-only scope claim cannot be independently
confirmed from a static diff (no branch/environment predicate in code,
only a documented claim) [cite:2026-09-26].

## PR #7 — the CSV-dedupe fix, 2026-09-28, first `build` contract on this repo

`2026-09-28-talentradar-csvdedupe-build-01`, promoted under the 09-27
retro's 3-cycle rule off the P1 that survived four straight review cycles
unfixed (09-17, 09-23, 09-25, 09-26), shipped as draft PR #7 the same
morning it was queued (opened 15:01:04 CEST, ~5.5 wall-minutes). The
de-dupe key at `src/lib/market/import.ts:44` (now `:46`) widened from
`[domain, sourceUrl, eventDate]` to also include `round`, `amount`,
`currency`, `investors` — rows differing in any of those four no longer
collapse; rows matching on all seven still do. A new `tests/market-signals.test.ts`
case exercises exactly the scenario the four reviews found (verified red
before the fix, green after); `npm test`/`typecheck`/`lint` all clean. One
adjacent gap left deliberately unfixed and disclosed in the PR body:
undated rows with *blank* round/amount/currency/investors that differ only
in `announcementUrl` still collapse last-wins — the contract's own spec
defines those as genuine duplicates, so fixing it would have been scope
creep, not a bug fix. This closes the finding that had been the sole
evidence, per [[models]], of `build`'s idle stretch since 09-02
[cite:2026-09-28].

## PR #6 — second fresh review, 2026-09-28: paused-mic race

`2026-09-27-talentradar-personalworkspace-review-02` reviewed the head that
gained the shared-microphone control after review-01 (which had covered
only voice-intake gating, profile-extraction inertness, call-ID privacy,
and the `INTAKE_VOICE_ENABLED` scope — all four re-confirmed still sound at
this new head). **New medium finding**: `selectMicrophone()` enables the
replacement track and awaits `replaceTrack()` before reapplying paused
state, while `pause()` only disables the *current* stream reference — so a
Pause, Finish, or hidden-tab suspension landing mid-switch can leave the
replacement input briefly live despite the paused UI. The PR's own
paused-switch test resolves its replacement mock immediately, so it cannot
exercise this interleaving. Device-switch claims otherwise hold: no new
model/session call, no duplicate-sender path, device IDs stay out of the
intake request body (though RLS-scoped `SELECT` on `pilot_records` does let
an authenticated owner retrieve their own stored call ID via direct REST —
worth not describing IDs as flatly browser-inaccessible). Overall verdict:
request changes [cite:2026-09-28] [[models]].

## PR #7 — first review, 2026-09-29: verdict PASS, no findings

`2026-09-29-talentradar-csvdedupe-review-01` reviewed the fix itself
adversarially: the widened seven-part key at `src/lib/market/import.ts:46`
stops the four-review-confirmed collapse (distinct undated rows differing
in round/amount/currency, or in investors alone, both now survive) without
breaking genuine-duplicate collapsing on rows matching all seven fields.
The extended `tests/market-signals.test.ts:16` case is a genuine
regression test, not a happy-path assertion. Missing-field normalisation,
JSON-key serialization, and investor whitespace/case handling all checked
sound. The disclosed `announcementUrl`-only gap is confirmed correctly
scoped as out-of-spec rather than a missed instance of the original bug.
This closes the loop this page has tracked since 09-17: a finding that
survived four review cycles unfixed is now independently confirmed fixed,
not just shipped [cite:2026-09-29] [[models]].

## Changelog

- 2026-09-29 (failsafe) — recorded PR #7's first review: verdict PASS, no
  findings, closing the CSV-dedupe finding this page has tracked since
  09-17 (four review cycles unfixed, one `build` contract, now one clean
  review). Nudged to merge; unconverted by 22:30. Verified per its
  Verification section tonight.
- 2026-09-28 (failsafe) — recorded PR #7, the first `build` contract on
  this repo, closing the CSV-dedupe P1 that had survived four straight
  review cycles unfixed; this is today's green-by signal. Recorded PR #6's
  second review: a new medium paused-mic race finding on the shared
  microphone control, the four review-01 claims re-confirmed sound. Both
  contracts verified per their Verification sections tonight.
- 2026-09-27 (retro) — the CSV-dedupe P1 (`src/lib/market/import.ts:44`)
  is this retro's evidence for a `playbook.md` change: having survived
  four review cycles unfixed (09-17, 09-23, 09-25, 09-26) with `build`
  otherwise idle since 09-02, a finding unfixed past 3 review cycles now
  promotes directly to a `build` contract instead of a fifth review
  [[models]]. This finding is the trigger case; tomorrow's scout is where
  the resulting contract should first appear.
- 2026-09-26 (failsafe) — recorded three fresh reviews: PR #4's rewritten
  scope (sign-in fix passes, inherited CSV-dedupe P1 still unacknowledged
  — now three review cycles unfixed), PR #5's first review (lease sound
  for normal concurrency but not external Notion races; release-boundary
  claim unenforced), PR #6's first review (missing verified-Google check
  on the new voice-intake route; preview-flag scope unconfirmable
  statically). All three verified per their Verification sections
  tonight.
- 2026-09-25 (failsafe) — recorded PR #4 reviewed then rewritten past the
  review same day (review found the CSV-dedupe P1 unacknowledged and the
  beta-gates list incomplete; PR then retitled/rebodied to a Google-sign-in
  fix, contract left unverified); recorded PR #5 and PR #6 opened, both
  draft, both stacked on PR #4.
- 2026-09-24 (failsafe) — recorded PR #1 and PR #2 both merged 17:24 CEST
  (21 and 18 days open respectively), and a new PR #4 opened same evening
  recording the beta's production promotion. The 09-23 P1 CSV-dedupe
  finding was not re-verified against the merged head tonight — carries
  forward as open until a fresh review runs against `main`.
- 2026-09-23 (failsafe) — recorded the second PR #2 fresh review at its
  09-21 head: resolved the 09-17 stale-test-count finding, re-confirmed
  the CSV-dedupe finding (now P1, unfixed across two review cycles), found
  one new P3 (unreachable provider fallback), and confirmed the new
  "Known live now" feature is read-only as described.
- 2026-09-17 (failsafe) — recorded the PR #2 fresh review at its 09-16
  head: two real findings (CSV-dedup gap, stale test-count doc) plus five
  sound confirmations, verified via PR-body corroboration.
- 2026-09-09 — recorded the fresh PR #3 review (three P1 findings: phase
  bypass, prompt injection via unescaped fields, cross-account voice
  leak; plus a red-CI finding), resolving the 09-08 unverified-drift gap.
- 2026-09-08 — recorded PR #3's post-review title/scope drift and the
  resulting unverified contract; added the PR #2 review pointer.
- 2026-09-05 — rewritten: dormant-scaffold framing replaced with the real
  PR #1 build (Supabase fetch layer, Radar UI, CI); recorded the
  search_code verification gap while PR #1 stays unmerged.
- 2026-08-27 — page created from journals 2026-08-25→26 and `state.json`.
