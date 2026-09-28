# Report — 2026-09-27-talentradar-personalworkspace-review-02

Produced by the workhorse/openai lane, 8.9 wall-minutes.

# PR #6 fresh review

Reviewed current head `38f2c0678d7cff025464dd5454274c5b58132509`. PR body was fetched with `repo:tompulsarlabs/talent-radar is:pr`.

**Overall verdict: request changes.** The four review-01 claims still hold at the new head within their stated scope, but the shared microphone switch has a pause/stop race that can briefly leave a replacement input live.

## Finding — medium: an in-flight switch can violate the paused-mic invariant

`selectMicrophone()` enables the replacement track, awaits `sender.replaceTrack()`, then only reapplies paused state afterwards (`src/lib/interview/voice-client.ts:117-135`). `pause()` disables only `this.stream`, which is still the old stream until the replacement is assigned (`src/lib/interview/voice-client.ts:152-158`).

So if Pause, Finish, or hidden-tab suspension occurs while `replaceTrack()` is pending, the new sender track may be live briefly despite the paused UI. This affects both intake and interview practice because they share `InterviewCall`; the intake Pause control remains usable while the picker is busy (`src/components/IntakeVoice.tsx:146`), and hidden tabs call `pause()` (`src/components/IntakeVoice.tsx:52-56`).

The claimed paused-switch test pauses before selection (`tests/microphone.test.ts:77-80`); its replacement mock resolves immediately, so it cannot exercise this interleaving. Track pending replacement explicitly and mute/stop it from `pause()`, `stopMicrophone()`, and `close()`; add a deferred-`replaceTrack` race test.

## 1. Microphone device-switch safety — partial / not safe to sign off

- **No new model/session call: confirmed.** Switching uses browser capture plus `RTCRtpSender.replaceTrack()` and has no exchange callback or model request (`src/lib/interview/voice-client.ts:117-143`). The only intake SDP exchange is initial connection (`src/components/IntakeVoice.tsx:89-98`), and the deterministic test asserts one exchange after a switch (`tests/microphone.test.ts:71-76`).
- **No duplicate sender path: confirmed structurally.** The old stream stops only after the sole sender accepts the replacement (`src/lib/interview/voice-client.ts:123-135`). Failed replacement retains the old mic and stops the attempted stream (`tests/microphone.test.ts:81-86`).
- **No-loss active hand-off: unverified.** There is no drain, acknowledgement, or physical-device test around the swap. The code does not establish gap-free audio.
- **Device-ID privacy: confirmed at application level.** IDs are used in browser enumeration, `getUserMedia`, and localStorage (`src/lib/interview/microphone.ts:4-18,26-45`), not the intake request body (`src/components/IntakeVoice.tsx:25-30,89-98`). This does not prove what a browser/WebRTC implementation may expose on the wire.

Relevant PR-body claim: “The shared microphone control … can replace the input during a conversation without a new model call. Device IDs remain in the browser.” The first sentence holds; the latter holds for application serialisation; muted-switch safety does not.

## 2. Review-01 claims at the new head — still hold, with stated caveats

- **Voice-intake gating: pass for new Realtime calls.** The route authenticates, then rejects `start` unless `INTAKE_VOICE_ENABLED === 'true'` and a server API key exist, before budget/provider work (`src/app/api/intake/voice/route.ts:44-71`). The client refuses unavailable starts (`src/components/IntakeVoice.tsx:68-70`). Invited membership is also required (`src/lib/pilot/server.ts:28-51`).

  Caveat: existing `sync`/`stop`/`finish` paths remain available for recovery; `finish` can run profile extraction after the flag is disabled (`src/app/api/intake/voice/route.ts:80-106`), though it cannot create a new WebRTC call.

- **Profile-extraction inertness: pass.** Finish hangs up before generation and saves only `intake/current` with a draft; it neither writes `profile/current` nor sets confirmation (`src/app/api/intake/voice/route.ts:84-106`). The test asserts confirmation remains absent (`tests/intake-voice.test.ts:64-71`). Research/matching requires an explicitly confirmed profile (`src/app/api/pilot/route.ts:668-679`).

- **Call-ID privacy: pass for the PR’s narrow wording.** `publicIntakeVoice()` omits `callId` (`src/lib/intake/voice.ts:26-30`), and `/api/pilot` excludes the `voice-current` record (`src/app/api/pilot/route.ts:292-303`). The start-response test also excludes the provider ID (`tests/intake-voice.test.ts:35-42`).

  Do not describe IDs as browser-inaccessible: authenticated owners have RLS-scoped `SELECT` on `pilot_records` (`supabase/migrations/20260906120000_executive_pilot.sql:101-115`). If `talent_radar` is REST-exposed, an owner could directly retrieve their own stored ID. This does not invalidate “stay off the public workspace response.”

- **`INTAKE_VOICE_ENABLED` scope: pass.** Current runtime use is confined to the intake voice route (`src/app/api/intake/voice/route.ts:38,48`) and defaults false (`.env.example:62-63`). Interview voice remains separately gated by `VOICE_ENABLED` (`src/lib/interview/server.ts:11-13`).

Relevant PR-body corroboration: “Profile extraction … does not confirm the profile or start matching”; “provider call IDs stay off the public workspace response”; and “`INTAKE_VOICE_ENABLED` is enabled only for this branch preview. Production, interview voice activation and automatic interview-preparation activation are unchanged.”

## 3. Validation claims versus actual coverage — partial

Current-head CI run 240 passed: 58 test files / 455 tests, typecheck, lint, and build. That corroborates the PR-body claim, “455 deterministic tests, typecheck, lint and production build pass.”

The deterministic tests substantiate mocked mechanics: built-in selection, one exchange, failed replacement, late-grant cleanup, and disconnected-input pause (`tests/microphone.test.ts:71-100`). They do not cover the pause-during-replacement race above.

The PR body accurately limits broader claims:

> “Eleven microphone/flow UI checks also pass, including … switching while paused…”

> “No physical microphone or private user content was used. Hosted user conversation and physical-device audio remain unverified.”

> “This remains a preview for real conversational testing, not a completed quality benchmark.”

The new-call path is structurally preview-gated, so the code does not silently activate intake, interview voice, or preparation. However, its stated paused-switch validation is insufficient for the actual concurrent switch path, and the post-disable recovery/model-work policy should be explicitly tested.

No files were modified.
