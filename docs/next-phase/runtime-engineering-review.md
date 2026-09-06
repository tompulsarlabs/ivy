# Preparation failure and client cleanup review — 6 September 2026

The system-only continuation fixes two concrete evidence gaps. A failed image
inspection previously left a reservation unresolved even though no workload could
have been submitted. Preparation now records its phase before each daemon mutation
and persists a terminal failure outcome. Only failures before build submission can
close on the basis of no submitted workload. An interrupted or failed build remains
unconfirmed; after create submission, owned-container inspection is required.

The final client wait previously added up to five seconds outside the shutdown
grace and could throw before receipt/ledger persistence. It now uses the remaining
shutdown grace and records client cleanup errors while retaining container shutdown
evidence. This reduces one timing gap; filesystem work and daemon-side build
lifetime still prevent a hard whole-lifecycle ceiling claim.

The approved single completion probe is recorded as an additional one-use local
authorization, separate from the consumed three-probe extension. Its prior ledger
hash, start, 600-second window and one-attempt limit survive restart. Original
start/limits, failed attempts and the earlier grant remain unchanged. This remains
a trusted-operator assertion, not signed approval or provider billing control.

Live result: `completion-20260906-1` failed during image inspection because the
sandbox denied access to the dedicated Docker socket. No build/container was
submitted. The new phase-aware failure path retained its error and consumed debit
and safely closed the never-submitted workload. Five attempts and 290 reserved
seconds remain; natural completion is still unverified. An additional reservation
was refused without changing ledger bytes. A separate escalated read-only image
inspection succeeded; another runtime attempt requires the pending explicit grant.

Validation: 54 deterministic tests pass, including nine additional tests for the
completion grant, preparation failure/interruption/lost-create response, and
expired client cleanup. These are software controls; the live sandbox-denied
preparation supplies distinct runtime evidence. No model-quality claim is made.
No real agent or judge ran, and Milestone A remains not passed. Authentication and
neutral-case model assessment are deferred during system development.

Remaining: actual natural completion; interrupted daemon-side build shutdown;
live post-submission preparation failures; hard end-to-end timing and measured
builder network behavior. See the current runtime handoff, resource ledger and
[evidence](evidence/runtime-completion-20260906.json). Production dispatch and
Cockpit were not changed. PR #20 stays a stacked draft.

## Previous engineering review — retained history

# Runtime preparation engineering review

## Authorized extension review — current result

5 September 2026, after Tom approved the proposed bounded extension. This section
supersedes the historical review below, whose failed attempts and prior conclusions
are retained. The existing branch and draft PR #20 remain unchanged in identity.

Repair iteration 2 reused the existing ledger and Docker adapter. An explicit
one-use local authorization record carries the previous ledger hash and allows
three fresh probes within 1,200 seconds; original start, rows and count/reserved-time
limits remain unchanged. It is a trusted-operator assertion, not signed approval.
Preparation commands and the worker loop share one monotonic deadline. Docker's
local logging compression is disabled after the first probe exposed its conflict
with `max-file=1`. This incremental correction and its failed probe are retained.

Observed outcomes:

- Fixed COPY-only preparation built successfully on real Docker.
- Natural completion probe failed before start on logging configuration; no
  successful completed-worker receipt exists after the correction.
- Explicit cancellation and deadline controls ran the worker and confirmed its
  owned container stopped. Both receipts retain partial capture.
- Four controls on copies of actual receipts rejected raw receipt changes,
  capture changes, missing capture and checksum-valid inconsistent image identity.
- Real wrong-owner inspection rejected; a fourth reservation was refused with
  byte-identical ledger. Original failure/recovery remains retained.
- Post-run inventory found four known stopped containers and no intermediates.
  This snapshot does not prove cancellation of an interrupted daemon-side build.

