# Domain docs

How the engineering skills consume this repository's domain documentation.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root: the glossary. Single context; there is
  no `CONTEXT-MAP.md`.
- **`docs/adr/`**: decisions recorded from now on, one short file each,
  numbered from `0001`. Created lazily by `/domain-modeling` when the first
  qualifying decision lands.
- **Historical decisions** predate `docs/adr/` and stay where they are:
  `DESIGN.md` §1 and §8 (the daily loop, GitHub's counting rules, what
  changed on contact with the sandbox), `dispatch/DESIGN.md` §1 and §10 (the
  executive layer), and `CHANGELOG.md` (every retro `learn:` change with its
  evidence). Read the section that touches the area before proposing a change
  to it.

If a file is missing, proceed silently.

`CONTEXT.md` keeps two sections beyond the glossary format on purpose:
`## Relationships`, and `## Flagged ambiguities`, which records the ambiguities
that already cost a contract and how each was resolved. Keep both.

Research notes (`/research`) go to `.scratch/research/<slug>.md`. `memory/` is
not a notes folder: only the failsafe and the retro write it.

## Use the glossary's vocabulary

When output names an Ivy concept (a contract's Task, a journal heading, a
memory-page claim, a commit message), use the term as `CONTEXT.md` defines it
and avoid the words it lists under _Avoid_. A concept the glossary lacks is
either language Ivy does not use (reconsider) or a real gap: note it in the
journal under `## Vocabulary gaps` for the retro.

## Flag decision conflicts

If output contradicts a recorded decision, say so rather than silently
overriding:

> _Contradicts dispatch/DESIGN.md §10.3 (workers open draft PRs), but worth
> reopening because…_

Immutable playbook sections are decisions too; they change only by a human
commit, so a conflict with one is a proposal to Tom, never an edit.
