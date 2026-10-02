# Ivy

Ivy is a set of scheduled agents that keep my software projects moving, and
that remember what they learn while doing it.

It runs three times a day in the cloud (plus a weekly retro), watches every
non-fork, non-archived repository on my account, and writes
everything it knows back into this repo as plain files. Nothing is hidden in
a database or a vendor's memory store — the whole system is markdown, JSON,
and git history you can read top to bottom.

## The daily loop

| Run | Time (Berlin) | What it does |
|-----|--------------|--------------|
| Scout | 09:00 | Reads its own memory, syncs the repo list, finds real work worth doing today, writes the candidates into a journal entry. Silent. |
| Check | 18:00 | Asks GitHub whether today counts yet. Green: records it, says nothing. Grey: one push notification naming one specific next action. |
| Failsafe | 22:30 | Confirms the day, verifies finished dispatch work, folds the day's facts into memory. If the day is still grey, writes a real engineering note and commits it. |
| Retro | Sun 10:00 | Reads a week of outcomes, changes at most two things, cites the evidence for each change. |

The failsafe is the floor: if a day would otherwise be empty, Ivy writes a
genuine journal entry rather than faking activity. It was not needed for the
first twenty recorded days; it first fired on 12 September 2026.

## The layers of state

Each layer answers a different question, and they stay in their own lanes.

- **`journal/`** — one entry per day. What was available, what happened,
  how the day was verified. This is the raw record.
- **`state.json`** — machine-readable outcomes: streak, per-day counts,
  whether a nudge was sent and whether it converted. Terse; it cites the
  journal for detail. `tomgreen.ai` reads this file live, so the schema is
  append-only.
- **`memory/`** — one page per subject: each repo, the environment,
  observed working patterns, routing evidence. Every claim carries a
  citation to a journal date or a commit. Pages link to each other with
  `[[wikilinks]]`. This is the layer that makes run number fifty smarter
  than run number one.
- **`dispatch/`** — work contracts. A scouted candidate becomes a file
  stating the task, the definition of done, and a check that proves it.
- **`procedures/`** — recipes. A task done well once, written down with
  exact commands so it never has to be re-derived from journal history.
- **`CONTEXT.md`** — the glossary. One word per concept and the words to
  avoid, so a journal, a memory page, and a contract all mean the same thing
  by "nudge", "done", or "connected address".

## How memory works

Journals and `state.json` are chronological, so answering "has this PR been
nudged before?" used to mean re-reading five days of entries. The `memory/`
wiki fixes that: one page per subject, read at the start of every run.

Two kinds of link do the work. `[[page]]` connects subjects sideways — the
`tomgreen.ai` page links to `ops` because the sandbox limits explain its
verification path. `[cite:2026-08-27]` connects a claim down to the journal
entry that proves it. `scripts/memory-lint.sh` checks that every link and
citation resolves, so the wiki can't rot into confident nonsense.

The failsafe adds facts daily. Only the weekly retro removes them, verifies
claims against their citations, and logs what it pruned.

## How dispatch works

A contract is a markdown file with frontmatter — task, definition of done,
a cloud-checkable verification, a lane, a wall-clock budget. The repo is the
message bus: every state change is a commit, and terminal contracts move
between `queue/`, `done/`, and `failed/`.

Lanes are coarse on purpose: `frontier`, `workhorse`, `fast-cheap`, each
mapped in `config.yml` to a concrete harness and model per provider. Model
names change monthly, so they live in config as data the retro can update,
not baked into behavior.

Execution splits across two machines because it has to. The cloud sandbox's
network access is scoped to this repo alone — it cannot reach OpenAI at all
— so a launchd runner on the Mac executes contracts and holds every
provider login. The cloud never sees a credential.

Workers are not trusted. They push branches and open draft pull requests,
never to a default branch. A contract is only *verified done* when the
failsafe independently runs its verification step and stamps the result.
Worker exit codes are claims; the check is the evidence.

## Skills

