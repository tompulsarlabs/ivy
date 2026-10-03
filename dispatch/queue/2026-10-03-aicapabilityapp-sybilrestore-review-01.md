---
id: 2026-10-03-aicapabilityapp-sybilrestore-review-01
type: review
state: open
repo: tompulsarlabs/ai-capability-app
lane: workhorse
pool: anthropic
created: 2026-10-03T09:00:00+02:00
created_by: scout
expires: 2026-10-05T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #9 ("Restore the existing SYBIL MVP with owner-approved beta
access") on its current head. Head branch `codex/private-beta` (confirmed
via `local-wip.json`) — openai authored, so this review is pinned to the
non-author family.

The PR claims: `main` had lost earlier MVP work and the demo bypassed
sign-in; this restores the product from a named prior commit and makes it
an owner-approved private beta at `sybil.tomgreen.ai`; Tom reviews,
preapproves and revokes users through `/beta-admin`, with middleware, API
routes, and database policies each independently enforcing admission;
capacity is 15 excluding the owner; additive migrations preserve 3
existing profiles and 13 existing assessments; Google OAuth and canonical
DNS/HTTPS are configured; 74 existing deterministic tests cover admission,
cross-account/team isolation, capacity, quotas, and provider boundaries;
anonymous model calls and reads of all six original tables were denied in
a live configuration check; no model-quality or full hosted end-to-end
pass is claimed.

Adversarial pass: (1) do middleware, API, and database-policy layers
*each* independently enforce admission as claimed, or does one layer
actually depend on another (so removing/bypassing the outer layer would
expose the inner one); (2) is capacity (15, excluding owner) enforced
server-side against a real count, or client-displayed only; (3) does the
additive migration genuinely preserve the stated 3 profiles / 13
assessments without a destructive step anywhere in the migration path
(check for any `DROP`/`TRUNCATE`/column-narrowing against those tables);
(4) is the "74 existing passing tests" claim accurate — are these tests
that predate this PR and already covered admission/isolation/capacity, or
does the PR's diff introduce new tests being described as pre-existing;
(5) the PR explicitly disclaims a full hosted end-to-end pass — confirm
the disclosed gaps (live assessment, learning persistence,
approval/revocation checks) are the ones actually missing, not a wider
list. Cite file:line for every finding.

## Definition of done

A findings report exists at
`dispatch/reports/2026-10-03-aicapabilityapp-sybilrestore-review-01.md`,
each finding tied to file:line with a proposed fix, and an overall verdict
(pass / request changes), committed and pushed to `main` of `ivy`.

## Verification (cloud-checkable)

The report file exists on `main` of `ivy`, is non-empty, and every
file:line it cites is corroborated against PR #9's own body text
(`search_pull_requests repo:tompulsarlabs/ai-capability-app` — this repo
sits outside this session's direct file access per `memory/ops.md`).
