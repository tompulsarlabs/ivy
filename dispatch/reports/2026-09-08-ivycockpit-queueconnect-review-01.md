# Report — 2026-09-08-ivycockpit-queueconnect-review-01

Produced by the workhorse/anthropic lane, 11.2 wall-minutes.

# Review — PR #1 "Connect cockpit actions to the Ivy queue"

**Contract:** `2026-09-08-ivycockpit-queueconnect-review-01`
**Head reviewed:** `codex/ivy-command-connection` @ `fc99eac` ("Connect cockpit commands to the Ivy queue with explicit controls"), 22 files, +1631/−307 vs `origin/main` @ `9fbef5b`.
**Method:** static review of the PR head via `git show origin/codex/ivy-command-connection:<path>`. All line numbers below are PR-head lines. No code was executed, no test suite was run, and no GitHub API call was made.

**Two limits on this review, stated up front.** `gh` was unavailable in this sandbox, so I could not read the PR body itself; I identified PR #1 as `codex/ivy-command-connection` by title match against the single commit on the only candidate branch, and I checked the PR's stated claims against `docs/command-connection.md` on the same head, which the PR adds. Second, I did not verify runtime behaviour — no deployed instance, no live GitHub write, no runner pickup.

---

## 0. The contract's premise is false on this head

The contract asks me to *confirm* that the command adapter "points to an undefined endpoint" and that execution is "disconnected." **It is not true on this head.** That sentence describes the adapter this PR *deletes*. `docs/command-connection.md` says so explicitly: *"The previous adapter required an undefined `IVY_COMMAND_ENDPOINT` and token… The replacement uses the existing TanStack server and Supabase operator sign-in."* The `ENDPOINT_VAR`/`TOKEN_VAR` constants are gone from `commands.functions.ts`.

The premise conflates three separate things. Split:

**(a) A live queue write path is reachable. Confirmed present.**
`src/lib/ivy/commands.functions.ts:184-201` → `enqueue` → `GithubQueue.commit` at `src/lib/ivy/queue-github.server.ts:82-129`, which performs `POST /git/trees`, `POST /git/commits`, and `PATCH /git/refs/heads/main` against `https://api.github.com/repos/tompulsarlabs/ivy` (`queue-github.server.ts:14`, `:119-122`). This is a real, unconditional write to Ivy's default branch, gated only on three environment variables being set (`commands.functions.ts:10-20`). A file written to `dispatch/queue/<id>.md` (`queue-core.ts:230-231`) is what the existing scheduled runner consumes — so this path does cause worker execution and model spend, indirectly.

The doc's statement *"No live GitHub queue write was made by this development session"* is a statement about the session, not about the code. Anyone reading the PR body's "disconnected" framing and approving on that basis would be approving a live write path. This is the single most important thing for the merge decision.

**(b) Direct runner invocation: genuinely absent.** Nothing in the diff calls a runner, opens a port, spawns a process, or touches a Mac host. Execution remains indirect, via the existing runner polling `dispatch/queue/`. Confirmed sound.

**(c) A deployment path: genuinely absent from the code.** Lovable tracks `main`; this branch is not merged. Merging *is* the deploy step (`docs/command-connection.md`, "Deployment setup"). Confirmed sound.

**Proposed fix:** amend the PR body so it describes the post-change state. The reviewer's checklist for merge is: this branch reaching `main` plus three env vars being set is sufficient to make cockpit buttons write to `tompulsarlabs/ivy` main and cause runner execution.

---

## 1. Operator allowlist — sound

Enforced server-side in two independent places, both against the Supabase `userId` supplied by `requireSupabaseAuth` middleware, never by the client:

- `src/lib/ivy/commands.functions.ts:93` — `!config.operators.includes(userId)` rejects before any DB insert or GitHub call.
- `src/lib/ivy/queue-core.ts:135-136` — `allowedOperators.includes(operator)` is the *first* statement in `enqueue`, before input parsing.

`submitCommand` carries `.middleware([requireSupabaseAuth])` (`:83`), so `userId` is not client-supplied. The `RECORD_ONLY` bypass (`:89`, `:93`, `:99`) lets any signed-in user write hold/close/drop rows to their own RLS-scoped ledger; that is by design and those rows never reach the queue. Covered by `queue-core.test.ts:121-128`, which asserts `store.writes === 0` for a non-allowlisted operator.

