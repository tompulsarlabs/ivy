---
id: 2026-09-08-ivycockpit-queueconnect-review-01
type: review
state: open
repo: tompulsarlabs/pixel-perfect-showcase-8458
lane: workhorse
pool: anthropic
created: 2026-09-08T09:00:00+02:00
created_by: scout
expires: 2026-09-10T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #1 ("Connect cockpit actions to the Ivy queue") on its current
head. Adversarial pass: are the operator and repository allowlists, queue
policy, source-revision checks, atomic writes and idempotent retries the PR
describes actually enforced server-side (not just in the browser client);
does "Start work" / "Request changes" / "Retry" only ever create bounded,
receipted tasks with no path to an unsupported operation; and is worker
completion genuinely never presented as independent verification anywhere
in the UI. The PR body says its command adapter "points to an undefined
endpoint" and execution is "disconnected" — confirm that is still true on
this head (no live queue write, runner invocation, or deployment path is
reachable). Findings as file:line with a proposed fix each, or a plain
confirmation where a section is genuinely sound.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-08-ivycockpit-queueconnect-review-01.md, each
finding tied to file:line, committed and pushed.

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, and every referenced
path exists on the PR head.
