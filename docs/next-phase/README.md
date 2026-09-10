# Ivy next phase: evidence for agent release decisions

Direction approved · 5 September 2026 · architecture scaffold implemented; live execution pending.
Tom authorized system design after the housekeeping handoff and selected teams
shipping coding or internal-workflow agents as the first customer group.

**Proposed job:** before changing an agent's instructions, model or tools, help its
release owner decide whether the change meets the team's acceptance requirements,
using the team's actual agent and inspectable evidence.

The first proof compares two instruction revisions of one PR-review agent on six
frozen repository scenarios. It produces a comparison and a reviewable decision
record. It does not deploy the agent or approve the code being reviewed.

## Current handoff

[Ultra → Extra High → High](build-handoff.md) records the implemented scaffold, exact
commands, remaining build interfaces and resource limits. The [package README](../../ivy_acceptance/README.md)
describes what works now. No model-quality eval has run in this stage.

## Read and decide

- [Product and validation](product.md): buyer hypothesis, cost of the problem,
  existing alternatives, demand tests and what would make us stop.
- [System design](system-design.md): components, data contracts, execution and
  evidence boundaries, state transitions and failure handling.
- [Bounded proof](proof-plan.md): exact demo, acceptance tests, work limits and
  milestones. This is a proposed build plan, not queued dispatch work.
- [Decision record](../adr/0001-agent-acceptance-proof.md): scope and tradeoffs.

## What the audit actually establishes

Ivy operates scheduled routines and local CLI workers. The housekeeping branch adds
explicit cases and evidence-completeness checks. It does not yet run reproducible
baseline/candidate experiments or establish enterprise demand.

The [housekeeping handoff](https://github.com/tompulsarlabs/ivy/blob/de084f15bece5393630dc6cf57191043a684c379/docs/housekeeping/rollout.md)
records 33 proposed behavior cases across 13 roles, six quarantined historical
verification stamps, and one writing smoke test with incomplete model provenance.
[PR 18](https://github.com/tompulsarlabs/ivy/pull/18) is a separate review and rollout;
this design does not assume it has been merged or deployed.

A local Cockpit V3.1 brief describes an existing Lovable interface with disconnected
execution controls. Its code and deployed behavior were not inspected in this pass.
That brief is context, not an instruction to implement its separate work here.

## Recommendation

Build one acceptance proof before expanding Ivy into a platform. The expensive
unknown is whether realistic fixtures and useful release evidence can be produced
quickly for a customer's existing workflow. Resolve that with one end-to-end slice
and an early external release-owner commitment, before spending on a dashboard, generalized orchestration
or a large model matrix.

Use the current daily Ivy system as a source of cases and operational lessons.
Keep its streak, contribution accounting and autonomous dispatch outside the new
acceptance workflow. No immutable operating policy changes are proposed here.
