# Report — 2026-09-26-talentradar-personalworkspace-review-01

Produced by the workhorse/openai lane, 6.6 wall-minutes.

# PR #6 review — 2026-09-26-talentradar-personalworkspace-review-01

Reviewed PR #6 head `f6b0781ff1d9d01b0336a01a89012c3cb540d78d`, stacked on #5. PR body was fetched using `search_pull_requests` with `repo:tompulsarlabs/talent-radar is:pr 6`.

## Outcome

Changes requested: the Google-identity claim fails at the new route, and preview-only flag scope is not independently provable from the diff. Profile extraction and the stated workspace-response privacy boundary pass.

### 1. Voice-intake gating — FAIL (Google); PASS (enabled membership)

PR body: “Existing Google sign-in and beta admission remain required; recording starts only after a tap.”

`/api/intake/voice` calls shared `authenticate()` before reads or spending ([src/app/api/intake/voice/route.ts:33] and [src/app/api/intake/voice/route.ts:44]). That helper validates a bearer token and requires an enabled `pilot_members` row ([src/lib/pilot/server.ts:28]–[51]), so anonymous and non-member access is blocked.

However, neither the route nor `authenticate()` checks a verified Google identity. The existing admission route does ([src/app/api/beta/admission/route.ts:34]–[38]), as does the existing voice-practice gate ([src/lib/interview/server.ts:16]–[28]); the intake route does not use that gate. The ordinary workspace also offers an email-OTP sign-in path ([src/components/Pilot.tsx:456]–[484]). An enabled non-Google member can therefore call the new route directly.

Add the same verified-Google check to the route/shared guard and add a regression test for an enabled member whose only identity provider is email.

### 2. Profile extraction — PASS

PR body: “Profile extraction preserves corrections and uncertainty and does not confirm the profile or start matching.”

Voice finish generates a draft and saves it only under `intake/current`; it does not write `profile/current` or enqueue work ([src/app/api/intake/voice/route.ts:93]–[106]). Confirmation is a separate explicit `action: "profile"` request ([src/app/api/pilot/route.ts:56]–[62], [src/app/api/pilot/route.ts:313]–[328]). Matching/research/prepare enqueue only after `profile.payload.confirmed === true` ([src/app/api/pilot/route.ts:668]–[679]); the UI submits that confirmation only from the “Confirm profile” form ([src/components/Pilot.tsx:922]–[998]).

Source tests cover unconfirmed drafts ([tests/intake-voice.test.ts:64]–[70]); they were inspected, not executed. An unrelated scheduler can still process an already-confirmed pre-existing profile, but extraction neither confirms nor alters it.

### 3. Provider call IDs off the workspace response — PASS, narrowly

PR body: “Selected documents only; provider call IDs stay off the public workspace response.”

The call ID is retained server-side for cleanup ([src/app/api/intake/voice/route.ts:54]–[59], [src/app/api/intake/voice/route.ts:73]–[76]). `publicIntakeVoice()` returns only `sessionId`, `status`, `transcript`, and `revision`, omitting `callId` ([src/lib/intake/voice.ts:26]–[29]); every intake-voice response uses that projection ([src/app/api/intake/voice/route.ts:78], [src/app/api/intake/voice/route.ts:89], [src/app/api/intake/voice/route.ts:106]). The aggregate workspace endpoint additionally excludes the raw `intake/voice-current` row ([src/app/api/pilot/route.ts:292]–[303]).

Caveat: this is true for the stated workspace/API response. The raw row still contains the ID for cleanup, and existing RLS permits an admitted owner to read their own `pilot_records` ([supabase/migrations/20260906120000_executive_pilot.sql:109]–[115]). It is not a guarantee that the value is absent from every owner-readable data path.

### 4. `INTAKE_VOICE_ENABLED` preview scope — NOT INDEPENDENTLY CONFIRMED

PR body: “`INTAKE_VOICE_ENABLED` is enabled only for this branch preview. Production, interview voice activation and automatic interview-preparation activation are unchanged.”

The source defaults fail-closed: `.env.example` sets `INTAKE_VOICE_ENABLED=false` ([.env.example:62]–[63]), and the route requires the exact string `true` for start ([src/app/api/intake/voice/route.ts:48]). But the implementation has no branch, preview, or deployment-environment predicate; it reads only the process-wide variable ([src/app/api/intake/voice/route.ts:38], [src/app/api/intake/voice/route.ts:48]).

`docs/HANDOFF.md` asserts that the value is configured only for Preview branch `codex/naboo-first-meeting` ([docs/HANDOFF.md:37]), but that is not independently verifiable deployment evidence. If the variable is enabled in Production or all Preview environments, every admitted member receives voice intake after merge.

Before approval, verify in deployment settings that the variable is set only for this branch preview and absent/false in Production and other Preview scopes.

## Verification limits

This was a read-only static review of the current PR head and fetched PR body. No PR worktree tests were executed or claimed as passing.
