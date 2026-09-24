---
id: 2026-09-24-ivy-harnesseffort-review-01
type: review
state: done
claimed_at: 2026-09-24T09:17:47+02:00
repo: tompulsarlabs/ivy
lane: workhorse
pool: anthropic
created: 2026-09-24T09:00:00+02:00
created_by: scout
expires: 2026-09-26T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #23 ("Apply harness effort settings and record execution
provenance") on its current head (`e23037c`, branch
`codex/ivy-harness-settings`, base `main`). The body claims the dispatch
runner previously dropped each lane's configured `effort` so frontier and
workhorse produced identical launch commands — this PR sends effort
through each native CLI, pins Claude's child effort environment, rejects
unknown model/harness/effort combinations before task claim or clone, and
adds an inspect-only route-preview plus execution-provenance recording
(CLI version, source revision, runner/config/prompt hashes) to started
attempts. Adversarial pass: does the effort value actually reach the CLI
invocation for both `claude` and `codex` (find the exact argv/env
construction and confirm frontier vs. workhorse now differ); does the
"unknown combination rejected before claim" path actually run before any
clone/claim side effect, or could it still burn a claim on an invalid
combination; is Haiku 4.5's effort field genuinely removed rather than
silently defaulted; does the route-preview truly touch nothing (no
runner-workspace write, no harness call) on both success and failure paths
it claims to cover. **PR #21 flags a direct conflict**: it says both PRs
touch `scripts/dispatch-runner.py` and `config.yml`'s lane effort wiring,
recommends merging this PR (#23) first, and notes its own registry "lists
only the current Opus" so a model move needs a registry entry too — note
this dependency in the report even though resolving it is Tom's merge-order
call, not this review's. Findings as file:line with a proposed fix each,
or a plain confirmation where the claim holds.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-24-ivy-harnesseffort-review-01.md, each finding
tied to file:line, committed and pushed.

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, and every referenced
path exists on the PR head. This session's GitHub access is scoped to
`ivy` itself, so `get_file_contents`/`pull_request_read` against this PR
are directly checkable — no PR-body-corroboration fallback needed.

outcome:
  claimed_at: 2026-09-24T09:17:47+02:00
  finished_at: 2026-09-24T09:27:08+02:00
  harness: claude-code (dispatch-runner)
  model: claude-opus-5
  wall_minutes: 9.3
  exit: 0
  artifacts:
    - dispatch/reports/2026-09-24-ivy-harnesseffort-review-01.md
