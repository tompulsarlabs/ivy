# 0002 — Assess saved probe evidence before measuring agent economics

Status: selected for Tom's authorized architecture/system-development iteration,
6 September 2026. This record specifies the next build, not completed implementation.

## Context

The acceptance scaffold at `eaa9b36` has saved real credential-free completion,
cancellation and deadline evidence. Its current verifier checks artifact integrity
but does not establish that the fixed probe produced every required observation.
No evaluated model or judge has run, and Milestone A has not passed. Cost and quality
comparisons would therefore be premature without an explicit measurement boundary.

Existing records already bind the fixed probe's bytes, visible-file hashes,
container configuration and captures. Offline replay can exercise that boundary
without another container, credential or API call. Current main and Cockpit work
remain separate from the acceptance branch and its stacked draft PR #20.

## Decision

Build one offline evidence-and-resource report within one 60-minute implementation
lane. Preserve prior effort and runtime history, with this iteration's design and
implementation debit recorded separately. Recommend Astra High as an engineering
choice, not a benchmarked cost optimum.

Keep artifact integrity, terminal execution, fixed-probe assertions, natural
completion, expected shutdown control and model benchmark status separate. Recognize
only explicit program digests and policies; derive legacy expectations from the
receipt-bound manifest. Missing or unsupported provenance cannot pass. A passing
cancellation control does not become successful natural completion.

Introduce a versioned resource record outside the existing instruction-only plan.
Aggregate exclusive spend components once; preserve reported, estimated and unknown
values and distinguish resource reservation from observed execution and engineering
time. Produce JSON and Markdown from the same assessment. Label infrastructure
proof and unknown billing explicitly. Do not divide probe cost by accepted tasks.

## Consequences and scope

The build can replay real evidence now and reject meaningless hash-consistent output
without claiming model quality. It supplies a small measurement boundary for later
real attempts, while leaving the current comparison schema and daily dispatch intact.
It does not solve authentication, semantic grading, whole-lifecycle termination,
cloud attestation, routing or customer validation. The trusted local supervisor
assumption is explicit; hashes are not protection against a hostile host operator.

A routing platform, model matrix or Cockpit redesign would introduce independent
work before the first trustworthy model result. An actual accepted-task cost metric
will require real independently assessed primary slots and complete usage scope.
Those requirements are retained rather than simulated with infrastructure probes.

See [the bounded iteration specification](../next-phase/cost-quality-design.md) for
record semantics, command exits, parser limits, twelve verification cases and the
offline replay gate. [Runtime handoff](../next-phase/runtime-handoff.md) continues to
record actual implementation state and carried-forward resource usage.
