---
subject: tompulsarlabs/talent-radar
type: repo
updated: 2026-09-09
---

# talent-radar

**Private.** First seen in the 2026-08-26 watchlist sync, created the day
before [cite:2026-08-26]. Dormant from the 2026-08-25 scaffold until PR #1
opened 2026-09-03 — then became a substantial, still-unmerged feature
build.

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

## Changelog

- 2026-09-09 — recorded the fresh PR #3 review (three P1 findings: phase
  bypass, prompt injection via unescaped fields, cross-account voice
  leak; plus a red-CI finding), resolving the 09-08 unverified-drift gap.
- 2026-09-08 — recorded PR #3's post-review title/scope drift and the
  resulting unverified contract; added the PR #2 review pointer.
- 2026-09-05 — rewritten: dormant-scaffold framing replaced with the real
  PR #1 build (Supabase fetch layer, Radar UI, CI); recorded the
  search_code verification gap while PR #1 stays unmerged.
- 2026-08-27 — page created from journals 2026-08-25→26 and `state.json`.
