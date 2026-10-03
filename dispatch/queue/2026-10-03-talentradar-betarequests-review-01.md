---
id: 2026-10-03-talentradar-betarequests-review-01
type: review
state: open
repo: tompulsarlabs/talent-radar
lane: workhorse
pool: anthropic
created: 2026-10-03T09:00:00+02:00
created_by: scout
expires: 2026-10-05T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #10 ("Add private beta requests, owner revocation and
twenty-place capacity") on its current head. Head branch
`codex/beta-request-profiles` (confirmed via `local-wip.json`) — openai
authored, so this review is pinned to the non-author family. Scope the
review to the PR's own title and its first two body paragraphs (access
control, capacity, revocation); later paragraphs in the body describe
unrelated prior UI/audio work and are not this PR's claim to check.

The PR claims: revocation disables membership atomically with an audit
entry and a durable voice-shutdown queue; existing tokens cannot authorize
new workspace requests post-revocation; an unused approval can be revoked
before first login; activated places still count toward the 20-place
cohort while an unused revoked approval releases its reservation; owner
notifications carry no applicant PII (name/email/career details/approval
tokens); decisions require verified Google owner identity; the dispatch
credential that drains the shutdown queue cannot choose a member,
approve/revoke access, or retrieve applicant details; open workspaces
recheck access every 15 seconds and on focus; 482 deterministic tests plus
typecheck/lint/build/synthetic-UI/rollback-only-SQL/11 live HTTP checks
pass.

Adversarial pass: (1) does the revocation path actually revoke atomically,
or is there a window where a revoked member's existing session/token still
reaches a protected route or the voice service; (2) can the "unused
approval" distinction (release the cohort slot) be forced incorrectly —
e.g. does "unused" get determined from a field a client can influence;
(3) is the dispatch credential's scope enforced server-side (a real
least-privilege boundary: denylist of member-selection/approval/
applicant-detail reads) or only true by omission in the code reviewed;
(4) do owner notifications' payloads actually exclude every PII field
listed, checked against the schema/template, not just the PR's own
description; (5) is admission truly gated on verified Google identity for
every new code path this PR adds, not only the pre-existing ones. Cite
file:line for every finding.

## Definition of done

A findings report exists at
`dispatch/reports/2026-10-03-talentradar-betarequests-review-01.md`, each
finding tied to file:line with a proposed fix, and an overall verdict
(pass / request changes), committed and pushed to `main` of `ivy`.

## Verification (cloud-checkable)

The report file exists on `main` of `ivy`, is non-empty, and every
file:line it cites is corroborated against PR #10's own body text
(`search_pull_requests repo:tompulsarlabs/talent-radar` — this repo sits
outside this session's direct file access per `memory/ops.md`).