Primary verification independently ran all three receipt verifiers, the read-only
plan, and **45 deterministic tests**. New independent tests cover inherited build
hooks/volumes, preparation-timeout restart blocking and unreachable shutdown.
Their first run failed from a test-fixture constructor error (`Limits()` without
required arguments); supplying explicit limits fixed the tests. No runtime attempt
was replaced or consumed by this software-test correction.

Remaining release gaps:

1. Natural worker completion with the corrected log settings is unverified; the
   authorized three probes and both repair iterations are consumed.
2. A hard whole-lifecycle wall ceiling is not established. Command timeouts clamp
   preparation/run, and safety shutdown commands share a 15-second grace, but
   filesystem packing/fsync, daemon-side build lifetime and a further five-second
   Docker-client wait are outside that hard-ceiling claim. Pre-create failure can
   retain an unresolved reservation; missing final container is not shutdown proof.
3. No isolated real-agent authentication, frozen effective harness metadata or
   human-approved neutral-case assessment exists. CLI subscription login is verified;
   an attempt-scoped subscription broker is not. No API spending or host credential
   exposure was authorized. Milestone A remains not passed.

OpenAI Docs informed the authentication boundary: subscription CLI sign-in and
API-key billing are separate paths; saved auth is sensitive. The documented
non-interactive invocation does not by itself implement Ivy's worker isolation.
[Authentication](https://learn.chatgpt.com/docs/auth),
[non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

### GSTACK REVIEW REPORT — current

| Review | Status | Remaining |
|---|---|---|
| Engineering continuation / primary independent checks | issues_open | Natural completion, hard lifecycle bound, real-agent integration |
| Astra High runtime repair | bounded work complete | Three probes retained; no additional repair/probe allowance |
| Outside model review | skipped under Codex | No nested Codex call or cross-model agreement claim |

VERDICT: NOT CLEARED for full runtime or milestone-A acceptance. Cancellation,
deadline shutdown and materialization now have real evidence. The remaining
decisions require a revised execution plan and intentional authentication; do not
silently renew the ledger or turn infrastructure results into a benchmark pass.

## Prior review — retained history

5 September 2026. Target: `runtime-handoff.md`, on the existing
`codex/ivy-acceptance-scaffold` branch and stacked draft PR #20.
The user requested gstack/plan-eng-review and Astra High debugging, preserving
the existing budget. This review applies that authorized, bounded scope; it
does not reopen the accepted design or authorize another execution window.

## Step 0: scope challenge

The smallest repair is inside the existing Docker probe: materialize its verified
worker bytes into an image before creating the read-only container. Reuse the
planner, archive function, persistent reservation, capture, stop confirmation and
receipt verification. No new adapter class, authentication system or scheduler is
needed. Implementation and tests fit in three files; documentation and evidence
record the outcome separately. Earlier commit `8f9e95e` introduced the failed
preparation path, so input preparation and its failure evidence receive the
regression coverage.

[Layer 1] Docker already supplies the image build operation. The fixed Dockerfile
contains only FROM and COPY, takes only selected fixture/instruction/probe bytes,
and resolves an already-local pinned base to its content ID. The final worker
retains its filesystem, privilege and network policy.
[Docker COPY reference](https://docs.docker.com/reference/dockerfile/#copy).
The actual legacy builder capability and lack of registry access remain unverified
on this installation; flags alone are not measured network evidence.

## Architecture

**Finding 1, P1, confidence 10/10: copying into the final read-only root fails.**
At `8f9e95e`, `docker_probe.py:103` calls
`self._cmd(["cp", "-", name + ":/"], data=pack_worker(self.files))`
after creating the read-only worker. Real Docker reproduction returned exit 1:
`Error response from daemon: container rootfs is marked read-only`.
Before and after inspection showed the same attempt-owned container in created
state, not running, with no mounts. Repair iteration 1 replaces that operation
with a fixed COPY-only image build and checks the effective worker image ID.

Base image identity, build context hash and derived image identity are recorded
and bound to the receipt. Inherited ONBUILD instructions and volumes are rejected.
The local legacy builder is selected explicitly and fails closed if unavailable;
there is no automatic engine installation or fallback. This remains a candidate
runtime repair until exercised against Docker under authorized remaining capacity.

Distribution remains a standard-library Python module in the existing repository.
Derived images are local attempt artifacts, not published images. CI runs the
deterministic suite on Python 3.11 and 3.14; it does not exercise Docker.

## Code quality

**Finding 2, P2, confidence 10/10: preparation discarded subprocess diagnostics.**
The original `_cmd` used `subprocess.run(..., capture_output=True, ...,
check=True)` and propagated the exception; the CLI printed only `str(exc)`.
The reproduced stderr was therefore absent from the original error message.
The repair saves subprocess stdout/stderr, error type, status and input hash to
a new attempt-owned record before propagating a failure. Failure history and
reservations remain retained.

Existing checksummed records detect corruption relative to a trusted supervisor.
They are not signatures against an operator able to rewrite and reseal all files.
Verification of a synthetic receipt is not evidence that its narrated execution
happened. No general receipt signing or evidence service is introduced.

## Tests and user flows

The framework is Python unittest. Tests never launch a model. Mocked Docker
responses and synthetic receipts are explicitly software controls, not runtime
acceptance evidence.

```text
probe CLI
  compile + materialize
    stale config/changed bytes/hidden files -> reject [deterministic]
  reserve original ledger
    unresolved prior workload -> block [deterministic]
    duplicate ID/expired time -> block [deterministic; fresh CLI refusal unverified]
    accepted -> fixed FROM/COPY archive [deterministic]
      inherited hooks/volumes -> reject [source reviewed; test gap]
      build failure -> retain diagnostics [mocked command control]
      built image -> read-only owned worker [mocked; LIVE GAP]
        complete -> captured events + confirmed stop [LIVE GAP]
        cancel   -> partial events + confirmed stop [LIVE GAP]
        deadline -> partial events + confirmed stop [LIVE GAP]

recover existing attempt
  wrong ownership -> refuse to confirm [live control blocked]
  correct ownership + stopped -> close reservation [live recovery blocked]
  missing/unreachable workload -> retain reservation [not newly live-tested]

verify saved receipt
  changed receipt/capture, missing capture -> reject [synthetic]
  missing image binding / inconsistent image IDs -> reject [synthetic]
  completed synthetic record -> evidence_incomplete [synthetic]
  partial cancel/deadline record -> stays partial [synthetic]

independent bad-output control
  fabricated citation -> fail [deterministic]
  valid citation -> semantics unverified [deterministic]
real agent + approved benchmark -> [BLOCKED; no authenticated execution]
```

The live success, running-container cancellation and deadline branches require
Docker integration evidence; synthetic tests cannot cover that gap. Receipt
tampering is tested on copies so the original failed attempt remains intact.
No percentage of full runtime coverage is claimed.

## Performance and budgets

**Finding 3, P1 release gap, confidence 10/10: the original execution window expired.**
`storage.py:147` checks
`now - self.state["started_at"] + seconds > self.limits.total_seconds`.
The one-hour clock includes the handoff gap. Recovery can confirm shutdown, but
does not replenish elapsed time or remove the consumed attempt. Creating a fresh
store, changing the start time or relaxing this condition would reset the budget
and is excluded by the user's instruction.

**Finding 4, P2 release gap, confidence 10/10: --deadline is a run-phase limit.**
`prepare()` performs separately timed image/inspect/create commands before
`run()` initializes its monotonic timer. The new build timeout is 60 seconds;
other Docker commands default to 15 seconds. This bounds individual clients,
not the entire preparation-plus-execution lifecycle. The complete wall-time and
builder-shutdown behavior is not demonstrated. Do not describe --deadline as an
end-to-end proof ceiling. Redesigning accounting or enabling another run is
deferred to an explicitly revised execution plan.

## What already exists

- `materialization.py`: recompile the plan, check copied bytes and pack selected
  files. Reused rather than reading the whole worktree into a Docker build.
- `storage.py`: atomic records, OS lock, nonrefundable reservations and recovery
  blocking. Unchanged budget semantics.
- `docker_probe.py`: fixed credential-free probe, supervisor streams, explicit
  cancellation and container ownership. Extended within the existing adapter.
- `probe_cli.py` and `grading.py`: verify stored bindings and run independent
  citation controls. No semantic or benchmark pass is inferred.

## NOT in scope

- Renewing execution capacity or repairing the result by replacing the ledger:
  explicitly forbidden in this continuation.
- Model authentication, provider request/cost enforcement and the wrapper spike:
  intentional authorization and implementation are still missing.
- A real six-case comparison, operator approval and semantic assessment:
  milestone A has not passed.
- Publishing container images, customer data, Cockpit or dispatch integration:
  no product/release gate authorizes these changes.
- A second execution engine or a broad refactor: unnecessary for the bounded fix.

## Failure modes

| Failure | Handling and evidence | Remaining gap |
|---|---|---|
| Copy into read-only root | Exact stderr and stopped-state evidence retained | Replacement not run live |
| Missing builder/base or failed image build | Fail closed; preserve consumed reservation and diagnostics | Live builder failure/shutdown not demonstrated |
| Output/capture tampering | Hash and image-binding checks reject software controls | Actual completed runtime receipt absent |
| Wrong ownership on recovery | Refusal exists in source | Live ownership rejection and recovery not executed |
| Expired ledger | Block before image build/container create | No capacity for success/cancel/deadline tests |
| Deadline during preparation | Individual command timeouts, unresolved reservation retained | Whole lifecycle deadline not enforced/tested |

## Implementation tasks

- T1 (P1): replace post-create copy with the fixed image preparation path, retain
  the worker policy and image provenance. One repair iteration only.
- T2 (P2): preserve preparation command diagnostics and cover failure retention.
- T3 (P1 verification): exercise actual completion, cancel and deadline with
  confirmed container shutdown. Blocked by the existing execution limit.
- T4 (P2): verify synthetic receipt tampering and independent bad-output controls;
  publish a sanitized observation report without private raw inspect data.

No new global TODO backlog was created. Blocked prerequisites already belong to
the accepted proof plan and are recorded here without increasing scope.

## Coordination and independent challenge

One Astra High implementation lane owns adapter code and preparation tests. The
primary lane reviews architecture, adds separate synthetic receipt controls and
records documentation/PR state. Both lanes debit the same engineering allowance;
overlapping elapsed work counts twice. The existing branch and draft PR remain.
The recovery helper waited approximately 390 seconds for tool escalation approval
and was interrupted at the budget checkpoint. It produced no recovery or ownership
control result. It was not an automatic approval rejection. The retained reservation
is still unconfirmed; the elapsed-budget prediction is source/ledger evidence,
not a newly observed CLI refusal. The final deterministic suite passed 36 tests.

[running under Codex — nested codex passes skipped; set GSTACK_FORCE_CODEX_REVIEW=1 to force]

No cross-model agreement is claimed. The primary source review challenged the
expired runtime ledger and whole-lifecycle deadline assumptions independently of
the debugging lane. These constraints remain visible in the result.

## GSTACK REVIEW REPORT

| Review | Runs | Status | Findings |
|---|---:|---|---|
| Engineering plan review | 1 | issues_open | 4 findings; copy/diagnostic repair scoped; live verification and lifecycle time limit gaps remain |
| Outside voice | 0 | skipped under Codex | No nested model call or cross-model claim |

VERDICT: NOT CLEARED for runtime or milestone-A acceptance. The bounded repair
is reviewable; deterministic checks cannot replace the missing live evidence.

NO UNRESOLVED DECISIONS
