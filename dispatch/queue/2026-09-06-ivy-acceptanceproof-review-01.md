---
id: 2026-09-06-ivy-acceptanceproof-review-01
type: review
state: open
repo: tompulsarlabs/ivy
lane: frontier
pool: openai
created: 2026-09-06T09:00:00+02:00
created_by: scout
expires: 2026-09-08T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #19 ("Design a bounded acceptance proof for agent instruction
changes") on its current head. Another self-modifying change to Ivy's own
instructions — check whether the proposed acceptance proof is actually
bounded (a concrete, cloud-checkable pass/fail, not an open-ended judgment
call left to whichever routine runs next), whether it can be gamed by a
routine motivated to self-report success, and whether it conflicts with
the existing Immutable verification rule rather than extending it.
Findings as file:line with a proposed fix each, or a plain confirmation
where a section is genuinely sound.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-06-ivy-acceptanceproof-review-01.md, each finding
tied to file:line, committed and pushed.

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, and every referenced
path exists on the PR head.
