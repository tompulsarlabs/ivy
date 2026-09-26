---
id: 2026-09-26-talentradar-personalworkspace-review-01
type: review
state: claimed
claimed_at: 2026-09-26T10:39:53+02:00
repo: tompulsarlabs/talent-radar
lane: workhorse
pool: openai
created: 2026-09-26T09:00:00+02:00
created_by: scout
expires: 2026-09-28T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

First review of PR #6 ("Give Radar a personal entrance and native
workspace"), opened 2026-09-25T17:46:39Z, draft, stacked on PR #5 —
pushed again this morning (updated 2026-09-26T05:00:19Z), the freshest
activity in the org. No prior contract has reviewed this PR.

Per the PR body: a new welcome flow ("Let's talk" / "Type instead")
starts a spoken career conversation over the existing WebRTC voice client
via a new authenticated route, gated behind a separate enable flag
(`INTAKE_VOICE_ENABLED`, "enabled only for this branch preview"). A
native workspace (saved briefs, research, evidence, coaching) is added
with optional Notion import/export; Tom's existing tracker "remains
canonical." Profile extraction is claimed to preserve corrections and
uncertainty "and does not confirm the profile or start matching."
Microphone handling and device IDs are claimed to stay in-browser;
"provider call IDs stay off the public workspace response."

Check, with file:line citations where the diff is accessible or PR-body
quotes where it isn't:

1. **Voice-intake gating.** Does the new authenticated route genuinely
   require the existing Google sign-in and beta admission, as claimed
   ("Existing Google sign-in and beta admission remain required")? A
   new route is exactly where an admission check is easiest to
   accidentally skip.
2. **Profile-extraction claim.** Verify "does not confirm the profile or
   start matching" — i.e. that extraction is genuinely inert until an
   explicit user action, not auto-triggering downstream matching.
3. **Privacy claim.** "Provider call IDs stay off the public workspace
   response" — a specific, checkable claim; confirm it rather than
   accept it.
4. **Feature-flag scope.** Confirm `INTAKE_VOICE_ENABLED` is actually
   scoped to this branch/preview as claimed, not a global default that
   would activate for all users on merge.

`talent-radar` sits outside this session's direct GitHub access
(repo-scoped to `ivy`); use PR-body corroboration — cite the specific
body text relied on for each claim.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-26-talentradar-personalworkspace-review-01.md,
with an explicit verdict on each of the four checks above, findings tied
to file:line or PR-body quote.

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, and its claims
about PR #6's body text match the PR body as fetched via
`search_pull_requests` (`repo:tompulsarlabs/talent-radar` in the query
string, per `memory/ops.md`'s cross-repo workaround).
