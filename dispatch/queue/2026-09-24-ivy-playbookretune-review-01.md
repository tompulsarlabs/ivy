---
id: 2026-09-24-ivy-playbookretune-review-01
type: review
state: claimed
claimed_at: 2026-09-24T09:57:14+02:00
repo: tompulsarlabs/ivy
lane: frontier
pool: openai
created: 2026-09-24T09:00:00+02:00
created_by: scout
expires: 2026-09-26T09:00:00+02:00
budget: { wall_minutes: 45 }
---

## Task

Review PR #21 ("Re-tune the playbook, routine prompts, and dispatch for
the current models; add a routine eval") on its current head (`5937264`,
branch `claude/skills-playbooks-refresh-784cgk`, base `main`). Frontier
lane, not workhorse: this PR rewrites the Tunable sections of
`playbook.md` and all four routine prompts that govern every future run of
this system, and its own body claims a byte-identical Immutable section
(that specific claim is load-bearing and must be checked directly, not
taken on trust). Adversarial pass, in priority order:

1. **The Immutable-section claim.** Diff `playbook.md`'s Immutable sections
   (counting rules, verification, commit attribution, no synthetic
   contributions, memory records observations, `state.json` append-only,
   dispatch guardrails) between `main` and this PR's head. Any byte
   difference is a P1 — the PR's own stated boundary would be violated.
2. **The eval's own numbers.** The body cites 45/46 preserve-runs and 4/4
   change-runs passing on the candidate vs. 35/46 and 0/4 on baseline, plus
   a transition variant. Spot-check `evals/routines/results/2026-09-23.md`
   and a sample of `evals/routines/` cases against these claims — do the
   case definitions test what the body says they test, and is "no
   regressions" (no case passing baseline that fails candidate) actually
   true across the full set, not just the cited samples.
3. **The stated open questions are real, not narrative.** The body names:
   a direct file-level conflict with PR #23 on `scripts/dispatch-runner.py`
   and `config.yml` (same files, same lane-effort feature — confirm the
   overlap is real by diffing both PRs' changed hunks in those files); the
   Immutable verification rule still names `check.sh`, which exits 2 in
   the cloud sandbox (confirm this PR does not silently paper over that
   gap in a Tunable section instead of leaving it for Tom); and PR #18's
   unresolved overlap (confirm this PR's claim that PR #18's Ivy cases are
   "covered here by runnable ones").
4. **Commit-signature note.** The body says the first 19 commits show
   Unverified on GitHub because committer and signing identity diverged,
   fixed from `7055d40` on, and that a squash merge would keep the
   unverified ones off `main` — confirm this is accurate and not a loose
   end that following commits also need.

Findings as file:line with a proposed fix each, or a plain confirmation
where a claim holds. This is the highest-consequence review queued today —
a wrong Tunable rewrite changes how every subsequent scout/check/failsafe
run behaves, silently, starting with the first run after merge.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-24-ivy-playbookretune-review-01.md, each finding
tied to file:line, committed and pushed.

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, and every referenced
path exists on the PR head. This session's GitHub access is scoped to
`ivy` itself, so `get_file_contents`/`pull_request_read` against this PR
are directly checkable — no PR-body-corroboration fallback needed.
