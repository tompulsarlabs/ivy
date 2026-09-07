---
id: 2026-09-07-tomgreenai-activitymatrix-review-01
type: review
state: done
claimed_at: 2026-09-07T10:04:07+02:00
repo: tompulsarlabs/tomgreen.ai
lane: workhorse
pool: anthropic
created: 2026-09-07T09:00:00+02:00
created_by: scout
expires: 2026-09-09T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #41 ("Preview a 30-day activity matrix in the Lab header") on its
current head. Adversarial pass: does the rolling 30-day window actually
handle the Berlin-date boundary and DST transitions correctly, does the
hourly refresh degrade gracefully when the GitHub data source is
unavailable (the PR claims a link fallback — verify it exists and is
reachable), and does the reduced-motion path fully disable the animation
described (staggered edge slivers, detached motes) rather than just
slowing it. Findings as file:line with a proposed fix each, or a plain
confirmation where a section is genuinely sound.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-07-tomgreenai-activitymatrix-review-01.md, each
finding tied to file:line, committed and pushed.

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, and every referenced
path exists on the PR head.

outcome:
  claimed_at: 2026-09-07T10:04:07+02:00
  finished_at: 2026-09-07T10:14:44+02:00
  harness: claude-code (dispatch-runner)
  model: claude-opus-5
  wall_minutes: 10.5
  exit: 0
  artifacts:
    - dispatch/reports/2026-09-07-tomgreenai-activitymatrix-review-01.md
