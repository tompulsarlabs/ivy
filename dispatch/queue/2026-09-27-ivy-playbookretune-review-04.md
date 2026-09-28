---
id: 2026-09-27-ivy-playbookretune-review-04
type: review
state: claimed
claimed_at: 2026-09-28T15:34:51+02:00
repo: tompulsarlabs/ivy
lane: workhorse
pool: openai
created: 2026-09-27T09:00:00+02:00
created_by: scout
expires: 2026-09-29T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Fourth review of PR #21 ("Re-tune the playbook, routine prompts, and
dispatch for the current models; add a routine eval") at its current
head `e466bb3` (branch `claude/skills-playbooks-refresh-784cgk`).
`2026-09-26-ivy-playbookretune-review-03` reviewed head `c78f8c8` and
returned **block** on one finding (P2: the memory graders still accept
an appended restatement instead of requiring an in-place rewrite). The
PR body claims two more commits since then:

- `cdd97b2` — claimed fix: memory-case graders now refuse a new
  "N missed windows"/days count in any wording and require exactly one
  complete account citing today, closing the review-03 finding. Also
  claims the eval was re-run and no run of 2026-09-24 or 2026-09-25
  changes pass/fail as a result.
- `e466bb3` — claimed correction only (not a functional fix): two
  claims in the PR description were wrong ("every variant ran on the
  head's playbook" — the baseline in fact ran `main`'s, as the control;
  and "five wrong edits per memory case" — the retro case had four) and
  are now corrected in the description text.

Check, with file:line citations against the diff (this repo is directly
accessible — no PR-body-corroboration fallback needed):

1. **Does `cdd97b2` actually close review-03's finding?** Confirm the
   memory-case test file (per the PR body: "adds the review's paragraph,
   the same sentence inside the account, a restatement with no count, a
   confirmation beside the rewritten account, and a second complete
   account on both failsafe pages, and a retro collapse that keeps an
   older count in other words") really exercises the appended-restatement
   case review-03 found, and that the grader rejects it — not just that
   new test cases exist, but that they fail against the pre-fix grader
   and pass against the fixed one.
2. **Is `grade`'s re-run claim accurate?** The body says `grade` was
   rebuilt to reconstruct each memory run's page from the case + stored
   diff, matching `patch` on "all 55 stored diffs," and that re-grading
   changes no pass/fail outcome for 2026-09-24 or 2026-09-25 runs. Verify
   this against the actual diff/test output rather than the PR's
   narrative.
3. **Re-check the Immutable byte-identity claim at the new head** —
   `playbook.md`'s Immutable sections must remain byte-identical to
   `main`'s (the PR claims 5,951 bytes, same SHA-256, confirmed at
   `c78f8c8`; confirm this still holds at `e466bb3`, since two more
   commits landed after that check).
4. **Are the two `e466bb3` corrections themselves accurate?** Confirm
   the baseline row in the results table actually ran on `main`'s
   playbook (not the head's) as the PR now claims, and that the retro
   memory case's test file has four wrong-edit variants, not five.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-27-ivy-playbookretune-review-04.md, with an
explicit verdict on each of the four checks above and an overall
verdict (pass / block, with severity and confidence per finding per the
worker prompt's review bar).

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, every commit sha
it cites (`c78f8c8`, `cdd97b2`, `e466bb3`, and any earlier shas it
re-confirms) is present on PR #21's branch via `list_commits`, and every
file path it cites exists at the branch's current head via
`get_file_contents`.
