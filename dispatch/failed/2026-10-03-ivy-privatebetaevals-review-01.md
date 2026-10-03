---
id: 2026-10-03-ivy-privatebetaevals-review-01
type: review
state: failed
claimed_at: 2026-10-03T10:35:03+02:00
repo: tompulsarlabs/ivy
lane: workhorse
pool: anthropic
created: 2026-10-03T09:00:00+02:00
created_by: scout
expires: 2026-10-05T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #26 ("Record private beta and personal-team evaluation
inventories") at its current head. Head branch
`codex/ivy-private-beta-evals` — openai authored, so this review is
pinned to the non-author family. This repo is directly accessible (not
access-scoped away), so read the actual diff rather than relying on the
PR body. The PR's own body states "Independent review is still required
before core merge" — treat that as the standing request this contract
answers.

The PR claims: it records shared evaluation inventories for the private
beta, personal brief, separate specialist runtime, and independent
deployment in `tompulsarlabs/ivy-app` (runnable cases live in that private
repo, not here); the inventory holds case definitions, fictional outputs,
and redacted real-run receipts, with personal correspondence/relationship
records/draft text/capabilities kept out of git; the current private-app
integration passed 132 Vitest cases (including real PostgreSQL controls),
54 Python cases, TypeScript, lint, and a standalone build; four
supplied-context regressions, a four-session synthetic team trace, and a
bounded four-session real-source acceptance were independently inspected;
hosted activation/auth/delivery, custom-domain cutover, desktop/mobile
visual review, and the next scheduled invocation remain unverified.

Adversarial pass: (1) confirm every file this PR adds/changes in `ivy`
actually matches the "inventory, not runnable cases" framing — flag any
added file that looks like it could execute against a live service or
contains a credential/token rather than a case definition or a redacted
receipt; (2) spot-check that "redacted" receipts are actually redacted
(no raw personal correspondence, real name, email, or other PII slipped
through) — this is the one claim most likely to fail silently; (3) 132 +
54 test-count claims belong to `ivy-app` (a repo this session cannot
read) — confirm the PR does not claim these numbers were independently
re-run from inside `ivy`, only recorded; if it does claim re-verification
from here, that claim cannot hold and is itself a finding; (4) confirm the
PR changes no file under `routines/`, `playbook.md`, or any Immutable
section listed in `playbook.md`, since an evaluation-inventory PR has no
reason to touch routine behavior. Cite file:line for every finding.

## Definition of done

A findings report exists at
`dispatch/reports/2026-10-03-ivy-privatebetaevals-review-01.md`, each
finding tied to file:line with a proposed fix, and an overall verdict
(pass / request changes), committed and pushed to `main`.

## Verification (cloud-checkable)

The report file exists on `main` of `ivy`, is non-empty, and every cited
file:line resolves against PR #26's head
(`2f7b5ea2c38d0929bdc0c85b2bb6f4febaafb12f`) — directly readable, this
repo is not access-scoped away.

outcome:
  requested_model: claude-opus-5
  requested_effort: medium
  effective_model: unknown
  effective_effort: unknown
  harness_version: 2.1.277
  source_revision: 802d1a766feb122a1301b01776c0f490c275e0d8
  runner_sha256: 7ede0aa04bc2fd57f673ca2a9729714a5d9c5e65f8a111c4ecf1cfa9d6e708c4
  config_sha256: c553d88a23c95b73c2b43c8fc0443b15bd72db73823cb01408e32a5fffa6e5c5
  prompt_sha256: d6f544db8096f42db6d4e70becd4a70fb075d45d32a7988ebd4b25ac2898ab16
  context_capture: runner_prompt_only
  usage_capture: unavailable
  claimed_at: 2026-10-03T10:35:03+02:00
  finished_at: 2026-10-03T10:35:10+02:00
  harness: claude-code (dispatch-runner)
  model: claude-opus-5
  wall_minutes: 0.0
  exit: 1
  note: harness_error; last output lines follow
  output_tail: |
      Failed to authenticate: OAuth session expired and could not be refreshed
