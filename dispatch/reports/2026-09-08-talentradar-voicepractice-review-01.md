# Report — 2026-09-08-talentradar-voicepractice-review-01

Produced by the workhorse/openai lane, 2.1 wall-minutes.

# PR #3 adversarial review

Reviewed head `a8a4cf4` (`codex/rad-interview-beta`) against the requested axes.

## Findings

1. **High — `/interview` is not itself access-gated, and an unapproved visitor can create a Google/Supabase account.** [src/app/interview/page.tsx:4] renders the client application for every request. [src/components/InterviewBeta.tsx:144-148] exposes `signInWithOAuth` to every visitor who can reach the share link. The allowlist is checked only when an API route is called, so it prevents session/model access but does not prevent public OAuth sign-in/account creation or display of the signed-in workspace shell.

   Proposed fix: enforce invited-user eligibility at the auth boundary: disable public Supabase signups, pre-provision invited identities (or use an auth hook that rejects non-allowlisted identities before user creation), and add a server-side `/interview` guard/denied state. Keep `voiceAuth` as defence in depth.

2. **Medium — an account switch can transiently render the previous account’s session list.** [src/components/InterviewBeta.tsx:98-104] starts an owner-authenticated list request but only checks the effect-local `alive` flag before applying its result. [src/components/InterviewBeta.tsx:60-70] clears state on an auth event, but React cleanup may not run before an already in-flight old-account request resolves and calls `setSessions`. This is a same-browser cross-account display race; the server does not disclose data to the new identity.

   Proposed fix: capture an auth-generation and owner ID when starting the request, increment the generation synchronously in `onAuthStateChange`, and apply the result only when both still match the current authenticated user. Abort in-flight account-scoped requests on identity change.

## Confirmations

- **Server-side resource gate is sound once an API is invoked.** [src/lib/interview/server.ts:10-23] requires the kill switch, a bearer token verified by Supabase, verified Google identity, and an exact case-normalised allowlist match. Both interview routes call it before reads, writes, budget use, model calls, or Realtime calls ([src/app/api/interview/route.ts:24,32], [src/app/api/interview/call/route.ts:11]). Owner predicates are present for every session lookup/update ([src/lib/interview/server.ts:30-40]), and direct browser table/RPC access is revoked ([supabase/migrations/20260907110000_voice_interview_beta.sql:34-41]).

- **Private notes are excluded from the two server model requests.** The Realtime request constructs instructions from saved setup and transcript only ([src/app/api/interview/call/route.ts:23-29]); the written debrief sends only setup and transcript ([src/app/api/interview/route.ts:59-61]). The exported ChatGPT fallback likewise uses setup only ([src/components/InterviewBeta.tsx:214-217]). This is backed by targeted tests ([tests/interview-api.test.ts:18-23], [tests/interview-call.test.ts:18-26]).

- **No repository code path promotes this beta to main, production, public invitations, or a share link.** The beta head is not an ancestor of `origin/main`; CI only checks branches ([.github/workflows/ci.yml:3-37]); `vercel.json` defines only existing pilot worker crons ([vercel.json:1-6]); and no deployment, invitation, or share-link creator exists in the diff. The claimed preview/share-link environment binding remains external configuration and cannot be proven from source alone.
