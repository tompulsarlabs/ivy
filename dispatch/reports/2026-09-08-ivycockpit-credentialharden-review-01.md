# Report — 2026-09-08-ivycockpit-credentialharden-review-01

Produced by the frontier/anthropic lane, 9.4 wall-minutes.

# Adversarial security review — PR #2, "Harden shared-credential access and document Ivy privacy findings"

Contract: `2026-09-08-ivycockpit-credentialharden-review-01`
Repository: `tompulsarlabs/pixel-perfect-showcase-8458`

## Scope and method

- **Head reviewed: `87a61a5`** ("Require approved operators for shared credentials and patch vulnerable dependencies"), tip of `origin/codex/ivy-security-hardening`, stacked directly on `fc99eac` (PR #1, `origin/codex/ivy-command-connection`), which is stacked on `main` at `9fbef5b`. The `gh` CLI was not permitted in this environment, so PR-number→branch identity is inferred from branch topology and the commit subject; if PR #2's head has moved since `87a61a5`, re-run against the new tip.
- All file:line references below are at `87a61a5`, read via `git grep -n "" 87a61a5 -- <path>`. No checkout, worktree, or working-tree modification was made.
- I reviewed the **whole head**, not only the PR #2 delta, because the five axes ask about behaviour of the merged result. Where a defect predates PR #2 I say so.
- **Not done, and not claimed:** the test suite was not run (read-only, no checkout permitted). Network fetches were denied, so registry hashes, advisory fixed-version floors, and deployed behaviour were not independently verified. The "56 tests pass" figure and the "dependency audit pass" result are the authoring worker's self-reports.
- **Instruction conflict, surfaced not silently resolved:** the contract's Definition of Done asks for a committed, pushed file at `dispatch/reports/2026-09-08-ivycockpit-credentialharden-review-01.md`. The dispatch Rules for this run say read-only and require the findings printed between `BEGIN_REPORT`/`END_REPORT`. I followed the Rules; this report is the deliverable and nothing was committed or pushed.

## Verdict by axis

| # | Axis | Result |
|---|---|---|
| 1 | Write credential inert on this head | **FAILS** — armed by a single env var; product UI still instructs granting write |
| 2 | JWT + exact allowlist before every credentialed call | **Holds**, with one real defence-in-depth gap and four qualifications |
| 3 | Raw Notion error bodies never returned or logged | **Confirmed sound** |
| 4 | Redirects rejected; real time limits | **Redirects confirmed**; timeouts are per-request only, not per-operation |
| 5 | Four patched deps resolve to non-vulnerable versions | **Resolution confirmed**; versions/hashes unverified, lockfile was hand-edited |

---

## F1 — HIGH. The write credential is not inert. It is armed by one environment variable, and the shipped UI still tells the owner to grant Contents write.

The PR body and `docs/security-review-2026-09-07.md:7` call this a release blocker that "must remain disabled." On this head, "disabled" is a documentation stance and an unset environment variable — not a property of the code.

**There is exactly one credential, and it serves both reads and writes.**

- `src/lib/ivy/commands.functions.ts:11-21` — `settings()` reads `IVY_GITHUB_TOKEN`, `IVY_OPERATOR_IDS`, `IVY_ALLOWED_REPOS`. One token value.
- `git grep -n "IVY_" 87a61a5 -- src` returns only those three names. There is no kill switch, no read-only mode, no separate write token, no feature flag anywhere in `src/`.

**The write path is live code reachable from the UI.**

- `src/lib/ivy/commands.functions.ts:101-102` — the sole write precondition is a non-empty token string.
- `src/lib/ivy/commands.functions.ts:186-203` — `submitCommand` constructs `new GithubQueue(config.token)` and calls `enqueue(...)` unconditionally once the action/operator/token checks pass.
- `src/lib/ivy/queue-core.ts:242` — `enqueue` calls `store.commit(snap.head, writes)`.
- `src/lib/ivy/queue-github.server.ts:82-128` — `commit()` creates a tree, creates a commit, and at **lines 119-122 PATCHes `refs/heads/main`** on `tompulsarlabs/ivy`. That is exactly the branch `docs/security-review-2026-09-07.md:37` says the Mac runner pulls and executes.

**A successful *read* arms the write UI.**

- `src/lib/ivy/commands.functions.ts:47-55` — `getCommandCapability` performs only a `snapshot()` (a read), then returns `available: true` and `actions: [...QUEUE_ACTIONS]`.
- `src/components/ivy/CommandDialog.tsx:155` — `!recordOnly && (!capability.data?.available || !capability.data.actions.includes(action.id))` is the *only* gate on the submit buttons. A read-capable token therefore presents a fully enabled Start work / Request changes / Retry interface.
- `src/lib/ivy/commands.functions.ts:53-54` — the capability success string is "Queue access checked. Work runs at the next available runner check; **submission confirms write access**." The design expects the token to carry Contents: write.

**The product's own setup instructions, shipped on this head, still tell the owner to grant write.**

- `src/routes/system.tsx:106-108` — "Add a repository-scoped GitHub credential with **Contents read/write** for tompulsarlabs/ivy to the server secret IVY_GITHUB_TOKEN."
- `src/routes/system.tsx:115-116` — "A queued task proves write access."
- `docs/command-connection.md:86-90` — deployment step 2 still says "Contents read/write … The token permits queue bookkeeping commits on Ivy main; branch protections must permit that authorized path." This sits *under* the heading at `docs/command-connection.md:80` that says the sequence is blocked, and after the paragraph at `:71-74` that says not to enable it. The PR edited the surrounding prose (`docs/command-connection.md:66-80`) but left the operative instruction intact, and did not touch `src/routes/system.tsx` at all.

**Why this compounds.** The read-only features the PR *does* want — the capability check (`commands.functions.ts:48`) and status reconciliation (`queue-status.server.ts:20,35`) — are gated on the same `IVY_GITHUB_TOKEN`. An owner who wants those must provision the token, and both the in-product panel and the deployment doc tell them to scope it read/write. At that instant the write path is live for every allowlisted operator, with no further gate. Per `docs/security-review-2026-09-07.md:35-37`, control of Ivy `main` is code execution on the Mac under the runner's OS account.

**Proposed fix.**

1. Add a default-deny flag, e.g. `IVY_QUEUE_WRITES_ENABLED === "true"`, enforced in **two** places so no future call site can bypass it: in `submitCommand` before the `enqueue` call at `src/lib/ivy/commands.functions.ts:186`, and inside `GithubQueue.commit` at `src/lib/ivy/queue-github.server.ts:83` (alongside the existing `invalid_write` guard). Add a test asserting `commit()` throws when the flag is unset.
2. Better, and structurally sound: split the credential into `IVY_GITHUB_READ_TOKEN` (used by `snapshot()`) and `IVY_GITHUB_WRITE_TOKEN` (required by `commit()`). With the write token unset, the capability and reconciliation features work and writes are impossible rather than merely unconfigured.
3. Have `getCommandCapability` return `available: true, actions: []` with an explicit read-only reason when writes are off, so `CommandDialog.tsx:155` renders the correct state instead of an armed one.
4. Change `src/routes/system.tsx:106-108` and `docs/command-connection.md:86-90` to instruct **Contents: read** only, and move the read/write step below the blocked-pending-boundary heading.

---

## F2 — MEDIUM-HIGH. Two shipped user-facing claims are false on this head.

- `src/routes/system.tsx:541` — "This console reads the ivy repository over public GitHub and never writes to it." Both halves are wrong: the console writes to `refs/heads/main` once configured (F1), and `docs/security-review-2026-09-07.md:5` records that Ivy is now private, so the anonymous reads at `src/lib/ivy/github.ts:17-18, 35-38` (unauthenticated `raw.githubusercontent.com` and `api.github.com`) no longer resolve. `docs/command-connection.md:76-78` states these client-side raw reads must be replaced with authenticated operator reads; that work is not in this PR.
- `docs/command-connection.md:98-99` — "Task instructions/criteria are published to the **public** Ivy repository, as stated in the confirmation." Ivy is private as of `docs/security-review-2026-09-07.md:5`. This is a stale privacy claim in the operator-facing confirmation text.

**Proposed fix.** Update `system.tsx:541` to state that the console writes queue and receipt records when a write credential is configured, and that repository reads require an authenticated operator. Correct `docs/command-connection.md:98-99` to say "private Ivy repository." Separately, replace or gate `loadSnapshot()` in `src/lib/ivy/github.ts:77-182` before the board is expected to work against the now-private repo.

---

## F3 — Axis 2: enforcement is present on every credential-backed entry point. Confirmed, with one real gap and four qualifications.

**Exhaustive enumeration.** `git grep -n "createServerFn" 87a61a5 -- src` returns **ten** server functions. All ten register `.middleware([requireSupabaseAuth])`; there is no unauthenticated fallback branch on any of them:

| Server function | Middleware | Operator check | Shared credential |
|---|---|---|---|
| `getCommandCapability` `commands.functions.ts:29-32` | `:30` | `requireOperator` `:32` | `IVY_GITHUB_TOKEN` |
| `submitCommand` `commands.functions.ts:84-102` | `:85` | `:95` + `queue-core.ts:135` | `IVY_GITHUB_TOKEN` |
| `listCommands` `commands.functions.ts:235-244` | `:236` | `queue-status.server.ts:12` | `IVY_GITHUB_TOKEN` |
| `getNotionStatus` `notion.functions.ts:78-81` | `:79` | `requireOperator` `:81` | Lovable + Notion keys |
| `createNotionAction` `notion.functions.ts:137-141` | `:138` | `requireOperator` `:141` | Lovable + Notion keys |
| `getWorkspace` `workspace.functions.ts:67-87` | `:68` | via `reconcileCommands` `:85` | none directly |
| `savePlan` / `saveOrder` / `saveDraft` / `deleteDraft` `workspace.functions.ts:102,130,168,195` | `:103,131,169,196` | n/a | none — caller-JWT client only |

The allowlist itself is exact: `src/lib/ivy/operator-access.ts:2-9` splits on comma, trims, filters empties, and requires `allowed.includes(userId)` with a truthy `userId` — no substring or prefix matching, and an empty/absent list denies everyone. `src/lib/ivy/operator-access.test.ts:3-12` covers `undefined`, `""`, `" , "`, anonymous callers, and the substring case `"to"` vs `"tom"`.

Denial happens **before** any credential is touched. `new GithubQueue(...)` appears at exactly `commands.functions.ts:48`, `commands.functions.ts:187`, and `queue-status.server.ts:35`, all downstream of an operator check. `src/lib/ivy/queue-status.test.ts:66-71` asserts `state.reads === 0` for a non-operator; `src/lib/notion-security.test.ts:54, 60, 110` assert `fetch` was never called on the denial paths.

**Gap (defence-in-depth, MEDIUM):** two queries select the command ledger with **no `user_id` predicate**, relying entirely on RLS that this PR's own report records as unverified.

- `src/lib/ivy/commands.functions.ts:238-242` — `.from("operator_commands").select("*").order(...).limit(200)`.
- `src/lib/ivy/workspace.functions.ts:74-78` — the same query inside `getWorkspace`.

`docs/security-review-2026-09-07.md:51` states: "Anonymous probes returned zero visible rows for each table. Empty results do not prove cross-user isolation … a two-user deployed test remains required." A non-operator authenticated user is correctly denied *reconciliation* (`queue-status.server.ts:12-19` returns "Operator access required" without reading GitHub) but still receives whatever rows the query returns — including other users' `instruction`, `expected_completion`, and `verification` free text.
**Fix:** add `.eq("user_id", context.userId)` at `commands.functions.ts:241` and `workspace.functions.ts:76`, so the server does not depend solely on a policy that has not been tested with two users.

**Qualification A (cosmetic).** `src/lib/ivy/commands.functions.ts:95` uses inline `config.operators.includes(userId)` instead of `requireOperator`. Semantics match — `settings()` at `:13-16` performs the same split/trim/filter — and `enqueue` re-checks independently at `queue-core.ts:135`. But this path does not inherit `operator-access.test.ts`'s coverage. Recommend routing it through `requireOperator` so there is one authorization code path.

**Qualification B (intentional, should be stated).** `RECORD_ONLY` actions (`commands.functions.ts:10`) skip the operator check — `:91`, `:95`, `:101` are all guarded by `!RECORD_ONLY.has(data.action)`. Those paths touch no shared credential (verified above) and write through the caller's own JWT-scoped Supabase client, so RLS bounds them. Any authenticated user can therefore append hold/close/drop rows to `operator_commands`. That looks deliberate and low-risk, but it is not documented as a decision.

**Qualification C (unverifiable here).** The JWT gate is `src/integrations/supabase/auth-middleware.ts:34-109` — unchanged by this PR and marked generated at `:1`. It requires an `authorization` header (`:57-61`), a `Bearer ` prefix (`:63-65`), a three-segment token (`:72-74`), a successful `supabase.auth.getClaims(token)` (`:94-97`), and a present `sub` claim (`:99-101`), throwing on each failure with no fallback. Whether `getClaims` performs cryptographic verification is a property of `@supabase/supabase-js@2.115.0` (`bun.lock:396`), which I could not exercise. Treat cryptographic verification as unconfirmed until the deployed signed-out/unapproved/approved test at `docs/security-review-2026-09-07.md:90` is actually run.

**Qualification D (test quality — the doc slightly overclaims).** `src/lib/notion-security.test.ts:4-23` mocks *both* `createServerFn` and `requireSupabaseAuth`. So `expect(endpoint.middleware).toEqual(["JWT_AUTH_REQUIRED"])` at `:44-46` and `:105` proves middleware **registration**, not enforcement — the file itself says so at `:2-3`. `docs/security-review-2026-09-07.md:72` lists "unauthenticated/unapproved handler denial" among the passing cases; the "unauthenticated" case (`userId: undefined` at `:47`) is a `requireOperator` denial inside the handler, not a JWT rejection. `docs/security-review-2026-09-07.md:29` is accurate ("adds JWT-auth middleware **registration**"); `:72` should be softened to match, and the deployed verification at `:90` remains the only thing that can close this.

---

## F4 — Axis 3: raw Notion error bodies genuinely never reach a client or a log sink. Confirmed sound.

Every credentialed Notion response path was traced:

- `src/lib/notion.functions.ts:42-44` — search non-2xx throws a constant string. `res.text()`/`res.json()` are never called on the failed response, so the body is never materialized.
- `src/lib/notion.functions.ts:200-202` — page-create non-2xx returns a constant. Same: the body is never read.
- `src/lib/notion.functions.ts:111-119` and `:205-210` — **bare `catch {}` with no binding.** This is the important detail: it makes it syntactically impossible to interpolate exception text, and it closes the subtle path where a 200 response with a non-JSON body makes `res.json()` (`:45`, `:203`) throw a V8 `SyntaxError` that embeds the leading bytes of the body. That error is discarded and replaced with a constant.
- **No log sink.** `git grep -n "console\.|captureException|reportError|logger|Sentry" 87a61a5 -- src` produces no hit in `notion.functions.ts`. `src/lib/error-capture.ts:55-63` wraps only `console.error` and does not hook `fetch`, so it never observes these responses. `src/lib/lovable-error-reporting.ts:26-57` is client-side and can only see what the server already returned.
- The only exception that escapes either handler is `requireOperator` (`:81`, `:141`), whose message is the constant at `src/lib/ivy/operator-access.ts:8`.
- Regression coverage exists: `src/lib/notion-security.test.ts:62-73` (error body and network-exception sentinels absent from the result) and `:74-101` (write rejection returns no raw body **and** `expect(log).not.toHaveBeenCalled()`).

**Adjacent, not Notion, for completeness.** Three other paths return upstream error text; none carries a provider body or a credential:

- `src/lib/ivy/queue-github.server.ts:38-42` places only the GitHub HTTP status into `QueueError`; `src/lib/ivy/queue-github.test.ts:62-64` asserts the token string does not appear.
- `src/lib/ivy/commands.functions.ts:214-232` returns `error.message` to the caller and persists it in `operator_commands.error`, but only for `QueueError`, whose messages are all fixed strings; anything else becomes the generic string at `:217`. Low risk.
- `src/lib/ivy/workspace.functions.ts:81` — `throw new Error(failure.message)` forwards the **raw PostgREST error message** to the client. Contrast `commands.functions.ts:109` and `:243`, which use constants for the same situation. Low, and outside this PR's diff, but inconsistent with the posture the PR establishes. Fix: replace with a constant.
- `src/lib/ivy/github.ts:64` returns `err.message` from the anonymous GitHub fetch to the client. Unauthenticated path, no credential. Low.

---

## F5 — Axis 4: redirects are genuinely rejected; time limits are real per request but absent per operation. One MEDIUM finding.

**Redirects — confirmed sound.**

- `src/lib/notion.functions.ts:34` and `:196` — `redirect: "error"` on both credentialed Notion calls, so a redirect never re-sends `Authorization: Bearer <lovable>` / `X-Connection-Api-Key: <notion>` (`:23-24`) to another host.
- `src/lib/ivy/queue-github.server.ts:26-35` — `...init` is spread **before** `redirect: "error"` and `signal`, so no caller can override either. Every GitHub call in `snapshot()` and `commit()` inherits them.
- Asserted by test at `src/lib/notion-security.test.ts:67` and `:99`.

**Timeouts — real per request.** `AbortSignal.timeout(10000)` at `notion.functions.ts:35`, `:197`, and `queue-github.server.ts:29`, in the same non-overridable position. The signal remains active through body consumption, so `res.json()` at `notion.functions.ts:45`, `:203` and `queue-github.server.ts:44` is also covered.

**Finding — no per-operation deadline.** `GithubQueue.snapshot()` (`src/lib/ivy/queue-github.server.ts:46-81`) issues two metadata requests plus up to **512** blob requests (the cap at `:56`) in sequential batches of eight (`:63`). Each of up to 64 batches can consume its full 10 s, so a single `snapshot()` can run roughly ten minutes against a slow upstream. `enqueue` then loops up to three times (`queue-core.ts:152`), each iteration doing a `snapshot()` plus a `commit()` (three more requests), and the failure path performs a further `snapshot()` at `:245`. Nothing bounds the total. "Requests carry real time limits" holds per request; the *operation* has none, so `submitCommand` and `listCommands` can be pinned far longer than the documented 10 s — a cheap resource-exhaustion lever against the server, reachable by any allowlisted operator or any upstream that simply stalls.

**Proposed fix.** Create one `AbortSignal.timeout(N)` per `snapshot()` (and one per `submitCommand`), thread it through `GithubQueue`, and combine with the per-request signal via `AbortSignal.any([operationSignal, AbortSignal.timeout(10000)])` at `queue-github.server.ts:29`. Alternatively lower the 512 cap at `:56` and widen the batch at `:63`. Add a test asserting the operation aborts once the outer deadline passes.

---

## F6 — Axis 5: all four patched versions win their resolution, but the lockfile was hand-edited and the versions and hashes are unverified.

**Resolution is correct.** I traced every consumer of each patched package at `87a61a5`, including entries the diff did not touch:

| Package | Lockfile entry | Every consumer | Satisfied |
|---|---|---|---|
| `brace-expansion@1.1.18` | `bun.lock:570` | `minimatch@3.1.5` requires `^1.1.7` (`bun.lock:826`) | yes; `balanced-match@1.0.2` (`bun.lock:566`) satisfies `^1.0.0` |
| `brace-expansion@5.0.9` (nested) | `bun.lock:1114` | `minimatch@10.2.6` requires `^5.0.8` (`bun.lock:1070`) | yes; `balanced-match@4.0.4` (`bun.lock:1118`) satisfies `^4.0.2` |
| `js-yaml@4.3.1` | `bun.lock:770` | `@eslint/eslintrc` `^4.3.0` (`bun.lock:148`); `xmlbuilder2` `^4.1.1` (`bun.lock:1022`) | yes, both |
| `nanoid@3.3.18` | `bun.lock:830` | `postcss@8.5.24` `^3.3.16` (`bun.lock:870`) | yes |

There is **no surviving stale entry** for any of the four — no second `js-yaml`, no second `nanoid`, and exactly the two expected `brace-expansion` entries. The version-resolution half of this axis is confirmed.

**Not confirmed — and this is a real defect in the change.** The four edited entries use a different serialization from every other line in the file: `{"dependencies": {"balanced-match": "^1.0.0", ...}}` at `bun.lock:570` versus bun's own `{ "dependencies": { ... } }` at `bun.lock:566`, `:826`, `:870`. That whitespace delta is the signature of a **hand-edited lockfile**, not of `bun update`. Consequently nothing in this change has verified that these versions exist in the registry or that the `sha512-` integrity values match the published tarballs. If a hash is wrong, `bun install --frozen-lockfile` fails at build time; if a version does not exist, resolution fails. `evals/security-review-2026-09-07.json:13` reports `dependency_audit: "pass; no advisories returned"` and `docs/security-review-2026-09-07.md:68` reports a clean re-audit — both are authoring-worker self-reports, not evidence in this repository. Network access was denied in this environment, so I could verify neither the integrity hashes, nor the existence of these versions, nor the fixed-version floors of the three cited advisories.

**Proposed fix.** Regenerate the lockfile with the package manager (`bun update brace-expansion js-yaml nanoid && bun install`) and commit bun's own output, so both the formatting and the hashes are tool-produced. Then paste the actual `bun install --frozen-lockfile` and audit output — not a summary of it — into `evals/security-review-2026-09-07.json`.

---

## Minor notes

- **`.env` remains tracked.** `.gitignore:36-37` adds `.env` / `.env.*`, but `.env` was already committed and `.gitignore` does not untrack it; it is still present at `87a61a5:.env:1-6`. Contents are Supabase project identifiers, URLs, and `sb_publishable_` keys only — no server credential — which matches the claim at `docs/security-review-2026-09-07.md:53`. Confirmed, no action required beyond awareness that the ignore rule is inert for this path.
- **`vitest.config.ts:3-6`** adds the `@` → `./src` alias. This is required for `notion-security.test.ts:21` to mock `@/integrations/supabase/auth-middleware`. No security implication.
- **PR #2's actual delta is small and correct as far as it goes**: `requireOperator` added at `notion.functions.ts:81, 141`, `commands.functions.ts:32`, `queue-status.server.ts:12`, plus `redirect: "error"` / `AbortSignal.timeout` and constant error strings in `notion.functions.ts`. The problem is not what the PR changed; it is that F1's claim of a disabled write credential is not backed by anything in the code, and the product's own setup panel still contradicts it.

## Recommendation

**Do not treat the "write credential remains disabled" claim as satisfied by this head.** F1 is the release blocker the PR body itself describes, and it is unaddressed in code: the write path is one environment variable away from live, and `src/routes/system.tsx:106-108` instructs the owner to set it with write scope. Land a default-deny gate (or a split read/write token) plus the two copy corrections in F1.4 and F2 before this is described as blocked. F3's missing `user_id` predicate and F5's unbounded operation deadline should land in the same pass. F6 needs a tool-regenerated lockfile, not further prose. Axes 3 and 4's redirect handling are genuinely sound and need no change.
