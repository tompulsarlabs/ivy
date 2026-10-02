---
id: 2026-09-23-tomgreenai-copy-03
type: build
state: failed
claimed_at: 2026-09-23T13:40:04+02:00
repo: tompulsarlabs/tomgreen.ai
lane: workhorse
pool: anthropic
created: 2026-09-23T09:00:00+02:00
created_by: scout
expires: 2026-09-25T09:00:00+02:00
budget: { wall_minutes: 40 }
---

## Task
Tighten the Scout demo page's intro copy to three sentences in plain
language. Branch from main as dispatch/2026-09-23-tomgreenai-copy-03, change
only src/app/demo/scout/page.tsx, open a draft PR, never push to the default
branch.

## Definition of done
A draft PR by tompulsarlabs from that branch, changing only
src/app/demo/scout/page.tsx, with tests passing.

## Verification (cloud-checkable)
search_pull_requests finds a draft PR by tompulsarlabs whose body names
2026-09-23-tomgreenai-copy-03 and lists only src/app/demo/scout/page.tsx.

outcome:
  claimed_at: 2026-09-23T13:40:04+02:00
  finished_at: 2026-09-23T14:20:09+02:00
  harness: claude-code (dispatch-runner)
  model: claude-opus-5
  wall_minutes: 40.0
  exit: timeout
  note: timeout; last output lines follow
  output_tail: |
    Opening draft pull request...
    https://github.com/tompulsarlabs/tomgreen.ai/pull/67
    Running the e2e suite once more before the summary.