The routines, the workers, and my own sessions share one working discipline:
[Matt Pocock's skills](https://github.com/mattpocock/skills), vendored under
`.claude/skills/`. Design happens as a grilling interview that writes
decisions into `CONTEXT.md` and `docs/adr/`; a spec breaks into
tracer-bullet tickets that publish as a chain of contracts (`blocked_by`
links them); review workers run `code-review`, build workers `tdd` then
`code-review`; and the retro applies `writing-for-agents` to the playbook
itself once a week, because every line of it costs on every run.
`docs/agents/` holds the three files that tell the skills where Ivy keeps
its tickets, its labels, and its decisions.

## Rules that don't change

These are marked immutable in `playbook.md`. The weekly retro can tune
timing, wording, and ranking, but it cannot touch these — that needs a
human commit.

1. **Contributions must be real.** No empty commits, no backdating, no
   filler. The failsafe's journal entry is genuine writing about the day.
2. **Verification is external.** "Green" comes from querying GitHub, never
   from a routine's own say-so. Same rule applies to dispatch workers.
3. **Attribution encodes intent.** Bookkeeping commits are authored by
   `ivy-bot` at an address GitHub doesn't recognize, so they never count.
   Only real work and genuine journal entries carry the connected address.
4. **Memory records observations, never instructions.** A page may say
   "nudges on this PR have not converted, 0 of 1 recorded." It may not say
   "stop nudging this PR." Behavior lives in `playbook.md`, and only the
   retro edits it. A memory the agent writes and then obeys is a
   prompt-injection channel with extra steps.
5. **The daily loop outranks everything.** The failsafe secures the day
   before it touches dispatch or memory. A broken sub-system can cost
   routing evidence; it can never cost the streak.

## What it has done

Forty recorded days (23 August–1 October 2026), every one green, 311
contributions. The first twenty were all real work; from 12 September the
failsafe secured twelve of the next twenty. Volume is uneven by nature: 46
contributions one day, 1 the next, and both days cleared the bar. Live
numbers are in `state.json`.

The clearest thing it has caught: on 27 August, six real commits on
`tomgreen.ai` were authored with an email GitHub didn't recognise, so none
of them counted. Git invents `user@hostname.local` silently when identity
is unset, and `git config user.email` reads as merely empty in exactly that
case. The scout spotted it at 07:12 the same morning. Within a day the
scanner had gained a check that uses `git var` instead, the playbook had
been changed to rank attribution failures above every other candidate, the
dispatch layer had gained a gate that refuses to build in a repo that would
author uncountable commits, and the six commits had been rewritten and
recovered. All of it is on the `ops` memory page with citations.

## What isn't working yet

As of 1 October 2026. The failsafe went from never firing to securing twelve
of twenty days. The retros first read that as a Mac outage (the local-WIP
scanner was dark from 9 to 24 September), but the floor kept firing after the
scanner recovered, so the outage explains part of it, not all.

Nudges have not worked: fourteen sent, none converted. And dispatch produces
reviews faster than pull requests get merged. Thirty-four of the first
thirty-eight finished contracts were reviews, and at least 21 of them went to
pull requests that are still drafts, although `dispatch/DESIGN.md` §6 says to
review only non-draft PRs whose head changed.
The one review finding routed into a build (`talent-radar` #7) passed its own
review and is still unmerged.

The next change follows from that: review only what changed or what I ask
for, count merges, and move the nudge to the morning with a link to the pull
request.

## Layout

```
config.yml       schedule, watchlist, lanes, dispatch limits
playbook.md      operating instructions — immutable rules + tunable behavior
CONTEXT.md       the glossary
CLAUDE.md        navigation pointers + agent-skills configuration
.claude/skills/  the vendored skill set; docs/agents/ maps it onto Ivy
state.json       machine-readable daily outcomes
memory/          the knowledge wiki (INDEX, ops, patterns, models, repos/)
journal/         one engineering note per day
dispatch/        work contracts (DESIGN.md, queue/, done/, failed/, reports/)
procedures/      recipes for recurring operational work
routines/        the four cloud routine definitions
scripts/         check.sh, local-wip.py, memory-lint.sh, dispatch-lint.sh,
                 dispatch-runner.py
setup/           launchd jobs and install helpers
```

`DESIGN.md` covers architecture and failure modes. `dispatch/DESIGN.md`
covers the executive layer. `CHANGELOG.md` tracks every version.

## Influences

Two systems shaped this, both credited in the design docs. Perplexity's
Brain gave the memory model: a wiki of linked markdown over raw evidence,
with citations down and context links sideways. Uber's software-factory
write-up validated the dispatch thesis — optimize a fleet of specialized
agents against per-class targets, and cut waste before you ever downgrade a
model.

Neither was copied wholesale. No vector store, no MCP gateway, no benchmark
suite. At this size `grep` over a small git repo is the retrieval layer,
and a capped weekly experiment is the benchmark.
