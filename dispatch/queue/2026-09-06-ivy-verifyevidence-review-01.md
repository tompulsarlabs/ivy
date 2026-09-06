---
id: 2026-09-06-ivy-verifyevidence-review-01
type: review
state: claimed
claimed_at: 2026-09-06T11:13:09+02:00
repo: tompulsarlabs/ivy
lane: frontier
pool: openai
created: 2026-09-06T09:00:00+02:00
created_by: scout
expires: 2026-09-08T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #18 ("Require explicit verification evidence and load
instructions by task") on its current head. This is a self-modifying
change to Ivy's own operating instructions (playbook/routines/CLAUDE.md),
so the adversarial pass matters more than usual: does the new wording
actually tighten verification (no room left for a routine to claim
"verified" on a self-report or an inference), does the task-scoped
instruction loading it describes avoid dropping a section a routine still
needs, and does it contradict or duplicate anything in the Immutable
sections it must not touch. Findings as file:line with a proposed fix
each, or a plain confirmation where a section is genuinely sound.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-06-ivy-verifyevidence-review-01.md, each finding
tied to file:line, committed and pushed.

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, and every referenced
path exists on the PR head.
