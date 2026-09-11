---
id: 2026-09-11-tomgreenai-radarsubtitle-review-01
type: review
state: open
repo: tompulsarlabs/tomgreen.ai
lane: workhorse
pool: openai
created: 2026-09-11T09:00:00+02:00
created_by: scout
expires: 2026-09-13T09:00:00+02:00
budget: { wall_minutes: 20 }
---

## Task

Review PR #58 ("Sharpen Radar demo subtitle") on its current head. Small,
single-line copy change on `/demos`: the Radar card subtitle becomes "Your
personal executive recruiter." Adversarial pass: confirm the new copy
actually matches the "approved positioning" the PR body claims (cite where
that approval lives, or flag if the PR body is the only evidence), check for
any other subtitle/copy sites that reference the old wording and were missed,
and confirm the PR body's validation claims (scoped ESLint, git diff checks)
are consistent with a copy-only diff. Findings as file:line with a proposed
fix each, or a plain confirmation where the change is genuinely sound and
scoped as claimed.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-11-tomgreenai-radarsubtitle-review-01.md, each
finding tied to file:line, committed and pushed.

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, and every referenced
path exists on the PR head.
