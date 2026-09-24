---
id: 2026-09-24-ivy-scannerfix-review-01
type: review
state: open
repo: tompulsarlabs/ivy
lane: workhorse
pool: anthropic
created: 2026-09-24T09:00:00+02:00
created_by: scout
expires: 2026-09-26T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #22 ("Restore local work visibility and isolate scanner
publication") on its current head (`173a9e6`, branch
`codex/ivy-scanner-reliability`, base `main`). This is the fix for the
local-WIP scanner outage that has stood as the playbook's leading blocker
for 15 calendar days / 29 missed windows (`memory/repos/ivy.md`) — it
discovers registered worktrees the prior scanner skipped, keeps a
per-checkout and repo-wide unpushed count, publishes a six-hour heartbeat
when work is unchanged instead of going silent, and switches snapshot
publication to bot-authored commits from a temporary clone (bounded
non-force retries for branch races) instead of rebasing/pushing the
operator's own checkout. Adversarial pass: does the worktree discovery
actually cover the checkouts it claims to (body cites "20 checkouts
including 3 Ivy checkouts without absolute paths"); does the bot-authored
temporary-clone publish path avoid ever touching the operator checkout or
inventing an attribution identity (`[[ops]]` attribution-traps class); does
the six-hour heartbeat correctly distinguish "unchanged" from "scan
failed" (the body says "failed reads remain failures" — verify that claim
against the code); is `evals/local-scanner.json` (23 controls, per the
body) real and does it cover branch races, duplicate suppression, failed
pushes, symlink refusal, and concurrent locks as claimed. Findings as
file:line with a proposed fix each, or a plain confirmation where the
claim holds. Note explicitly whether `launchd` installation/activation is
in scope for this PR or deferred (the body says "launchd remains
unloaded" and lists post-merge steps) — that gap, if still open, belongs
in the report even though it's not this PR's to close.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-24-ivy-scannerfix-review-01.md, each finding tied
to file:line, committed and pushed.

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, and every referenced
path exists on the PR head. This session's GitHub access is scoped to
`ivy` itself, so `get_file_contents`/`pull_request_read` against this PR
are directly checkable — no PR-body-corroboration fallback needed.
