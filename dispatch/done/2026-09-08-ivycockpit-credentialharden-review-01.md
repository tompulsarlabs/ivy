---
id: 2026-09-08-ivycockpit-credentialharden-review-01
type: review
state: done
claimed_at: 2026-09-08T09:32:47+02:00
repo: tompulsarlabs/pixel-perfect-showcase-8458
lane: frontier
pool: anthropic
created: 2026-09-08T09:00:00+02:00
created_by: scout
expires: 2026-09-10T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #2 ("Harden shared-credential access and document Ivy privacy
findings") on its current head, stacked on PR #1. This is the highest-
stakes candidate in the queue today: the PR's own body states the proposed
write credential "can also modify the repository from which the Mac
automatically executes runner code" and calls this a release blocker that
"must remain disabled." Adversarial security pass, in priority order:
(1) confirm there is no code path on this head that enables or activates
that write credential — it must be inert, not merely undocumented;
(2) verify the JWT middleware and exact approved-operator allowlist are
actually enforced before every Notion status/write and credential-backed
GitHub capability/status read, with no unauthenticated fallback;
(3) confirm raw Notion error bodies are genuinely never returned or logged
anywhere (grep for the response bodies reaching a client or log sink);
(4) confirm redirects are rejected and requests carry real time limits, not
just documented ones; (5) check the four patched transitive dependencies
actually resolve to non-vulnerable versions in the lockfile. Findings as
file:line with a proposed fix each, or a plain confirmation where a
section is genuinely sound — this repo interacts with Ivy's own dispatch
queue and runner, so an unconfirmed claim here is a standing risk to the
system that reviews it.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-08-ivycockpit-credentialharden-review-01.md, each
finding tied to file:line, committed and pushed.

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, and every referenced
path exists on the PR head.

outcome:
  claimed_at: 2026-09-08T09:32:47+02:00
  finished_at: 2026-09-08T09:42:20+02:00
  harness: claude-code (dispatch-runner)
  model: claude-opus-5
  wall_minutes: 9.4
  exit: 0
  artifacts:
    - dispatch/reports/2026-09-08-ivycockpit-credentialharden-review-01.md

verified: true
verified_note: >
  Report exists on main of ivy, non-empty. PR #2 remains open (draft) and
  unchanged since 2026-09-07T13:39:49Z, well before this review's
  2026-09-08T09:32:47+02:00 claim -- head 87a61a5 confirmed stable.
  pixel-perfect-showcase-8458 is not in this session's repo scope, so
  paths could not be checked directly; corroborated instead against PR
  #2's own body, which restates the report's central claim verbatim: "The
  earlier Contents-write setup must remain disabled: that credential can
  modify the repository from which the Mac automatically executes runner
  code" -- matching F1's finding that the credential is armed by one env
  var, not actually disabled in code. Same corroboration standard used for
  talentradar-pilot-review-01 on 2026-09-07.
