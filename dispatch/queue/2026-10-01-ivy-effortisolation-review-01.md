---
id: 2026-10-01-ivy-effortisolation-review-01
type: review
state: open
repo: tompulsarlabs/ivy
lane: workhorse
pool: openai
created: 2026-10-01T09:00:00+02:00
created_by: scout
expires: 2026-10-03T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #24 ("Keep unset effort isolated and expose dispatch preflight
failures") at its current head (`fbfb4ca5`). This repo is directly
accessible (not access-scoped away), so read the actual diff rather than
relying on the PR body. The PR claims to fix harness review findings F1,
F3, F2 (false-healthy reporting), and F5 (test coupling) from
`dispatch/reports/2026-09-24-ivy-harnesseffort-review-01.md`. Adversarial
pass: (1) confirm an unset Claude lane no longer inherits an ambient
`CLAUDE_CODE_EFFORT_LEVEL` — inspect how the command is constructed for an
unset-effort lane and confirm no stray environment value leaks through;
(2) confirm a malformed or unreadable routing configuration now fails
preflight before any contract is claimed, rather than the prior
false-healthy `lint_ok: true` heartbeat the PR describes; (3) confirm a
provenance read failure leaves the contract `open` with
`provenance_unavailable` (not silently dropped) and that the next eligible
contract still runs; (4) check the four newly registered tests (of 23
total harness control tests) actually exercise these three cases
red-before/green-after, not just happy-path assertions — the PR claims
these failed against base `1305117` before the fix; (5) confirm
command-construction tests run against fixtures rather than live
`config.yml`, so a future legitimate lane retune won't spuriously break
them. Cite file:line for every finding.

## Definition of done

A findings report exists at
`dispatch/reports/2026-10-01-ivy-effortisolation-review-01.md`, each
finding tied to file:line, with an overall verdict (pass / request
changes), committed and pushed to `main`.

## Verification (cloud-checkable)

The report file exists on `main` of `ivy`, is non-empty, and every cited
file:line resolves against PR #24's head
(`fbfb4ca5f33196922e78a3396e958751ee20a3d5`) — directly readable, this
repo is not access-scoped away.
