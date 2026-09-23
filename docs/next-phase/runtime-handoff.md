# Current build — scanner and harness repairs ready for review, 23 September 2026

Tom authorized the two-day Ivy build to begin with local-work visibility and
harness correctness. Two independent branches start from production main; the
existing acceptance/Paperclip stack is not used as their release dependency.

- [Draft PR #22](https://github.com/tompulsarlabs/ivy/pull/22),
  `codex/ivy-scanner-reliability`, head `173a9e6`: discovers registered worktrees,
  keeps repository-wide and per-checkout unpushed counts, refreshes unchanged
  snapshots after six hours, refuses failed reads, and publishes bot-authored
  snapshots from an invocation-owned temporary clone. No human index, branch or
  unpushed commits are staged/rebased/pushed. Adds preview and stable-main-only
  launchd install/status tooling. Twenty-three deterministic cases pass locally
  and in Python 3.11/3.14 CI. The read-only Mac scan observed 20 checkouts,
  including 3 Ivy checkouts, before creating the second repair worktree; the
  payload contained no absolute paths. Live publication/install have not run.
- [Draft PR #23](https://github.com/tompulsarlabs/ivy/pull/23),
  `codex/ivy-harness-settings`, head `e23037c`: applies Claude/Codex effort flags,
  validates before task claim or project clone, captures requested settings and
  source/config/runner/prompt identities, and adds a strictly inspect-only route
  preview. Removes Haiku 4.5's unsupported effort field without changing model
  selection. Sixteen deterministic cases pass locally and in Python 3.11/3.14
  CI, including a real fixed local program that checks argv/environment and
  returns a fixture report. No evaluated model was called; effective backend
  model/effort stay unknown and context/usage coverage remains incomplete.

Four implementation commits use Tom's verified noreply attribution. This handoff
and its engineering ledger update are bot-authored bookkeeping. New inventories
were also placed in `~/Build/ivy/evals/` without replacing its pre-existing files.
The existing runner suite, dispatch lint (29 contracts), memory lint (21 pages),
shell syntax where changed and diff checks pass. CI results were read at the
listed branch heads. No independent model-quality or semantic acceptance pass
is claimed. Main checkout's existing untracked documents are preserved.

Next: review the two repair PRs. After landing the scanner, update the stable
main checkout, preview, install, publish one scan and verify its remote snapshot
and next scheduled run. After landing the harness repair, the existing runner
loads its synchronized script/config; prove one bounded task before broader
model routing. Applying previously ignored effort can alter output and usage.
Full structured event/context capture, disabled new-model profiles and comparative
model evaluation remain follow-up work. CLI help/version inspection found Claude
Code 2.1.277; current upstream docs require 2.1.280 for Opus 5.5. No upgrade ran.

Both PRs remain draft. Production runner/scanner code and model routing are
unchanged, the scanner job is still unloaded, no paid resources were created,
and no provider auth was read/copied. PRs #18/#19/#20 remain unmerged. The board,
Mac connection, real-agent acceptance and Milestone A retain their prior limits.

A conservative 3,600-second allocation for this single-primary implementation,
local checks and closeout is appended to the engineering ledger: cumulative
**27,300 seconds**. This is estimated engineering bookkeeping, not measured
provider billing or a renewed runtime/model-evaluation grant. Historical runtime
attempts, exhausted grants, failures and original timestamps are retained.

## Previous checkpoint — retained

# Current assessment — model routing and harness, 23 September 2026

Tom requested reassessment for Opus 5.5, GPT-6 Sol and GPT-6 Luna, independently
of the coordinator choice. [The review](model-routing-review-20260923.md) records
source checks, proposed routing, a staged patch and evaluation cases. Confirmed
without worker execution: the current launcher's Claude frontier/workhorse
commands are identical because configured effort is ignored. The runner clone
and main checkout contain the same launcher bytes; neither was modified.

Recommendation: fix effective configuration/capture first, register disabled
candidate profiles, then compare bounded tasks before promoting one class.
Sol implementation, Luna bounded support and Opus difficult design/review are
hypotheses, not evaluated wins. Keep task acceptance and routing independent of
Paperclip; do not introduce a second dispatcher or subscription-to-API fallback.
No model/authentication probe, judge, runtime worker or production edit occurred.
CLI help/version and one pure-function launcher check were run. Prior test
results are not rerun evidence for a new model. Milestone A remains unpassed.

The existing ledger retains 22,800 seconds and adds a conservative 900-second
single-primary assessment/documentation/closeout allocation: **23,700 seconds**.
Historical runtime grants, attempts, original timestamps and failures remain
unchanged. Hosting checkout/payment and Mac connection remain at the last
recorded unverified state; this assessment did not operate Railway.

## Previous checkpoint — retained

# Current direction — nontechnical users must be able to ship and operate

22 September 2026. Tom supplied a product-factory workflow screenshot and made
the requirement explicit: Ivy must put the technical delivery process underneath
a product that lets nontechnical people achieve technical-operator impact.
The [existing plan](hybrid-worker-plan.md#product-requirement-technical-capability-accessible-to-nontechnical-people)
now defines the visible journey, internal responsibilities and six proposed
acceptance cases. These are requirements, not evaluated behavior. Paperclip
remains the internal coordination foundation; this does not authorize a production
agent change or broad demo redesign. Evaluate Jev after this release against a
representative journey once the product is identified.

Hosting state correction: Tom has signed in and Railway reports a verified Trial
account. Its account screen lists 0.5 GB RAM/service despite public trial docs
listing 1 GB. The local app used 743.1 MiB in one sample. Tom authorized moving
to Hobby; checkout is open at $5 upfront with payment details still needed at the
last observation. Subscription completion is unverified. No service was deployed
or budget control configured. Next: complete payment directly in Railway, set
the authorized $30 alert/$40 compute cap and perform hosted release checks.

This documentation/closeout stage appends a conservative 300 seconds to the
existing engineering ledger: cumulative **22,800 seconds**. Historical runtime
attempts and grants are unchanged. No new runtime tests, model calls or judge
calls occurred. The last code head's 121 tests and Python 3.11/3.14 CI passed;
this update changes documentation and bookkeeping only. Milestone A remains
unpassed; the Mac connection and public deployment remain unverified.

## Previous checkpoint — retained

# Current handoff — board built and locally rehearsed; hosting login pending

22 September 2026. Tom approved planning/building the always-on Paperclip board
and Mac-first execution direction after the $30 alert/$40 compute cap proposal.
Work remains on `codex/ivy-acceptance-scaffold`, restored at
`/tmp/ivy-paperclip-release`, in the same stacked draft PR #20. No PR merged;
main checkout, production dispatch, Cockpit and tomgreen.ai demo are unchanged.

Built a pinned 2026.916.1 wrapper with startup checks for authenticated mode,
canonical HTTPS origin, persistent storage, app secrets and inactive scheduler.
Live debugging fixed missing CLI bootstrap config and differing auth/CSRF origin
variables. All failures remain in
[evidence](evidence/paperclip-board-build-20260922.json); private fixture accounts,
secrets, logs and backups are in `/tmp/ivy-paperclip-release-proof-20260922`.
This is a separate board rehearsal, not a replacement historical runtime store.

The final real image passed internal HTTP owner signup/bootstrap, anonymous and
unrelated-user refusal, signup lock, task and owner-session persistence after
restart, and database/app-data restoration into separate volumes. Agent run
inventory was empty. All nine rehearsal containers are stopped; their containers,
images and volumes are retained. Only `colima-ivy-acceptance` was used and its VM
was returned to stopped. The host loopback HTTP forward failed; public TLS and
interactive browser login have not been tested. Attachment round-trip and
scheduled provider backup restoration remain unverified.

All **121 deterministic tests pass** locally. These are deployment/software
controls, not model-quality evaluation. The native SSH environment configuration
renderer is built and tested; **the Mac is not connected**. The
[hybrid plan](hybrid-worker-plan.md) names private networking, dedicated account,
scoped SSH identity, isolated model authentication and interrupted-run evidence
as remaining work. No Mac account, SSH service or tunnel was installed. No
subscription authentication was read, copied or mounted.

Railway is open at its login screen. Tom must sign in to the intended account;
no billable service exists yet. Next, establish the dedicated workspace's $30
alert/$40 compute cap, provision the board/database within that allowance, and
run the [hosted checks](../../deploy/paperclip/README.md). Hosting approval does
not authorize model APIs, cloud workers, paid networking or production migration.
No production URL is available. Keep signup locked after Tom claims ownership.

The original 18,900-second cumulative debit is retained and this single-primary
build/rehearsal/closeout adds a conservative 3,600 seconds: **22,500 seconds**.
This is engineering bookkeeping, not the ChatGPT subscription or hosting limit.
Historical timestamps, eight attempts, 480 reserved seconds, failures and exhausted
runtime grants are unchanged. No evaluated model or judge calls occurred.
**Milestone A is not passed.** Its hard lifecycle and real-agent/neutral-case
assessment gaps remain; this board rehearsal does not close them.

## Previous checkpoint — retained

# Current handoff — private Paperclip release prepared, hosting decision pending

22 September 2026. Tom asked to ship Paperclip and evaluate the linked workflow
article, then selected always-on private web hosting and asked its costs.
Worktree `/tmp/ivy-paperclip-release` restores the same
`codex/ivy-acceptance-scaffold` branch and stacked draft PR #20. PRs #18/#19/#20
remain unmerged; no production dispatch, Cockpit, demo or main-checkout edits.

The [release configuration](../../deploy/paperclip/README.md) proposes Railway,
a private authenticated board, PostgreSQL and persistent storage. Estimated
$20–40/month before tax; proposed $30 alert and $40 compute shutdown limit in a
separate workspace. No hosting purchase, model API spending or migration has been
approved. No billable resources were created. There is no deployed Paperclip URL.

The official Paperclip 2026.916.1 image is pinned by its public OCI index digest.
Source settings and registry availability were checked; this image has not been
run. Existing integration controls apply to 2026.831.1 only. Authenticated login,
restart persistence, a backup restore and current-version worker controls must
pass before production use. The first release is a manual company/task board;
Mac/remote autonomous worker authentication and dispatch are not implemented by
this configuration. No subscription authentication was copied or read.

The bridge now explicitly closes SQLite connections while preserving commit and
rollback behavior. All **102 deterministic tests pass** on local Python 3.14 with
resource warnings enabled and none observed. CI on the pushed head is recorded
by GitHub; this note does not pre-award it a pass. Configuration JSON parses and
its used fields were checked against the provider schema; no full schema
validator or hosted runtime validation ran.

The [workflow evaluation](workflow-evaluation-20260922.md) recommends GitHub for
versioned source/evidence, Paperclip for coordination after validation, Ivy for
acceptance policy, and optional Notion for human-authored context. One dispatcher
must own each task class. A representative completed review was checked directly
against GitHub: its report exists on pinned Ivy main, nine linked files exist
and cited lines are in range at the recorded PR head, and CI succeeded on that
head. The original review did not pin its source commit; historical correctness
and semantic acceptance remain unverified. This was a read-only reassessment,
not a new Paperclip campaign. See [evidence](evidence/contract-readiness-20260922/assessment.json).

**Private evidence availability changed since the previous checkpoint:**
`/tmp/ivy-runtime-proof-20260905` is absent on this host, and the September 10
Paperclip directory contains only an install directory. Original campaign data
and logs cannot currently be revalidated. Committed portable observations,
including every recorded failure, remain intact. Neither store was recreated,
replaced or reset. Earlier statements below describe their historical availability.

The same ledger retains 16,500 seconds and appends a conservative 2,400-second
single-primary preparation/closeout allocation: cumulative **18,900 seconds**.
This is engineering bookkeeping, not an account limit. Historical Docker grants,
eight attempts, 480 reserved seconds and failures are unchanged. No Docker launch,
evaluated model, judge or paid-provider call occurred. **Milestone A is not passed.**

Next: obtain the recurring hosting-spend decision, connect the chosen hosting
account, provision the reviewed configuration, run its live release checks, and
record the actual URL. Keep failed checks and source evidence. A real-agent
integration still requires isolated authentication and explicit execution scope.

## Previous checkpoint — retained

# Current handoff — Paperclip isolated integration slice verified

10 September 2026. Tom approved the proposed integration with “I'm aligned,
let's go.” Work is on `/tmp/ivy-paperclip-integration`, the existing
`codex/ivy-acceptance-scaffold` branch and stacked draft PR #20. The previous
worktree path was missing/prunable, so this worktree restores the same branch.
Keep PRs #18, #19 and #20 unmerged.

Paperclip `2026.831.1` ran real Python fixture processes in a separate local
instance. The bridge seals captured output, checks task/run ownership and the
fixed fixture, and publishes through a separate reviewer identity. Valid
output and duplicate delivery finish through review; false completion and a
rehashed tampered copy remain in review. Cancellation plus pause leaves the
observed worker PID absent and refuses a later completion claim. Paperclip can
create a retry record after cancellation: the final control retained two run
records but only one worker process. This is not a daemon/descendant lifetime
or distributed exactly-once guarantee.

The final five-case campaign passed, including under Python `-O`; the complete
software suite has **102 passing deterministic tests**. These are integration
and software controls, not model or semantic acceptance. The supervisor relays
the completion claim and performs assessment; reviewer no-op runs establish
Paperclip run context. Workers share the operator's OS trust boundary.

Read [the integration notes](paperclip-integration.md) and
[portable evidence](evidence/paperclip-integration-20260910/report.json).
All eleven development campaigns, including six failed campaigns, and the first
failed PostgreSQL startup remain under `/tmp/ivy-paperclip-pilot-20260910`.
Aggregate inventory: 58 Paperclip run records, 51 observed process PIDs; all
60 pilot agents paused, no queued/running work and no active pilot agent keys.
The final transport fixtures are copied with digests; raw instance data and
logs remain private. The data directory is not the original Docker store. The pilot server and
embedded database were stopped; both listeners and fixture process inventory
were confirmed absent.

The same engineering ledger retains 14,100 prior allocated seconds and adds
2,400 for this single-primary integration and closeout: cumulative **16,500**.
This is bookkeeping for the newly approved system-development scope, not an
account limit, provider cost or renewed runtime grant. The historical eight
Docker attempts, 480 reserved seconds, failures and exhausted grants are
unchanged. No Docker launch, model, judge or paid-provider call occurred.

Continue the adoption evaluation with one representative Ivy contract and its
independent check, making recovery policy explicit. No production dispatch,
Cockpit, live demo or unrelated main-checkout files were changed. Native Runner
bundle compatibility, isolated real-agent auth, effective harness metadata,
neutral benchmark approval, independent semantic assessment, buyer validation
and hard whole-lifecycle timing remain unverified. **Milestone A is not passed.**

## Previous checkpoint — retained

# Current handoff — High offline evidence/resource build complete

6 September 2026. Built on the Ultra design at `89b1f91` after reading the terminal
checkpoint. Tom authorized this implementation with “Ok build with high”. Work is
on `/tmp/ivy-acceptance-scaffold`, branch `codex/ivy-acceptance-scaffold`, stacked
draft PR #20. Keep PRs #18, #19 and #20 unmerged. Main's unrelated scan work and
Cockpit briefs were not edited.

## Delivered and checked

- `assess-probe` parses bounded, strict recorded capture bytes and recognizes the
  exact historical fixed-program digest. It separates artifact integrity, execution,
  observed assertions, natural completion, expected stop control and benchmark state.
- `probe` uses its predeclared expectation and returns assessment exit 0/1/2 for
  pass/fail/unverified. Invalid cancellation options fail before setup or reservation.
  `verify-probe` is explicitly integrity-only. `report` exits 0 for successful rendering;
  its status counts remain the assessment result, not an implied acceptance pass.
- Versioned exclusive resource records distinguish reported, estimated and unknown
  values. Declared missing scopes remain unknown; overlapping inclusive totals,
  duplicate scope records and mismatched recorded durations are rejected.
- Offline JSON/Markdown reports expose allowlisted results and hashes, protect input
  stores, refuse overwrites and have a detached canonical-JSON digest.
- **82 deterministic tests pass locally**, including [EQ01–EQ12](../../evals/evidence-quality.json).
  They cover known failures with missing evidence, malformed/nested input, numeric
  boundaries, capture framing, source binding, command exits and read-only replay.
  Python 3.11/3.14 PR CI is checked after pushing; see the checks on the resulting head.

The [portable report](evidence/offline-report-20260906/report.md) reassesses the real
historical completion, cancellation and deadline receipts. All three expected
controls pass; only the completion receipt passes natural completion. No model
benchmark pass is awarded. The [replay record](evidence/offline-report-20260906/replay-controls.json)
records CLI results, two identical renders and a before/after snapshot of all 120
original store files, including the ledger. Every source byte remained unchanged.

Report canonical digest:
`6cc0949cc41b6d436baf9a420ea3aea57ad4410fa175e71ad8278468adf9ef15`.
Private manifest and copied resource observations are under
`/tmp/ivy-offline-evidence-20260906-high/`; final output is `release-report/`, with
`release-report-reproduced/` as the matching second render. Originals remain in
`/tmp/ivy-runtime-proof-20260905`. No Docker command, new container, evaluated model,
judge, API call or credential read was needed for this build.

The report's 11,700 engineering seconds are the prior design checkpoint allocation,
not this build's final cumulative total or measured inference time. Current effort
is appended in [resource-ledger.json](resource-ledger.json); prior debits, eight
runtime attempts, 480 reserved seconds and exhausted runtime grants are preserved.
The High build uses one primary lane and a conservative 2,400-second allocation
including closeout, within its 3,600-second checkpoint. Unknown tokens and billing
remain unknown. No cost-per-accepted-task or savings claim is supported.

## Next product proof and remaining gaps

The customer direction remains teams shipping coding or internal-workflow agents.
The next useful proof is an independently assessed before/after agent change on a
real release owner's representative cases, with measured whole-run usage and an
explicit acceptance threshold. A routing service or UI expansion is not required
to establish that value. Follow [the design](cost-quality-design.md) and
[ADR 0002](../adr/0002-evidence-and-resource-report.md) for the fixed contracts.

Real-agent authentication, effective harness metadata, an approved neutral benchmark,
independent semantic assessment, actual model comparison and buyer validation remain
unfinished. Milestone A is not passed. This build does not authorize the deferred
model/API integration or renew any runtime grant. Hard whole-lifecycle bounds and
daemon-side build termination also remain incomplete; offline reporting does not
repair them. Hashes assume a trusted local supervisor and are not signed attestations.

The separate housekeeping work retains ownership of operational-agent instructions
and its shared inventory. This additive eval file does not silently replace that
branch or claim all operational agents have now been evaluated.

## Prior runtime validation checkpoint — retained evidence

# Runtime validation passed for completion, cancellation and deadline shutdown

6 September 2026. Tom approved preflight before reservation and a bounded validation
session instead of per-launch approvals. System development remains credential-free;
real-agent authentication and paid integration are deferred.

The CLI now checks eligibility without reserving, then checks evidence-store writes,
the requested Docker context, daemon access and the pinned local image through the
same subprocess path as execution. Setup commands share a 15-second deadline and
write separate preflight records. Preparation repeats image checks, and reserve
rechecks capacity after preflight. Setup readiness does not guarantee a later build.

A one-use 600-second session allowed at most three fresh probes, preserving all
prior grants, five attempts, original start, limits and debit. Results:

| Attempt | Result | Whole command observed | Termination | Capture |
|---|---|---:|---|---|
| `validation-complete-20260906` | completed | 0.503 s | confirmed | complete |
| `validation-cancel-20260906` | canceled | 2.428 s | confirmed | partial |
| `validation-deadline-20260906` | timed out | 10.190 s | confirmed | partial |

All three receipts verify. Completed-worker fixture hashes match selected inputs;
non-root/read-only/no-network/no-host-mount settings remain intact. Tampering with
a copy of completed capture is rejected and its original still verifies. Successful
preflight left ledger bytes unchanged. A real sandbox-denied preflight recorded the
setup error without reserving an attempt or changing ledger bytes. A fourth session
reservation was refused with identical ledger bytes. Final dedicated-context
inventory: seven stopped containers, none running.

**59 deterministic tests pass locally.** The existing ledger now retains eight
attempts and 480 reserved seconds, with no unresolved reservation. All historical
failures remain. Private originals and tampered copy remain in the same store;
portable observations are in [the validation report](evidence/runtime-validation-20260906.json).

Natural completion is now verified. Remaining limitations: interrupted daemon-side
build shutdown, live failures after build submission, measured builder network
behavior, and a hard whole-lifecycle wall ceiling. The observed 10.190-second deadline
command includes shutdown; it is not proof of a 10-second end-to-end guarantee.
Real-agent authentication, effective harness metadata and approved neutral-case
assessment remain deferred. No model/judge call occurred; Milestone A has not passed.

The prior 9,300-second engineering debit is preserved; the remaining 600 seconds
are allocated after the prior closeout boundary (08:13:27 through 08:23:27 UTC),
including this session's verification, docs, push and CI closeout. Initial reading
at 08:12:18 falls in the prior allocation, not a second charge. Cumulative allocated
debit is 9,900 seconds, with no remaining engineering allowance or session probes.
The earlier pending per-attempt question is superseded by Tom's session approval.
Keep branch `codex/ivy-acceptance-scaffold` and stacked draft PR #20. Production
dispatch, Cockpit and the unrelated checkout were not changed.

## Previous checkpoint — retained history

# System-only continuation: preparation failures recorded; completion still pending

6 September 2026. Tom clarified that this is system development and approved
continuing after the proposal to use the remaining 25 engineering minutes for one
repair iteration and one completion probe. Authentication and paid API integration
are deferred; no API key is required for this system work. This checkpoint
supersedes the current status below while preserving all historical results.

Repair iteration 3 records preparation phases before submitting daemon operations.
Failures before build submission now retain an explicit failure record and close
only the reservation for which no workload was submitted. Build failure, timeout
or interruption retains an unresolved reservation because stopping a client does
not confirm daemon-side shutdown. A lost create response triggers owned-container
inspection/shutdown. Final Docker-client cleanup uses the existing shutdown grace;
a cleanup timeout is retained in the receipt instead of preventing its persistence.

The original runtime ledger received a separate one-use completion authorization:
one fresh attempt in 600 seconds, preserving its original start, limits, first four
attempts and earlier three-probe authorization. `completion-20260906-1` failed while
inspecting the pinned local image: the tool sandbox denied Docker socket access.
No image build or container was submitted. Its consumed 90-second reservation and
failure remain recorded with `termination_basis: no_workload_submitted`; this is
not inspected-container termination or completed-worker evidence. Five attempts
and 290 reserved seconds are now retained; none is unresolved. No attempt ID was
reused. A further CLI reservation was refused with byte-identical ledger and no
new attempt directory.

A separate explicitly escalated, read-only pinned-image inspection succeeded.
This establishes the access path for a future probe, not a successful completion.
An asynchronous request asks Tom to approve one additional fresh completion attempt
within the same engineering allowance. No answer has been recorded at this
checkpoint; do not treat the request or successful read-only inspection as a grant.
Before any future reservation, verify read-only Docker access through the same
approved tool permission boundary that will execute the probe.

**54 deterministic tests pass.** New cases cover preserved authorization history,
one-use/full-window/aggregate caps, missing-base failure, interrupted build
uncertainty, lost create responses, and receipt retention when client cleanup
expires. The actual sandbox-denied preparation independently exercised the new
pre-build failure path. These tests do not establish live interrupted builder
shutdown or a hard end-to-end wall ceiling. Filesystem operations and daemon build
lifetime remain outside that claim. Natural completion remains unverified.

Milestone A has **not passed**. No evaluated model or judge call occurred. Real-agent
authentication, effective harness metadata and approved neutral-case semantic
assessment are intentionally deferred, not prerequisites for ordinary system work.
Keep the same draft PR #20 stacked on `codex/ivy-next-phase-design`, the existing
worktree/branch, and Docker context `colima-ivy-acceptance`. Production dispatch,
Cockpit and the unrelated checkout were not changed.

Private originals remain in `/tmp/ivy-runtime-proof-20260905`, including the saved
pre-continuation ledger, command/failure evidence and refusal control. The portable
[completion report](evidence/runtime-completion-20260906.json) contains only
allowlisted observations. The resource ledger preserves 8,400 prior debit seconds
and allocates 900 seconds for this single-agent continuation and closeout through
08:13:27 UTC; 600 seconds remain, not a new repair/probe grant. Work beyond that
allocation must debit the same remaining allowance. No timestamps or runtime store
were reset.

## Prior checkpoint — retained history

# Live cancellation and deadline verified; model integration still blocked

Latest checkpoint, 5 September 2026, supersedes the historical sections below.
Tom approved the proposed additive extension: 45 aggregate engineering minutes,
20 minutes for at most three fresh runtime probes, and the one remaining repair
iteration. The original ledger, start time, limits and consumed failed attempt
were preserved. No API spending was authorized by the subscription upgrade.

Repair iteration 2 adds an explicit, one-use local authorization record and a
shared preparation/run command deadline. It also disables Docker local-log
compression, after the first new probe exposed an incompatible `max-file=1`
configuration. That failed probe remains visible; it was not retried under its ID.

| New attempt | Actual result | Container stopped | Capture |
|---|---|---|---|
| `extension-complete-1` | Image built; Docker start failed on log configuration | Confirmed | Complete error stream, not worker success |
| `extension-cancel-2` | Worker ran; explicit cancellation | Confirmed | Partial |
| `extension-deadline-3` | Worker ran; deadline shutdown | Confirmed | Partial |

All three saved receipts independently verify. Actual receipt-copy tampering,
wrong-owner inspection and refusal of a fourth reservation were checked without
altering originals. There are four consumed attempts in total, with 200 seconds
reserved, no unresolved final-container reservation and no completed worker run.
The three-probe extension is spent; do not renew it or create a replacement store.
Both repair iterations are now used. The engineering ledger records the separate
additive allowance and continuation debit; handoff is never a reset.

The full deterministic suite passes **45 tests**. The read-only plan still returns
`execution_ready: false`. No real agent, model or judge attempt ran. Milestone A is
**not passed**, even though the running-container shutdown controls now work.

Remaining verification: natural completion with the corrected logging option;
daemon-side build cancellation and failures before final-container creation;
hard whole-lifecycle timing; isolated real-agent authentication, effective harness
metadata, approved neutral case and independent semantic assessment. The shared
deadline clamps Docker preparation commands and the run loop, with a separate
15-second shutdown grace; filesystem work, daemon build lifetime and a final
five-second client wait prevent claiming a hard end-to-end wall ceiling.

Host Codex 0.153.0 still reports ChatGPT login. Official documentation supports
subscription CLI authentication, but no attempt-scoped subscription credential
broker was established here. Neither a host CLI working directory nor ignoring
user config establishes the intended isolation. Do not copy/mount host auth into
the worker or reinterpret a Pro upgrade as API-key billing authorization.
See [authentication](https://learn.chatgpt.com/docs/auth) and
[non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

Private originals remain in `/tmp/ivy-runtime-proof-20260905`; portable, allowlisted
observations are in [the extension summary](evidence/runtime-extension-20260905.json).
No raw Docker inspection, provider credentials or machine/account paths belong in
the public evidence summary. Existing branch and stacked draft PR #20 are preserved.

## Previous recovery checkpoint (retained history)

Follow-up on 5 September 2026, after Tom asked to solve the outstanding gaps:
`recover-probe` confirmed that the original attempt-owned container is stopped
and closed its reservation. The consumed `isolation-1` attempt is retained with
`execution_error`; the ledger's original start time and limits are unchanged.
A real Docker inspection rejected a deliberately mismatched owner. A fresh CLI
probe returned `attempt or execution time budget exhausted` before creating a
new attempt; the ledger was unchanged by that refusal.

Private evidence: `recovery-controls-20260905.json` in the original store and
`isolation-1/stop-1788631255903549000.json`. These are observed recovery/ownership/
budget controls, not successful worker execution. Image build, success/cancel/
deadline paths and real agent execution are still unverified.

A proposed extension awaits Tom's answer: up to 45 additional engineering minutes,
a 20-minute runtime window for at most three new probes, the one remaining repair
iteration, and all prior attempts/debits retained. No runtime allowance was changed
and no paid model call was authorized. The recovery diagnostics were authorized
by this follow-up; they do not reopen the expired implementation budget.

## Previous High checkpoint (retained history)

High continuation, 5 September 2026: one repair iteration, 36 deterministic tests
passing. The exact original copy failure was reproduced and retained:
`Error response from daemon: container rootfs is marked read-only`.
The before/after container inspection confirmed matching ownership and created,
stopped state. The adapter now packages verified inputs through a fixed FROM/COPY
image context and records base/derived identities while preserving worker isolation.
This replacement has not been built or executed on real Docker.

The recovery helper waited approximately 390 seconds for escalation approval and
was interrupted at the budget checkpoint. No recovery result was obtained; the
original reservation remains unconfirmed. No ownership-rejection control or fresh
probe executed. The unchanged ledger's one-hour elapsed window has expired, so a
fresh attempt would also be refused after recovery. Do not create another store,
change timestamps or raise limits to bypass either condition.

Actual completion, explicit cancellation of a running container, deadline shutdown,
builder availability/offline behavior and runtime receipt verification remain
unverified. Synthetic receipt controls do reject tampering/missing evidence and
preserve incomplete states. Preparation commands have separate timeouts outside
the run-phase `--deadline`; whole-operation boundedness is not established.
No evaluated agent or judge calls occurred; milestone A remains not passed.

See [engineering review](runtime-engineering-review.md) and the portable
[sanitized evidence summary](evidence/runtime-debug-20260905.json). The original
failed attempt and added reproduction record remain in the private store. The
resource ledger carries the original debit plus this continuation; no budget reset.

## Original Extra High handoff (retained history)

5 September 2026. Worktree `/tmp/ivy-acceptance-scaffold`, branch
`codex/ivy-acceptance-scaffold`, stacked draft PR 20. Do not modify the unrelated
untracked correctness document in `/Users/tom/Build/ivy`.

## Implemented and checked

- Durable comparison-bound ledger with atomic replacement/fsync, exclusive OS lock,
  consumed IDs, worst-case time reservations and restart blocking until an
  attempt-owned container is confirmed stopped.
- Recompile the saved preview and check every copied byte against its snapshot.
  Pack only the selected fixture and instruction bundle; no grader files.
- Fixed Python runtime probe with a digest-pinned image, no credentials/network/host
  mounts, non-root user, read-only root, capability drop and resource limits.
- Supervisor stdout/stderr capture, container inspect records, bounded cancellation,
  immutable attempt directories and hash verification commands.
- Independent bad citation control. Passing citations still leave semantic status
  unverified; this module cannot award a benchmark pass.

`python3 -B -m unittest discover -s tests -v` passes **27 deterministic tests**.
Actual runtime preparation has **not** passed. No agent/model/judge calls occurred.
The new adapter is explicitly an infrastructure probe, not the real harness.

## Exact first failure

```sh
python3 -B -m ivy_acceptance probe examples/acceptance/preview.json \
  --store /tmp/ivy-runtime-proof-20260905 \
  --image python@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea \
  --context colima-ivy-acceptance --attempt isolation-1
```

Expected: copy only prepared bytes, run the probe, confirm stopped, verify receipt.
Observed: `docker cp - ivy-360f57ca484a8b56c935b14b87d1da52:/` returned exit 1
before start. The current CLI does not include subprocess stderr in its error output;
capture that safely when reproducing. Read-only-root materialization is the suspected
cause, not yet verified. The consumed reservation remains unconfirmed in
`/tmp/ivy-runtime-proof-20260905/ledger.json`; preparation metadata is in `isolation-1/`.

The container should be in created state; inspect ownership and status rather than
assuming. Use `recover-probe --store /tmp/ivy-runtime-proof-20260905 --attempt isolation-1`
to close the reservation only after confirming it stopped. Use a **fresh** attempt ID
for the next actual test. Never delete the ledger to get a passing result.

## Debugging scope and order

Use Astra High as Tom requested. At most **two repair iterations**, charged to the
remaining milestone-A time in `resource-ledger.json` (do not restart the two-hour cap).

1. Reproduce the copy failure; retain stderr and lifecycle evidence. Correct input
   preparation while preserving the final worker's read-only filesystem and zero
   host mounts. One possible small solution is an offline, COPY-only derived image
   built from the pinned base and verified tar bytes, recording both image identities.
   Do not loosen the worker's filesystem policy simply to make copying succeed.
2. Exercise complete, explicit cancel and deadline paths against real Docker.
   Confirm the container, not only the Docker client, stopped. Test tampering against
   the receipt, restart recovery and ownership; do not treat missing capture as pass.
   Retain failed attempts and label partial capture. Verify deterministic bad-output
   grading separately from actual runtime results.
3. Run the full deterministic suite after the fix. Save a portable synthetic evidence
   bundle/report with scope and limitations; review files for machine/account paths
   before adding artifacts to this public repo. Update PR 20's final scope and checks.

## Runtime installation and authentication

Installed with Homebrew: Colima 0.10.3, Docker CLI 29.7.2, Lima 2.2.0. Dedicated
Colima profile `ivy-acceptance` is running, 2 CPU / 2 GiB, 12 GiB disks, host mounts
disabled, SSH config integration disabled, and no change to the default Docker
context. Use `docker --context colima-ivy-acceptance ...`. Installation/start and
Docker calls require the local tool's filesystem/network escalation. They were
approved in the Extra High stage. No automatic service was enabled.

Host Codex 0.153.0 reports a ChatGPT subscription login. Its auth file was not read,
copied or mounted. No `OPENAI_API_KEY` or `CODEX_API_KEY` is present. The design excludes
provider-wide credentials in the worker. An asynchronous question asks Tom whether
he will provision a dedicated API key locally and authorize at most $5 for the proof,
or defer model authentication and keep this as runtime-only proof. No answer was
received at this checkpoint. Never ask him to paste a key in chat. A $5 answer alone
is not an implemented enforceable request/cost limit.

The existing-tool spike has not started: Promptfoo's Codex provider supports saved
CLI auth or API credentials, but does not remove the worker credential boundary.
Do not call its absence an incompatibility or silently authorize a second execution
engine. Resolve intentional authentication before spending the 30-minute wrapper
sub-cap. A suitable documented API proxy exists in OpenAI's Codex GitHub Action,
but it requires an API key and has not been integrated or tested here.

Milestone A still needs a real neutral agent case with effective harness/model/tool
configuration, owner approval binding and actual evidence. Runtime-only tests do not
pass that gate. Do not proceed to six cases or a broad product build without the
named external release owner/pending change/timed workaround gate, or Tom's explicit
internal-dogfood extension.

Sources checked for the authentication decision:
[Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode),
[Codex Action](https://github.com/openai/codex-action),
[Promptfoo Codex provider](https://www.promptfoo.dev/docs/providers/openai-codex-sdk/).