No finding.

## 2. Repository allowlist — sound

Four independent server-side layers, all after the client input crosses the boundary:

1. `queue-core.ts:12` — `repo` regex hard-pins the owner to `tompulsarlabs/`.
2. `queue-core.ts:138-139` — membership in the `IVY_ALLOWED_REPOS` env list.
3. `queue-core.ts:157-158` — must be in Ivy's own `config.yml` watchlist and not in `parked`.
4. `queue-core.ts:160-161` — must equal the `repo:` recorded in the source task's own committed record, so a client cannot retarget an existing task.

Supporting evidence that the server never follows client-supplied URLs: `sourceRawUrl` is accepted by the schema at `commands.functions.ts:72` and then **never read** — it is not passed to `enqueue` (`:186-201`) and not persisted in the insert (`:112-126`). The only fetch of that URL is client-side, in the browser (`CommandDialog.tsx:38-53`). The doc's claim "Arbitrary source URLs from the client are not fetched by the server" holds.

Covered by `queue-core.test.ts:124-127` and `:137-142`. No finding, beyond a trivial note that `sourceRawUrl` is dead weight in the schema and could be dropped.

## 3. Queue policy and bounded operations — sound in the server, misdescribed in the UI

**Server-side bounds are real.** The write allowlist at `queue-github.server.ts:87` is the strongest control in the PR:

```
!/^dispatch\/(?:queue\/[a-z0-9-]+\.md|commands\/[a-f0-9]{64}\.json)$/.test(p)
```

checked *before any API call* (`queue-github.test.ts:28-38` asserts zero fetches on rejection). `config.yml`, `dispatch/done/`, `dispatch/failed/` and the runner status file are unwritable by construction. Beyond that: unsupported actions are rejected at `commands.functions.ts:88-92` against `RECORD_ONLY ∪ QUEUE_ACTIONS`, where `QUEUE_ACTIONS` is exactly `["dispatch_now", "iterate", "retry_unchanged"]` (`queue-core.ts:5`). There is **no** server-side merge, cancel, verify-now, pool-change or ship path anywhere in the diff. Type is forced to `build` and lane to `workhorse` for iterate (`queue-core.ts:214-215`); budget is capped at `Math.min(source, 30)` (`:231`); expiry comes from `config.yml`, not the client; frontmatter is generated entirely from validated records and server policy. Follow-ups are blocked while the source is active (`:186-193`). Daily cap enforced at `:202-206`.

So: **"Start work" / "Request changes" / "Retry" can only ever create bounded, receipted tasks. There is no reachable path to an unsupported operation.** That part of the contract's question is confirmed sound.

But the dialog tells the operator things the server does not do:

### Finding 3.1 (high) — "Start work" claims it releases the task to the runner immediately; the server only writes a receipt

`src/lib/ivy/commands.ts:164-171`

```ts
dispatch_now: {
  consequence: "Release the queued contract to the runner immediately, ahead of the schedule.",
  expectedCompletion: "The contract moves to claimed and then records an outcome.",
```

`CommandDialog.tsx:175` renders `action.consequence` in the dialog description, `:218` renders it again as "Requested work", and `:221` renders `expectedCompletion` as "Complete when". Meanwhile `queue-core.ts:172-184` for `dispatch_now` performs only eligibility checks and leaves `writes` containing nothing but the receipt (`:240`) — no state change, no reprioritisation, no runner signal. `queue-core.test.ts:197-209` asserts exactly this and expects the progress string `"Queued for the next runner check"`.

The PR contradicts its own specification. `docs/command-connection.md` states: *"**Start work:** acknowledges an existing, eligible open queue task. It does not duplicate the task or wake the runner… the interface says queued for the next runner check."* The interface does not say that; the dialog says the opposite.

**Failure scenario:** an operator clicks "Start work" on a task the scheduled runner would not reach for hours. The dialog promises immediate release ahead of schedule and a move to `claimed`. Nothing changes. The operator waits, or clicks again, and reads the delay as a broken runner.

**Fix:** change `consequence` to "Confirm this task is eligible and record the decision. It stays queued for the next scheduled runner check — this does not start a worker now." and `expectedCompletion` to "The task remains open and is picked up at the next runner check."

