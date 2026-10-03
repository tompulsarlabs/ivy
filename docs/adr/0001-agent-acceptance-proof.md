# 0001 — Prove one agent acceptance workflow before expanding Ivy

Status: proposed for Tom's review. Date: 2026-09-05.

## Context

Tom authorized a next-phase system design after instruction/eval housekeeping and
selected teams shipping coding or internal-workflow agents. He wants a working,
demoable proof and a clear limit on work that does not create product value.

Current Ivy provides operations and useful verification lessons. Its case inventory
does not execute comparisons; receipts do not yet establish complete provenance or
reconcile revocation. Established tools already provide generic eval infrastructure.

## Decision proposed

Start with release acceptance for one PR-review agent. Compare two instruction
versions on six frozen scenarios through one actual harness. Use an existing
experiment tool where it fits, a small trusted supervisor, independent grading and
a portable report. The acceptance owner records a version-bound decision; no
automatic deployment or merging is included.

Keep the current daily Ivy system separate. Use new acceptance-domain manifests;
do not overload dispatch completion or the GitHub contribution metric as quality
signals. Resolve one authoritative acceptance/revocation policy before UI integration.

## Alternatives and consequences

A generic eval platform overlaps heavily with existing products and increases
integration and product risk before demand is known. A cockpit-first implementation
could demonstrate appearance while execution and evidence remain disconnected.
A service-only pilot can test demand quickly but still needs trustworthy evidence;
it is a valid outcome if reusable setup proves impractical.

The chosen proof may fail at isolation or fixture cost. Stop at the explicit effort
and call limits rather than expanding infrastructure. Six cases are smoke/regression
evidence; customer pilots and payment tests remain separate gates.

## Compatibility

No immutable playbook changes, model-lane changes, new dispatch contracts, production
commands or website schema changes. This acceptance context can later integrate
through explicit versioned interfaces after it proves useful.

See [system design](../next-phase/system-design.md), [proof plan](../next-phase/proof-plan.md)
and [product validation](../next-phase/product.md) for the concrete contracts and gates.
