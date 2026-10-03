---
id: 2026-10-03-ivy-prheadsscan-review-01
type: review
state: open
repo: tompulsarlabs/ivy
lane: workhorse
pool: openai
created: 2026-10-03T09:00:00+02:00
created_by: scout
expires: 2026-10-05T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #25 ("Publish PR heads from the scanner; warn on memory
budgets; fix stale OVERVIEW") at its current head
(`c59a4c4f5c6537e37eb8ce785ca329f35d6e01d3`). Head branch
`claude/pile-up-pr1a` — anthropic authored, so this review is pinned to
the non-author family. This repo is directly accessible (not
access-scoped away), so read the actual diff rather than relying on the
PR body.

The PR claims: `scripts/local-wip.py` gains `pr_heads: {repo: {pr: sha}}`
from one bounded `git ls-remote <repo> 'refs/pull/*/head'` per watchlist
repo (15s per call, 120s total), with `GIT_TERMINAL_PROMPT=0` so a launchd
run can't hang on a credential prompt, and a repo that fails is absent
from `pr_heads`, never empty; a failed scan reaches the cloud as a fixed
`scanner_error` code on the last good snapshot, with `generated_at`
untouched so the 36h staleness rule still measures the last good scan;
`memory-lint.sh` gains warn-only word budgets (1,200 words/repo page,
1,800/subject page) that only fail the exit status under
`IVY_MEMORY_BUDGET=fail`; and the public `OVERVIEW` wording is corrected.
Verification claims: 41 `local-wip-test.py` tests (16 new) passing on
Python 3.14 and 3.9.6; a live dry-run against the real watchlist (22/22
repos, 129 PR heads, 5.9s); the same repeated under an `env -i` minimal
environment. The PR's own "Not verified" section discloses that the real
launchd/keychain context and the cloud MCP `label:` qualifier are
unverified, and that the scanner takes effect only once `~/Build/ivy`'s
checkout is on a `main` that includes this change.

Adversarial pass: (1) confirm the `git ls-remote` call is actually bounded
(a real timeout, not just a documented intent) and that one slow/hanging
repo cannot stall the whole pass past its claimed 120s budget; (2) confirm
a failing repo is omitted from `pr_heads` rather than written as an empty
or null entry indistinguishable from "no open PRs"; (3) confirm
`scanner_error` surfaces without mutating `generated_at`, so a scan
failure can't be mistaken for a stale-but-healthy snapshot; (4) confirm
the memory word-budget check is genuinely warn-only by default (run or
trace the exit-code path for a page over budget with
`IVY_MEMORY_BUDGET` unset) — this gates whether the failsafe's nightly
memory commit could ever be silently blocked by this change; (5) spot
check 2-3 of the claimed 16 new tests actually exercise the new
`pr_heads`/`scanner_error` behavior rather than re-asserting existing
scanner behavior under a new name. Cite file:line for every finding.

## Definition of done

A findings report exists at
`dispatch/reports/2026-10-03-ivy-prheadsscan-review-01.md`, each finding
tied to file:line with a proposed fix, and an overall verdict (pass /
request changes), committed and pushed to `main`.

## Verification (cloud-checkable)

The report file exists on `main` of `ivy`, is non-empty, and every cited
file:line resolves against PR #25's head
(`c59a4c4f5c6537e37eb8ce785ca329f35d6e01d3`) — directly readable, this
repo is not access-scoped away.