### Finding 3.2 (high) — "Discard" and "Close" claim repository state changes that never happen

`src/lib/ivy/commands.ts:120-127` (`drop`: *"Close the contract as abandoned so it stops appearing as outstanding work"*, `expectedCompletion: "The contract is moved out of the active queue"*, `verification: "Contract folder read back from the repository"`) and `:146-153` (`close`: *"Mark the verified contract as finished"*, *"The contract is closed in the repository"*).

Both are in `RECORD_ONLY` (`commands.functions.ts:9`) and change nothing outside the operator's private Supabase ledger. `CommandDialog.tsx:296-298` does add "This records your decision only. It does not start, stop or change any work" — but it renders *below* `:218`/`:221`, which have already asserted the repository will change. Two contradictory statements in one dialog; the specific one comes first.

**Failure scenario:** an operator drops a stale task, believes it left the queue as the dialog said, and the task remains open and eligible for the runner.

**Fix:** rewrite both `consequence`/`expectedCompletion` strings to describe a private note ("Record that you consider this abandoned. The task is not removed from Ivy's queue and the runner is unaffected."), and set `verification: "None — this is a human record, not execution."` to match `hold` at `:90`.

### Finding 3.3 (medium) — the retry path bypasses the reserved-content guard

`src/lib/ivy/queue-core.ts:140-148` blocks `---`, `outcome:`, `verified:` and reserved `## ` headings in operator-supplied text. But the `retry_unchanged` branch at `:220-228` assembles the new task body from `section()` extracts of the *source* contract, and those strings never pass through that guard before being written at `:231`.

The invariant "user text cannot inject reserved frontmatter/result sections" holds. The stronger invariant the doc implies — that a generated task file never contains reserved markers — rests entirely on the boundary regex at `queue-core.ts:116-124` (`(?=^## |^outcome:|$)`), which is heuristic. Any source contract whose Task or Verification section contains a bare `---` line, or an indented `outcome:`, is copied through verbatim. `queue-core.test.ts:189-196` only tests one well-formed fixture where the outcome starts at column 0.

**Failure scenario:** a source contract whose "Task" section contains a Markdown horizontal rule is retried; the rule is copied into the new task body, where downstream frontmatter parsers that split on `---` without anchoring mis-read the record.

**Fix:** run the same loop from `:140-148` over the assembled `task`/`dod`/`verify` strings in the retry branch and fail closed with a distinct code (e.g. `unsafe_source`).

### Finding 3.4 (medium) — one malformed contract anywhere in the Ivy repo blocks all follow-up creation

`src/lib/ivy/queue-core.ts:196-201`

```ts
const todayCount = records.filter(
  ([, text]) => day(new Date(contract(text).created)) === day(now),
).length;
```

`contract()` (`:67-72`) runs `contractSchema.parse` and **throws** on any record that does not fit. `contractSchema` (`:42-53`) is narrow: `type` must be one of four values, `state` one of five, `budget.wall_minutes` must be `> 0` and `≤ 60`, `created`/`expires` must be RFC-3339 with offset. This runs across *every* file in `dispatch/queue|done|failed/`, including years of historical records the cockpit did not create.

**Failure scenario:** one legacy contract in `dispatch/done/` has `type: research` or `wall_minutes: 90`. Every "Request changes" and "Retry" from the cockpit now throws a `ZodError`, which is not a `QueueError`, so it surfaces via `commands.functions.ts:212-215` as the generic *"The outcome could not be confirmed. Retry this same request to reconcile it safely."* The operator retries forever against a deterministic failure with no indication of the cause. `dispatch_now` still works, which makes the diagnosis harder.

**Fix:** use `contractSchema.safeParse` in the cap count and skip (or conservatively count) records that fail, and add a distinct `QueueError("unreadable_queue", …)` naming the offending path if a record must be rejected.

## 4. Source-revision check — sound, with a caveat worth stating

`src/lib/ivy/queue-core.ts:162-166` recomputes `sourceRevision(source.text)` from the server's **own** snapshot of the contract and compares it to the client-supplied value. The client value (`CommandDialog.tsx:38-53`) is not trusted as content — it is an assertion of "this is what I was shown," and the server independently derives the truth. `CommandDialog.tsx:164` also blocks submission when no revision could be read, so a failed fetch fails closed rather than submitting blind. Covered by `queue-core.test.ts:129-136` and `:172-179` (`sourceRevision: null` rejected).

Caveat to record rather than fix: this is a race guard, not an authorisation control. An allowlisted operator's client can compute a matching digest from the public raw file without ever displaying it. Correct for a trusted-operator threat model, which is what the allowlists establish. No finding.

## 5. Atomic writes and idempotent retries — sound in the queue layer

- One tree + one commit + one non-force ref update; `force: false` is asserted by test (`queue-github.test.ts:25`), `redirect: "error"` and a 10s timeout on every call (`queue-github.server.ts:28-29`).
- A lost race returns `false` on 409/422 (`:125-126`) rather than force-pushing, and `enqueue` re-snapshots and revalidates up to three times (`queue-core.ts:152`, `:242`).
- Replay is by durable receipt keyed on a content fingerprint (`:149-155`), so a repeated submission returns the original receipt instead of creating a second task — and a *different* payload under the same key is rejected as `key_conflict` (`:104-113`) rather than silently overwriting.
- A lost response after a successful push is recovered by re-reading the receipt (`:243-250`).
- A truncated GitHub tree is refused rather than treated as an empty queue (`queue-github.server.ts:50-54`) — a good catch, since an empty queue would have defeated the collision and cap checks.
- Errors do not echo the token or the upstream body (`:38-42`, asserted at `queue-github.test.ts:59-67`).

Races are covered by `queue-core.test.ts:94-120` and `:149-158`. The mechanism is sound. What is not sound is how its outcomes are reported — Finding 6.1.

## 6. Error and delivery reporting — the main correctness defect

### Finding 6.1 (high) — every failure is reported as "unconfirmed, retry to reconcile," including failures that can never succeed

`src/lib/ivy/commands.functions.ts:211-231`

```ts
} catch (error) {
  const message = error instanceof QueueError ? error.message : "The outcome could not be confirmed…";
  row = await persist({
    status: "Needs attention — retry to reconcile",
    delivery: "Unconfirmed",
    error: message,
  });
```

That state is accurate for exactly two of the fifteen-odd error codes: `delivery_unknown` (`queue-core.ts:247`) and `busy` (`:253`). Every other error is raised *before* any write and is deterministic: `forbidden` (`:136`, `:139`), `reserved_content` (`:144`), `parked` (`:158`), `stale` (`:163`), `repo_mismatch` (`:161`), `invalid_state` (`:174`, `:190`), `expired` (`:179`), `blocked` (`:183`), `daily_cap` (`:203`), `collision` (`:209`), `lane_unavailable` (`:169`, `:219`), `source_missing`/`invalid_source` (`:87`, `:69`), plus every `ZodError`. In all of those, nothing was sent and retrying the identical request cannot change the result.

The mislabelling then propagates to two more surfaces:
- `CommandDialog.tsx:342-350` shows a **"Retry same request"** button whenever `delivery === "Unconfirmed"`.
- `queue-status.server.ts:35-41` reports `"No queue receipt — retry to reconcile"` on every subsequent page load, permanently.

The code even knows better in one case: `commands.functions.ts:228` sets `stale: true` on the response, yet the row is still written as `Unconfirmed` and still gets a retry button.

**Sharpest failure scenario:** the owner follows `docs/command-connection.md` step 2 but provisions the fine-grained token with Contents **read** only. `getCommandCapability` performs a read-only `snapshot()` (`commands.functions.ts:45`), succeeds, and reports `available: true` with "Queue access checked." Every submission then fails at `POST /git/trees` with `github_403`, which is caught by `enqueue`'s inner handler at `queue-core.ts:243-250`, finds no receipt, and throws `delivery_unknown` — *"Delivery could not be confirmed. Retry this same request to reconcile it safely."* The operator is told to retry a permanently misconfigured write, on a connection the System page calls healthy, with no message anywhere naming the missing permission.

**Fix:** classify errors by code into `rejected` (nothing sent — every pre-write code above, plus `ZodError`, plus `github_401/403/404`) and `unconfirmed` (`delivery_unknown`, `busy`, `github_5xx`). Persist `delivery: "Rejected"` / `status: "Not sent — <reason>"` for the first class, and gate the `CommandDialog.tsx:342` retry button on `delivery === "Unconfirmed"` only. Surface `github_403` as a distinct "the configured credential cannot write to the queue" message rather than a delivery ambiguity.

Related: **`submitCommand` has no test coverage at all.** All 25 new tests target `queue-core`, `queue-github` and `queue-status`; the layer holding this bug is untested.

### Finding 6.2 (high) — `getCommandCapability` is an unauthenticated endpoint that runs a privileged full-repository read

`src/lib/ivy/commands.functions.ts:28`

```ts
export const getCommandCapability = createServerFn({ method: "GET" }).handler(
```

No `.middleware([requireSupabaseAuth])` — compare `submitCommand` at `:82-83` and `listCommands` at `:233-234`, which both have it. TanStack `createServerFn` exposes this as a publicly callable RPC endpoint. Each call:

- runs `new GithubQueue(config.token).snapshot()` (`:45`) using the server's write-capable credential — one ref read, one recursive tree read, and up to 512 blob reads (`queue-github.server.ts:46-80`);
- returns the exact names of unset environment variables (`:31-35`) and whether the credential works.

**Failure scenario:** an unauthenticated client polls this endpoint. Each call burns GitHub quota against the privileged token. Once the 5000/hour authenticated limit is exhausted, `snapshot()` starts failing, so `getCommandCapability` reports unavailable and `reconcileCommands` (`queue-status.server.ts:73-79`) degrades every command to "Progress unavailable" — the app-wide banner at `ExecutionConnection.tsx:20-28` shows "Work cannot start from this cockpit" for the real operator.

**Fix:** add `.middleware([requireSupabaseAuth])`; return the `missing` array only to allowlisted operators (a generic "not configured" for everyone else); and replace the full `snapshot()` with a cheap `GET /git/ref/heads/main` probe, since the capability check only needs to prove the credential can reach the repo.

### Finding 6.3 (medium) — full-repository snapshots on a 60-second timer, amplifiable by any authenticated user

`src/lib/ivy/workspace.functions.ts:85` calls `reconcileCommands` on **every** `getWorkspace`, and `src/lib/ivy/useWorkspace.ts:78` sets `refetchInterval: 60_000`. `submitCommand` snapshots twice per submission — once inside `enqueue` (`queue-core.ts:153`) and again at `commands.functions.ts:202` purely to compute a progress string. Each snapshot walks the whole tracked tree.

`queue-status.server.ts:18` short-circuits when every row is a hold/close/drop note, which correctly spares users with no command history. But the Supabase grants at `supabase/migrations/20260906081412_…sql:71,74` let any authenticated user INSERT a row into their own ledger with an arbitrary `action` string directly from the browser client, bypassing `submitCommand`'s operator gate entirely. A row with `action: 'iterate'` defeats the short-circuit, and that account's every 60-second `getWorkspace` poll then forces a privileged full-repository read.

**Fix:** memoise the snapshot server-side keyed on the head SHA with a short TTL; have `reconcileCommands` fetch only the receipt blobs and linked-contract blobs it actually needs rather than the whole tree; have `enqueue` return the snapshot it already holds so `commands.functions.ts:202` reuses it; and restrict reconciliation to rows whose `action` is in `QUEUE_ACTIONS`.

### Finding 6.4 (low) — the idempotency key is a 32-bit non-cryptographic hash, and a collision is a permanent dead end

`src/lib/ivy/commands.ts:431-436` computes `h = (h * 31 + charCode) | 0` over `objectId|action|instruction` and emits `idem-<base36>`. The server derives the receipt path from it: `commandId = hash(operator + "\n" + idempotencyKey)` → `dispatch/commands/<commandId>.json` (`queue-core.ts:149-151`).

The Java-style 31-multiplier hash has trivially constructible collisions and a ~65k birthday bound. On collision, `receiptAt` (`:104-113`) finds a receipt whose fingerprint differs and throws `key_conflict` — "This request ID belongs to different work. Open a new preview." But the key is a pure function of the same inputs, so reopening the preview regenerates the identical key. That action, for that task, with that text, can never be submitted.

**Fix:** use `crypto.subtle.digest("SHA-256", …)` — already imported and used in the same PR at `CommandDialog.tsx:42-49` — or generate a random UUID per opened preview and hold it in dialog state.

### Finding 6.5 (low) — `created_by: tom` is hardcoded while the allowlist is plural

`src/lib/ivy/queue-core.ts:231` writes `created_by: tom` into every generated contract, but `IVY_OPERATOR_IDS` is a comma-separated list (`commands.functions.ts:12-15`) and `enqueue` receives the real `operator` as an argument (`queue-core.ts:130`). A second approved operator's tasks are attributed to Tom.

Note that `queue-core.test.ts:92` deliberately asserts the receipt does *not* contain the operator ID — pseudonymising the operator in the public Ivy repo appears intentional. So the fix should preserve that: map the Supabase ID to a configured public handle rather than writing the raw ID.

**Unverified, flagged for the owner:** the commit identity `ivy-bot <bot@ivy.invalid>` at `queue-github.server.ts:113-114` — I could not check this against Ivy's playbook bot identity, and `bot@ivy.invalid` is a reserved-TLD address that will not link to any account.

### Finding 6.6 (low) — 25 new tests, no way to run them

`vitest.config.ts` is added and 25 tests ship across three files, but `package.json` gains no `test` script (scripts remain `dev`, `build`, `build:dev`, `preview`, `lint`, `format`). The doc's verification section invokes `bunx vitest run` by hand. Nothing in CI or in a default `bun test` will execute these controls.

**Fix:** add `"test": "vitest run"` to `package.json`.

## 7. Worker completion is never presented as independent verification — sound

I checked every surface that renders a completion state, including the pre-existing ones the PR did not touch.

**New surfaces added by this PR are honest:**
- `queue-core.ts:256-262` — `progress()` returns `"Result recorded — inspect independent checks"` for a done contract. It reports where the record sits, never that checks passed. `queue-core.test.ts:210-215` asserts precisely this ("reported completion cannot imply independent checks passed").
- `queue-status.server.ts:5-79` — the browser-writable ledger cannot attest to anything. `reconcileCommands` overwrites `status` and `delivery` on **every** return path from the Git receipt, and nulls `linked_work_id` when no receipt exists. Better still, it re-derives the fingerprint from the row's own fields at `:44-55`, so an operator who edits `instruction`/`verification` in their own row via the Supabase client gets "Receipt could not be verified" rather than a stale pass. Tests at `queue-status.test.ts:36-46` confirm a forged `Sent` and a forged `Not applicable` are both downgraded to `Unconfirmed`.
- `commands.functions.ts:49-51` — the capability reason states "Queue access checked… submission confirms write access," explicitly declining to infer write access from a read.
- `src/routes/index.tsx:91-92` — the dashboard heading is narrowed to "Runner and source health," with body copy stating cockpit execution has a separate check, so a fresh heartbeat can no longer stand in for working commands. This is a genuine improvement.

**Pre-existing surfaces still hold.** `readVerification` (`src/lib/ivy/outcome.ts:71-96`) reads `c.outcome.verified` — the failsafe-written stamp — and never the worker's exit code or claim. Its `provenance` string is careful: *"Ivy recorded a verification pass on this contract. The cockpit shows the recorded stamp and note; it did not rerun the checks itself."* `verificationState` (`derive.ts:26-32`) maps a missing stamp to `"Claimed done but unverified"`, `decideContract` (`commands.ts:322-329`) renders "The worker reported completion. No independent verification stamp exists on this contract," and `deriveExceptions` (`derive.ts:506-525`) raises a medium-severity exception for exactly that case. `shipEvidence` (`outcome.ts:297-321`) refuses to establish shipping without a current stamp *and* declines it for review contracts on the grounds that verifying a report exists is not approval of the code it reviewed.

**Verdict on this axis: confirmed sound.** I found no surface where worker completion is presented as independent verification.

One presentational note, not a finding: `system.tsx:146-156` and `CommandDialog.tsx:186-191` set the pill tone from `delivery === "Sent"` → green. That is green-for-delivery, not green-for-result, and the status text beside it always says what actually happened, so it does not misrepresent verification. The audit trail correctly sources from `useWorkspace().commands` (`system.tsx:55`) → `getWorkspace` → `reconcileCommands`, not from unreconciled data.

## 8. Stale claims left in shipped copy

### Finding 8.1 (high) — the System page still tells the operator the cockpit never writes to the Ivy repository

`src/routes/system.tsx:541-542`

```
This console reads the ivy repository over public GitHub and never writes to it.
Operator actions are recorded separately, outside Ivy's own state.
```

Both sentences are false on this head. The server commits to `tompulsarlabs/ivy` `main`, and operator receipts are written *inside* Ivy's own state at `dispatch/commands/<id>.json` (`queue-core.ts:151`, `:240`). This is unchanged context in the diff — the author updated the neighbouring header (`Shell.tsx:42-44` correctly drops the "· read-only" badge) but missed this paragraph.

**Failure scenario:** the exact reader this PR is aimed at — an owner deciding whether to provision a write-capable GitHub token — reads a screen that says the console never writes, and mis-scopes the credential or mis-assesses the blast radius.

**Fix:** replace with something like: "This console reads the ivy repository over public GitHub. When execution is connected, it also writes operator commands and linked tasks to `dispatch/` on the ivy default branch, using the configured server credential. It never writes to product repositories."

### Finding 8.2 (low) — the new `.gitignore` rule does not protect the file the setup doc points at

`.gitignore` gains `.env` / `.env.*` with the comment *"Server credentials belong in deployment secrets or local overrides."* But `.env` is already tracked on this head (six lines), and `.gitignore` has no effect on tracked files. Contents are public `SUPABASE_*` / `VITE_SUPABASE_*` values only, and the comment does acknowledge the tracked file, so the exposure today is nil — but the rule provides no protection for the `IVY_GITHUB_TOKEN` that step 2 of the setup instructions tells the owner to configure.

**Fix:** `git rm --cached .env`, commit the public client values to `.env.example`, and state in the setup steps that `IVY_GITHUB_TOKEN` goes in the deployment secret store and never in a repository file.

---

## Summary

| # | Severity | Location | Finding |
|---|---|---|---|
| 0 | — | `queue-github.server.ts:82-129` | PR premise is stale: a live queue write path **is** reachable on this head |
| 3.1 | High | `commands.ts:164-171` | "Start work" claims immediate runner release; server writes only a receipt |
| 3.2 | High | `commands.ts:120-127`, `:146-153` | Drop/Close claim repository changes that never occur |
| 6.1 | High | `commands.functions.ts:211-231` | Deterministic rejections reported as "unconfirmed — retry to reconcile" |
| 6.2 | High | `commands.functions.ts:28` | `getCommandCapability` unauthenticated; runs privileged full-repo read |
| 8.1 | High | `system.tsx:541-542` | System page still says the cockpit never writes to the Ivy repository |
| 3.3 | Medium | `queue-core.ts:220-228` | Retry path bypasses the reserved-content guard |
| 3.4 | Medium | `queue-core.ts:196-201` | One malformed contract blocks all follow-up creation |
| 6.3 | Medium | `workspace.functions.ts:85`, `useWorkspace.ts:78` | Full-repo snapshots every 60s, amplifiable by any authenticated user |
| 6.4 | Low | `commands.ts:431-436` | 32-bit idempotency hash; collision is a permanent dead end |
| 6.5 | Low | `queue-core.ts:231` | `created_by: tom` hardcoded despite a plural operator allowlist |
| 6.6 | Low | `package.json` | No `test` script; 25 new tests never run by default |
| 8.2 | Low | `.gitignore` | New ignore rule does not cover the already-tracked `.env` |

**Sound, no findings:** operator allowlist (§1), repository allowlist (§4 layers, §2), server-side operation bounds and the write-path allowlist (§3), source-revision checking (§4), atomic writes and idempotent replay (§5), and the treatment of worker completion versus independent verification (§7).

**Overall.** The queue core is careful work — the write allowlist, the fingerprinted receipts, the non-force ref update, and the receipt-derived status reconciliation are all genuinely load-bearing, and the tests exercise the races. The defects cluster in the two places the tests do not reach: the `submitCommand` orchestration layer, and the static UI copy. Findings 3.1, 3.2 and 8.1 are all the same class — the server was rewritten to do less than the UI already promised, and three strings were not brought back into line. They are cheap to fix and each one, left in, tells the operator something untrue about what the cockpit did.
