# Report — 2026-09-09-talentradar-sybilintake-review-01

Produced by the workhorse/openai lane, 23.2 wall-minutes.

# PR #3 adversarial review

Reviewed current head `23724a0bfc2b2610538516d8e563947d714aa7fc` read-only.

## Findings

### P1 — The three-phase contract can be bypassed

`src/app/api/intake/route.ts:57` marks the conversation ready after 25 user turns even without `[ASSESSMENT_COMPLETE]`; `:60-64` then permits rubric scoring. This contradicts the required natural Phase-3 completion in `src/lib/intake/sybil-prompts.ts:57-62,104-105`.

Fix: remove the forced-ready fallback. Persist and validate phase/coverage server-side, require a completion signal after Phase 3, and add a no-marker-at-25-turns regression test.

### P1 — Candidate input is interpolated into the system prompt containing the hidden rubric

Client-controlled `user` and `company` fields are accepted at `src/app/api/intake/route.ts:10-11,44-49` and inserted directly into the system prompt at `src/lib/intake/sybil-prompts.ts:12-25`. Conversation content is likewise interpolated into the assessment prompt at `:115-125`. The untrusted-data reminder is appended later in `src/lib/intake/service.ts:11,20-24`, not enforced as a role/data boundary.

A malicious name, summary, company field, or answer can therefore compete with instructions in the same prompt that contains the rubric.

Fix: keep system instructions/rubric static; send candidate, company, and transcript data as structured untrusted input. Add prompt-injection tests using profile fields and transcript content that attempt rubric extraction.

### P2 — “Confirm extracted context” does not permit confirmation of all extracted context

`src/components/SybilIntake.tsx:54-58` only edits five scalar fields. Extracted experience, skills, and education are shown as a read-only `<pre>` at `:56`, yet skills and experience enter the assessment prompt at `src/lib/intake/sybil-prompts.ts:16-17`.

Fix: provide structured edit/remove controls or a re-extraction flow for every extracted field, save a confirmed-context revision, and test that corrections reach the interview prompt.

### P2 — Company research can be attached to a different confirmed company

`src/app/api/intake/route.ts:39-43` researches and saves context for submitted `a.user`; `:44-49` later accepts independently supplied `a.user` and `a.company` when starting the interview. The UI permits editing both independently at `src/components/SybilIntake.tsx:55,58`. Research for company A can therefore be retained while the candidate profile says company B.

Fix: persist a normalized researched-for company and source revision; clear/research company context on identity change, or reject/require explicit confirmation of a mismatch server-side.

### P1 — Voice responses can leak locally after an account switch

`src/components/InterviewBeta.tsx:60-71` clears local state on auth change, but requests at `:88-96` are not bound to the initiating owner. Delayed list/create/debrief responses can still be applied at `:108-114,169-195,197-218`. Since the list endpoint returns full payloads (`src/app/api/interview/route.ts:24-27`) and selected sessions copy transcript/notes into UI (`src/components/InterviewBeta.tsx:102-105`), a shared browser can transiently expose Alice’s voice data to Bob.

Fix: increment an auth epoch synchronously on every identity change; capture owner/epoch per request; abort or discard stale responses; reset queued work. Add delayed two-account browser tests for list, create, save, call, and debrief responses.

### P2 — Confirmed Radar context does not reach invited voice practice

The Radar Google redirect is callback-only (`src/components/Pilot.tsx:395-397`; `src/components/InterviewBeta.tsx:78-86`). Voice starts from `emptySetup` and only fills a Google display name (`src/components/InterviewBeta.tsx:12,108-114`); `/api/interview` saves browser-supplied setup (`src/app/api/interview/route.ts:34-39`) and the Realtime call uses that setup (`src/app/api/interview/call/route.ts:20-27`).

The broad interview-practice claim is true for Radar text practice, not `/interview` voice practice.

Fix: add an owner-authenticated Radar-to-voice bootstrap that snapshots explicitly shareable confirmed-profile and selected-opportunity fields server-side, or narrow the PR/documentation claim to text practice.

### P1 — Current-head CI is red

GitHub Actions runs `34237555287` and `34237562665` both fail on head `23724a0`. All 214 Vitest tests pass, then `tsc --noEmit` fails at `tests/sybil-intake.test.ts:15-21` for possibly undefined responses and `:23` for an incompatible partial `Capability` cast. Lint and Actions build do not run after typecheck fails.

`src/app/api/intake/route.ts:66-72` also has no terminal return after the action chain, contributing to `POST` being inferred as possibly undefined.

Fix: make the action switch exhaustive with a terminal error/return, use explicit non-null test results, construct a complete typed capability fixture, then rerun the full CI workflow.

## Confirmations

- The relevant Sybil assessment/profile prompt bodies and all 25 rubric entries match source commit `032f756`. `src/lib/intake/sybil-prompts.ts:1`, `src/lib/intake/sybil-rubric.ts:1`, and `src/lib/intake/service.ts:1` are server-only, and the browser intake component imports only types. This is a structural bundle boundary, not protection against the prompt-injection finding above.

- The main Radar text path is owner-scoped and uses an explicitly confirmed profile: `src/components/SybilIntake.tsx:67-70` → `src/components/Pilot.tsx:804-850` → `src/app/api/pilot/route.ts:282-299`. Queued research/match/prepare work re-reads that owner’s confirmed profile at `src/app/api/pilot/route.ts:556-567`; public web research receives company/role only (`src/lib/pilot/tasks.ts:262-279`), while assessment and text preparation use owner-scoped data (`:201-259,288-357`). No server-side cross-candidate or cross-text-session leakage was found.

- Sybil intake/upload state is owner-scoped: `src/app/api/intake/route.ts:18-34`; `src/lib/pilot/server.ts:66-110`; `src/app/api/pilot/upload/route.ts:16-94`.

- The voice-resource gate remains sound. `src/lib/interview/server.ts:10-23` requires enabled status, a verified Supabase bearer user, verified Google identity, and an exact normalized allowlist. Both voice routes invoke it before protected work: `src/app/api/interview/route.ts:24,32`; `src/app/api/interview/call/route.ts:11`.

- Private voice notes remain excluded from model input: Realtime uses setup/transcript only at `src/app/api/interview/call/route.ts:23-29`; debriefing uses setup/transcript only at `src/app/api/interview/route.ts:59-61`; setup has no notes field at `src/lib/interview/types.ts:3-18`.

- Scope note: `/interview` itself is publicly renderable and can initiate Google OAuth (`src/app/interview/page.tsx:4`; `src/components/InterviewBeta.tsx:154-158,246-251`). This is not a protected-resource bypass, but if “invited only” includes preventing uninvited OAuth/account creation, enforce that in a Supabase auth hook or server-side guard.

- The PR-state claim holds: PR #3 is `OPEN` and `DRAFT`, based on `codex/executive-pilot` `d7f505d`, with head `23724a`; comparison reports 14 commits ahead and zero behind. Repository PR metadata reports no merged PRs. CI contains only test/typecheck/lint/build steps (`.github/workflows/ci.yml:31-39`) and `vercel.json:2-5` only configures existing worker crons; no repository promotion path was added.
