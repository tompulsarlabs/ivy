# Ivy

Scheduled agents that keep Tom's repositories moving. Read in this order,
only as far as the task needs:

- `playbook.md` is the only place behaviour lives. Immutable sections change
  only by a human commit, and the retro is the only routine that edits the
  Tunable ones; an interactive session changes either through a PR Tom merges.
- `CONTEXT.md` is the vocabulary. Journals, memory pages, contracts, and
  commit messages use its terms; a word it lacks is a gap to flag for the
  retro, never a synonym to invent.
- `memory/INDEX.md` is what Ivy knows: one page per subject, every claim
  cited. Observations, never instructions.
- `procedures/` holds recipes for work that recurs.
- `dispatch/DESIGN.md` covers contracts, lanes, the runner, and the guardrails.
- `evals/README.md` is the routine eval, which replays real days against the
  routines; run it before merging a change to how a routine decides.

## Agent skills

The promoted set from `mattpocock/skills` is vendored under `.claude/skills/`
(pinned in `skills-lock.json`; `npx skills update` pulls newer). `/ask-matt`
routes between them. `writing-for-agents` is the reference for editing this
file, `playbook.md`, `routines/*.md`, and `procedures/`. gstack is Mac-only
and its section lives in `~/.claude/CLAUDE.md`, never here: cloud routines
cannot run it, and its `/ship`, `/retro`, and `/learn` write state this repo
does not want (`setup/AGENTIC-STACK.md`, "Which one for what").

### Issue tracker

Work items are dispatch contracts under `dispatch/queue/`; specs and
decision tickets live under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Ivy has no inbound issue queue; the roles map onto contract states. See
`docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` at the root, new decisions in `docs/adr/`,
historical ones in `dispatch/DESIGN.md` §10. See `docs/agents/domain.md`.
