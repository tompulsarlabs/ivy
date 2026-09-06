# Report — 2026-09-06-ivy-acceptanceproof-review-01

Produced by the frontier/openai lane, 3.7 wall-minutes.

# PR #19 acceptance-proof review

Reviewed head `8528cb5d60f5f63df4bdafd842bb08a461e20c6a` against base `71e09466678d139a99b032fe98cc69236aac0ed3`.

## Standards

### [P2] Proposed implementation spec is stored outside the prescribed location

**Location:** `docs/next-phase/proof-plan.md:3-5`, `docs/next-phase/proof-plan.md:132-150`

The file describes itself as a proposed, unqueued build contract. `docs/agents/issue-tracker.md:3-6` requires non-executable specifications under `.scratch/<effort>/`, while executable work must become a linted dispatch contract.

**Proposed fix:** Keep durable decisions in the ADR, move the implementation specification to `.scratch/agent-acceptance-proof/spec.md`, and derive a proper dispatch contract once implementation is authorized.

No material baseline code smells apply to this documentation-only change.

## Spec

### [P1] Semantic grading is not closed into a bounded verdict

**Location:** `docs/next-phase/proof-plan.md:31-43`, `docs/next-phase/proof-plan.md:145-150`

The six cases use undefined judgments such as “material defect,” “consistent with the code,” and “disputed new finding,” while human review decides correctness and usefulness. No complete answer key, allowed-equivalence rules, named adjudicator, deadline, or fail-closed treatment of unresolved disputes is specified. Consequently, the deterministic aggregation at `docs/next-phase/system-design.md:249-255` only deterministically aggregates subjective inputs supplied later.

**Proposed fix:** Freeze a versioned rubric before execution containing criterion IDs, ground-truth tests/source locations, allowed equivalent findings, evidence requirements, and explicit pass/fail/unverified mappings. Name an independent reviewer, bind their authenticated approval to the benchmark hash, and require unresolved criteria to become `Evidence incomplete` at a fixed deadline.

### [P1] The proof has no independently cloud-verifiable evidence path

**Location:** `docs/next-phase/system-design.md:94-102`, `docs/next-phase/system-design.md:211-223`, `docs/next-phase/system-design.md:274-277`

The result and operator actions are local records. The design explicitly acknowledges that their hashes do not create an immutable audit log or protect against a compromised host. It does not define where a cloud verifier obtains the frozen inputs, captures, assessments, or authenticated approvals, nor a command or check that independently recomputes the bindings and verdict. A supervisor routine can therefore publish a plausible self-reported pass that the cloud cannot distinguish from authentic evidence.

**Proposed fix:** Require a durable externally anchored evidence bundle, or a digest whose complete artifacts remain accessible to the verifier. Authenticate owner and reviewer attestations against the exact benchmark/result hashes. Define one fail-closed cloud check that fetches the pinned artifacts, recomputes all hashes and the decision function, verifies the authorized attestations, and rejects missing, expired, mismatched, or worker-authored evidence.

## Confirmed sound

- `docs/next-phase/proof-plan.md:24-48` and `docs/next-phase/system-design.md:179-215` materially protect against gaming by the evaluated worker: labels and grader fixtures remain outside its environment, authoritative captures belong to the supervisor, and worker success flags are explicitly rejected.
- `docs/next-phase/system-design.md:245-267` fails closed on incomplete coverage and prevents retries from repairing or replacing adverse primary results.
- `docs/next-phase/system-design.md:24-26` and `docs/adr/0001-agent-acceptance-proof.md:39-43` keep the proposed workflow separate from daily dispatch and make no Immutable playbook change. This extends rather than conflicts with `playbook.md:101-104`; operational release integration remains explicitly deferred.

## Verification

`git diff --check` passed. Every referenced path exists on the recorded PR head, and the worktree remained unchanged. Per the contract’s read-only rule, no report file, commit, or push was created by this worker.

Summary: Standards—1 finding, chiefly the non-executable spec location. Spec—2 P1 findings, chiefly the absence of an independently cloud-verifiable proof.
