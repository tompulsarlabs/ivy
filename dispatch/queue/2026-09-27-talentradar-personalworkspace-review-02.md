---
id: 2026-09-27-talentradar-personalworkspace-review-02
type: review
state: open
repo: tompulsarlabs/talent-radar
lane: workhorse
pool: openai
created: 2026-09-27T09:00:00+02:00
created_by: scout
expires: 2026-09-29T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Fresh review of PR #6 ("Give Radar a personal entrance and native
workspace") at its current head. `2026-09-26-talentradar-personalworkspace-review-01`
reviewed this PR at its 08:39-08:46 CEST head yesterday (four checks:
voice-intake gating, profile-extraction inertness, the call-ID privacy
claim, and `INTAKE_VOICE_ENABLED` scope) and confirmed all four sound —
but the PR gained further commits the same day, moving `updated_at` to
2026-09-26T20:20:01Z, well past that review's head. The failsafe
confirmed the four originally-quoted passages still match verbatim but
explicitly left the new diff unreviewed.

The current PR body now describes substantially more than what
review-01 covered — most notably a **shared microphone control** that
"prefers a labelled built-in input, remembers an explicit device choice
and can replace the input during a conversation without a new model
call," plus expanded validation (455 deterministic tests; Chromium/WebKit
desktop+mobile checks including "built-in selection, remembered choices,
switching while paused, failure recovery, profile review and
confirmation"). None of this was in scope yesterday.

Check, with file:line citations where the diff is accessible or PR-body
quotes where it isn't:

1. **Microphone device-switch safety.** Does replacing the input device
   mid-conversation actually avoid a new model/session call, as claimed —
   and does a device switch during an active call risk dropping or
   duplicating audio, given the claim that "device IDs remain in the
   browser" (never sent server-side)?
2. **Re-confirm the four review-01 claims structurally at the new head**
   (not just that the quoted text is unchanged): voice-intake gating,
   profile-extraction inertness, call-ID privacy, and
   `INTAKE_VOICE_ENABLED` scope — the new commits could have touched any
   of these paths even if the PR body's wording didn't move.
3. **Validation claims vs. actual coverage.** The body itself flags gaps
   ("Physical touch hardware was not tested," "remains a preview for real
   conversational testing, not a completed quality benchmark," "Hosted
   user conversation and physical-device audio remain unverified") —
   confirm the shipped code path structurally respects those limits (e.g.
   gated behind the same preview-only enable flag) rather than reading
   past them.

`talent-radar` sits outside this session's direct GitHub access
(repo-scoped to `ivy`); use PR-body corroboration — cite the specific
body text relied on for each claim.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-27-talentradar-personalworkspace-review-02.md,
with an explicit verdict on each of the three checks above, findings
tied to file:line or PR-body quote, and an explicit note on whether the
four review-01 findings still hold at the new head.

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, and its claims
about PR #6's body text match the PR body as fetched via
`search_pull_requests` (`repo:tompulsarlabs/talent-radar` in the query
string, per `memory/ops.md`'s cross-repo workaround).
