# Build handoff: Ultra → Extra High → High

Tom approved the next-phase direction and asked for architecture/scaffolding at
Ultra, implementation at Extra High, then debugging at High (5 September 2026).
Keep these stages in the existing task and shared build budget. This handoff does
not claim that the app's model/reasoning setting has been changed automatically.

**Current checkpoint:** Extra High implementation has reached its first actual
runtime preparation failure. Continue with [runtime-handoff.md](runtime-handoff.md)
at High; it supersedes the original scaffold status below. Milestone A is not passed.

## Stage 1 — Ultra: architecture and scaffold

Implemented in `codex/ivy-acceptance-scaffold`, based on design PR 19. The worktree
is `/tmp/ivy-acceptance-scaffold`. Housekeeping PR 18 is a separate branch; its
unmerged code is not a runtime dependency of this package. Production dispatch and
the existing Cockpit were not changed.

Start with `ivy_acceptance/README.md`. Run from the worktree root:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B -m ivy_acceptance plan examples/acceptance/preview.json
```

Current evidence: 18 deterministic tests pass locally. They cover canonical identity,
strict schema/path boundaries, detached mutable inputs, paired trial slots, in-memory
reservations, unavailable live operations, read-only CLI behavior, and two synthetic
fixture behaviors. CI exercises Python 3.11 and 3.14. Its actual status belongs to the
PR checks, not an assumption from this document.

The example compiles eight slots for R1 and R3. Runtime fields remain unset, grading
labels require owner review, and `execution_ready` is always false. The package does
not execute agents, collect authoritative traces, authenticate approval, grade model
outputs or produce release eligibility. There have been zero evaluated-worker runs
in this stage. Implementation-assistant usage is separately recorded as unavailable
where this environment does not expose per-call accounting; see `resource-ledger.json`.

The read-only availability probe found no callable `docker`, `podman` or `colima`
on PATH. No container runtime was installed and no credentials were copied.

## Stage 2 — Extra High: implement milestone A first

Use Astra with Extra High reasoning as Tom requested. Read this file, the package
README, `proof-plan.md` and the relevant system-design sections. Preserve the current
architecture; reopen a decision only for a demonstrated blocker.

1. Establish one local Docker-compatible execution path and intentional harness
   authentication. Resolve the actual harness/version, model request, effort, tools,
   permissions and instruction imports. Keep hidden labels and authoritative data
   outside the worker's filesystem. Do not mount the host home, repository root,
   provider-wide credentials or container-control socket into the worker. Stop with
   the exact prerequisite if isolation/authentication cannot be established within A.
2. Give the Promptfoo wrapper at most 30 minutes inside the same two-hour milestone,
   with result caching/resume reuse disabled. Use the small sequential adapter only
   if a concrete incompatibility justifies it; no second engine or new platform.
3. Implement `HarnessAdapter` with supervisor-owned capture and an attempt-owned
   container identity. `cancel` must confirm that workload stopped; killing the
   launcher is insufficient. Unknown shutdown keeps capacity reserved and blocks
   another launch. Provider work already in flight can outlast local cancellation.
4. Persist the attempt/resource ledger atomically before launch and validate it on
   restart. Revalidate the detached plan hash and actual file snapshots immediately
   before materialization. The preview envelope is not an executable or authenticated
   approval record. Add explicit owner-review approval and effective preflight binding;
   do not enable a run by editing `execution_ready` in saved JSON.
5. Run one neutral case with real evidence and a separately labeled deterministic
   bad-output grading control. Capture requested versus observed model settings,
   completion state, relevant tool/effect events and available usage. No final-text
   self-score can satisfy independent assessment.

Milestone A's exit is the real end-to-end evidence, not a passing scaffold test.
The two-hour A limit includes this scaffold stage's conservative aggregate time debit
in `resource-ledger.json`; it does not restart at handoff. At the boundary, report the
result and ledger. Do not consume the remaining proof budget without the external
release owner/pending change/timed-workaround gate, unless Tom explicitly chooses
further internal dogfood.

If A passes and that product gate is satisfied, implement B/C within the shared
12-hour limit: complete R2/R4/R5/R6 with owner-approved neutral tasks and labels;
freeze 24 primary slots; collect the two versions' actual evidence; independently
grade required criteria; generate the comparison and a version-bound operator record.

The primary slot set never changes after freezing. A diagnostic retry references the
original attempt, gets a new ID and cannot repair primary coverage or replace a bad
result. Every primary slot requires a fresh execution. Operator actions reference an
immutable computed result; they do not mutate observations or deploy anything.

## Stage 3 — High: bounded debugging

Switch Astra to High for debugging once the implementation has a concrete failing
check or the build handoff is ready. Start with the failing command, expected versus
observed behavior, exact source revision and captured evidence. Reproduce in isolated
fixtures before making the smallest fix. Preserve hashes, primary coverage, evidence
boundaries and stop conditions. Do not weaken grading rules or increase limits to get
through a failure.

Run the affected checks, then the full deterministic acceptance suite and the relevant
actual adapter acceptance test. A model rerun needs a reason, a new attempt ID and
remaining budget. Use at most two repair iterations after the initial implementation
per milestone; persistent failure returns the concrete blocker to Tom. Debugging may
not add scope or reset the resource ledger.

## Explicitly unfinished interfaces

- Persisted plan/attempt/assessment validation, artifact storage and crash recovery.
- Effective harness configuration, isolated preparation, streaming capture and confirmed
  workload termination; all live adapter methods currently raise `CapabilityUnavailable`.
- Independent assessment binding and the authoritative benchmark decision function.
  The state enums are contracts, not an implemented grader. Known failures must
  outrank missing evidence; missing required coverage can never pass.
- Comparison/report generation and version-bound local operator records.
- Four remaining real fixtures, owner approval and external product validation.

Do not infer any of these from the preview's hashes or directory separation. Keep
raw customer evidence private; this Ivy repository is public. Broader enterprise
features and Cockpit execution remain outside the bounded proof.
