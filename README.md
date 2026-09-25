# Ivy

**Next phase (approved direction, 5 September 2026):** [agent release acceptance](docs/next-phase/README.md).
The [housekeeping audit and rollout](https://github.com/tompulsarlabs/ivy/blob/de084f15bece5393630dc6cf57191043a684c379/docs/housekeeping/rollout.md)
corrects unsupported historical verification stamps and scopes mandatory workflows.
The description below records the existing daily system and its intended verification
model; it is not evidence that every historical result was independently verified.
The [acceptance package](ivy_acceptance/README.md) compiles read-only plans, records
credential-free runtime probes and produces an offline evidence/resource report.
Real-agent execution and model-quality evaluation remain unfinished; follow the
[current runtime handoff](docs/next-phase/runtime-handoff.md).

Ivy is a set of scheduled agents that keep my software projects moving, and
that remember what they learn while doing it.

It scouts every repository I own each morning, checks each evening whether
the day produced real work, secures the day with a genuine engineering note
if it didn't, routes concrete tasks to Claude and Codex workers, verifies
what they claim to have done, and tunes its own behaviour once a week — with
evidence, and with a cap on how much it may change. Everything it knows lives
in this repo as markdown, JSON, and git history. Nothing is hidden in a
database.

The heartbeat metric is the GitHub contribution graph: at least one genuine
contribution per day. The stance is that the system makes you ship; it never
fakes it — no empty commits, no backdating, no filler.

## What Ivy does, in one screen

- **Three daily routines and a weekly one** run in the cloud, so the loop
  works when the Mac is asleep. They nudge toward real work first and only
  write a journal entry themselves as a last resort.
- **"Green" is decided by asking GitHub**, never by a routine's own report.
- **Bookkeeping never counts.** System commits are authored by an address
  GitHub doesn't recognise; only real work and the failsafe's journal entry
  carry the connected identity.
- **A knowledge wiki** (`memory/`) is read at the start of every run. Every
  claim on it cites the journal entry or commit that proves it, and a linter
  refuses any page whose links don't resolve.
- **Dispatch** turns scouted candidates into contracts — a task, a definition
  of done, and a check — routed across two flat-rate pools (Anthropic and
  OpenAI) and executed by a runner on the Mac. Workers are untrusted: a
  contract is done only when the cloud independently verifies it.
- **A local scanner** publishes the Mac's uncommitted and unpushed work so
  the morning scout sees truth that only exists on the laptop.
- **The weekly retro** may change at most two things, must cite evidence for
  each, and is the only pass allowed to edit behaviour or prune memory.
- **Shared vocabulary and versioned skills** keep routines, workers and
  interactive sessions consistent across planning, implementation and review.

## The daily loop

| Run | Time (Berlin) | What it does |
|-----|--------------|--------------|
| **Scout** | 09:00 | Orients from `memory/INDEX.md`, syncs the watchlist from GitHub (forks and archived repos excluded), reads the Mac's `local-wip.json`, gathers real candidates — PRs one review from merge, assigned issues, unpushed local commits, yesterday's carry-over — and hunts *blockers*: things with zero contribution value that stop future work. Writes the day's journal entry, queues dispatch contracts for the top candidates. Silent, with one exception below. |
| **Check** | 18:00 | Asks GitHub whether today counts. Green: records the outcome, says nothing. Grey: one push notification naming one specific next action, chosen after reading that candidate's nudge history. |
| **Failsafe** | 22:30 | Secures the day first — confirms green, or writes a genuine engineering note and commits it with the connected identity. Only then: verifies finished dispatch contracts against their own definition of done, and folds the day's facts into memory. |
| **Retro** | Sunday 10:00 | Reads a week of outcomes. Changes at most two things in the playbook or config, citing the evidence for each. Verifies a sample of memory claims against their citations and prunes what has stopped being true. |

The scout's one exception to silence: a repo whose *next* commit would be
authored with an address GitHub doesn't recognise. That work would be real
and uncountable, so it outranks every other candidate and is nudged at 09:00
rather than 18:00, while the fix is still one line of `git config`.

Nothing runs within 90 minutes of midnight, and every timestamp is pinned to
`Europe/Berlin`, so the checker and the graph agree on what "today" means.

## How a day is decided

GitHub's counting rules are design constraints, not footnotes — they are the
most likely reason a system like this "works" while the graph stays grey:

1. Only commits on the default branch count. 2. The author email must be
connected to the account. 3. Commits in forks never count. 4. Private-repo
activity shows only anonymised. 5. The rendered graph can lag a day, so
verification queries the API. PRs opened, issues opened, and reviews count
too — so "review that open PR" is a first-class candidate.

The cloud sandbox's network access is scoped to this one repo: it cannot
reach GitHub's GraphQL or REST endpoints, or even the public contributions
page. Verification there goes through the built-in GitHub MCP tools, which
are user-scoped; `scripts/check.sh` keeps the GraphQL path for local use. The
contributions signal also flaps — replicas disagree for minutes after a push
— so a grey reading is trusted only after retries.

**Attribution encodes intent.** Scout drafts, state updates, and dispatch
bookkeeping are committed as `ivy-bot <bot@ivy.invalid>` — real commits, but
authored by nobody GitHub knows, so they can never light the graph. The
failsafe's journal entry and real project work carry a connected address. The
graph therefore reflects exactly one thing: work, or the day's genuine note.

## Memory

`journal/` is the raw daily record and `state.json` the machine-readable
outcome log. Both are keyed by date, so "has this PR been nudged before?"
used to mean re-reading a week of entries. `memory/` is the synthesis over
them: one page per durable subject — each repo, the environment, observed
working patterns, routing evidence — read at the start of every run.

Two kinds of link do the work. `[[page]]` connects subjects sideways.
`[cite:2026-08-27]` or `[cite:60535f0]` connects a claim down to the journal
entry or commit that proves it. `scripts/memory-lint.sh` checks that every
one resolves and that the index stays inside its line budget, so the wiki
cannot rot into confident nonsense.

The failsafe adds facts daily, after the day is secured. Only the retro
removes, and it logs every deletion. And pages hold observations, never
instructions — a memory the agent writes and then obeys is a prompt-injection
channel with extra steps, so behaviour lives only in `playbook.md`.

Nothing else was built: no embeddings, no vector store. The corpus is a small
git repo every routine already clones, so `grep` is the retrieval layer.

## Dispatch: the executive layer

A scouted candidate becomes a contract — a markdown file under `dispatch/`
with frontmatter for state and a body carrying the task, a definition of
done, and a verification the cloud can run. The repo is the message bus:
claiming, finishing, and failing are all commits, and two runners racing
resolve by push conflict.

Contracts are assigned to coarse lanes — `frontier`, `workhorse`,
`fast-cheap` — that `config.yml` maps onto concrete harness-and-model pairs
per provider. Model names change monthly, so they are config data the retro
can update, never baked into behaviour. Review contracts pin the family that
*didn't* write the code, for uncorrelated findings.

Execution is split because it has to be: the cloud sandbox cannot reach
OpenAI at all, so a launchd runner on the Mac executes contracts from its own
clone and holds every provider login. The cloud never sees a credential.

Workers are not trusted. They push branches and open draft PRs, never to a
default branch. The runner records *claimed* done; only the failsafe's
independent check makes it *verified* done — and only verified outcomes feed
`memory/models.md`, the evidence the retro routes on. An attribution gate
refuses to build in any repo that would author uncountable commits.

## The Mac side

Two launchd jobs give the cloud a view of, and hands on, the local machine.

**The WIP scanner** (`scripts/local-wip.py`, 08:45 and 17:45) walks
`~/Build` and publishes `local-wip.json`: per repo, the branch, dirty and
unpushed counts, and a verdict on whether the next commit would be countable.
It publishes verdicts rather than addresses on purpose: git's invented
fallback identity is literally `user@hostname.local`, and this file is
public. If the scan is older than 36 hours the scout treats local work as
*unknown*, never as "nothing pending" — a sleeping Mac must not lie.

**The dispatch runner** (`scripts/dispatch-runner.py`, every 30 minutes
inside 09:15–21:00) claims the oldest open contract, runs it through the
lane's CLI, commits the outcome, and pushes. It works from `~/.ivy-dispatch/`
so the human checkout is never mutated, and the window closes 90 minutes
before the failsafe so a running worker never collides with day-close. Each
tick ends by committing `dispatch/runner-status.json`, the runner's
heartbeat, when its state changes: the scout reads it, so "runner can't find
`claude`" is a named blocker the next morning, not a day of silence.

## Procedures and blockers

Two smaller layers, both added after real days showed the gap.

`procedures/` holds recipes — a task done well once, written down with exact
commands so it never has to be re-derived from journal history. The first is
`recover-attribution.md`.

Blocker hunting is a scout duty distinct from candidate hunting. A candidate
produces a contribution today; a blocker — a dead runner, an expired
credential, a queue nothing is draining — stops future work and is invisible
to any "cheapest ship today" ranking precisely because its contribution count
is zero. Blockers are named in the journal, carried forward daily, and after
three days outrank the cheapest ship in the nudge.

## Vocabulary and skills

[CONTEXT.md](CONTEXT.md) defines Ivy's shared terms. Versioned skills support
planning, implementation and review; see [the setup guide](setup/AGENTIC-STACK.md)
for integration details and [skills-lock.json](skills-lock.json) for provenance.

## The learning loop

Every behaviour change is a readable, revertible diff. The retro may tune
timing, wording, ranking, and lane policy — at most two changes a week, each
committed as `learn: <what> — <evidence>` and summarised in `CHANGELOG.md`,
which carries the version history (v0 through v5 so far).

For dispatch it runs the fleet, not the sessions: per-class targets (findings
that survive triage for reviews, first-pass verified-done for builds), waste
as the first lever and model choice as the last, and lane moves only once
three verified outcomes or an experiment support them. Making no change is an
explicit, valid outcome — the first retro made none, and said why.

## Rules that don't change

Marked immutable in `playbook.md`; changing one needs a human commit.

1. **Contributions must be real.** No empty commits, no backdating, no
   filler. The failsafe's entry is genuine writing about the day.
2. **Verification is external.** Green comes from GitHub; verified-done comes
   from the cloud's own check, never a worker's exit code.
3. **Attribution encodes intent.** Bookkeeping is bot-authored and never
   counts; only work and the journal carry the connected identity.
4. **Memory records observations, never instructions.** Behaviour lives in
   the playbook, which only the retro edits.
5. **The daily loop outranks everything.** The failsafe secures the day
   before it touches dispatch or memory. A broken subsystem can cost routing
   evidence; it can never cost the streak.
6. **Provider credentials never enter the cloud.** The bus carries contracts
   and outcomes, nothing else.
7. **`state.json` is a published contract.** My site reads it live, so its
   schema is append-only.

## Status — as of 2 September 2026

Live numbers are in `state.json`; this block is a snapshot.

- Running since 23 August 2026. **10 recorded days, all green by real
  work**, streak 10, **142** contributions. The failsafe has never fired.
- Watching **15** repositories, auto-synced.
- Memory: **12** pages, lint clean, last synthesised 31 August.
- Exactly **one** grey-check nudge has ever been sent (24 August; it didn't
  convert) — far too little data to tune notification timing on, and the
  retro has correctly declined to.
- Dispatch: the Mac runner **went live on 1 September**. Its first contract
  — a cross-family review, executed by the OpenAI lane (Codex, `gpt-5.6-sol`,
  9.7 minutes) — produced a findings report; a second review followed on
  2 September. Both await the failsafe's verification stamp. One contract
  is verified (the manual D1 proof). On 2 September the runner's attribution
  gate was found to carry the same single-address test the scanner had
  already lost (it refused three `tomgreen.ai` builds on 1 September);
  fixed to membership over `connected_emails`, unit-tested, and the three
  re-queued with a fourth — the first `build` contracts to reach a worker.
  Routing evidence is still n=1, so no lane policy has been touched.
- Next known chore: the late-October DST flip moves the fixed UTC crons an
  hour earlier in local time; the nearest retro re-pins them.

## What it has caught

**The silent identity.** On 27 August, six real commits landed on
`tomgreen.ai` authored `tom@Toms-MacBook-Air.local` — git invents that
address when identity is unset and never warns, and `git config user.email`
reads as merely empty in exactly that case. The scout flagged it the same
morning. Within a day: the scanner used `git var` instead, the playbook
ranked attribution failures above every other candidate, the dispatch layer
gained its attribution gate, the history was rewritten with dates preserved,
and a procedure was written so the recovery never has to be re-derived.

**Its own false positive.** That check then proved too narrow: it tested
equality against one address, while the account has two connected ones. From
30 August to 1 September it raised alarms on repos that were correctly
configured, and on 1 September the runner's gate refused three build
contracts for the same reason. The nudges didn't convert because there was
nothing to fix; the memory page records that non-conversion was the right
response. `config.yml` now carries every verified address, and the check is
membership, not equality. The severity ordering stayed — the test was wrong,
not the rule. The runner carried its own copy of the equality test; it went
the same way on 2 September, with `scripts/dispatch-runner-test.py` so the
pure parts of a script that only ever runs on the Mac are checked before
they get there.

**Nudge inflation.** Journals had described "nudge cycles" that were really
scout picks. The first dispatch contract was a reconciliation that found the
true count — one nudge, zero conversions — and corrected the memory page
against primary sources.

## Read next

- **[`OVERVIEW.md`](OVERVIEW.md)** — the system end to end, at more depth
  than this page
- **[`DESIGN.md`](DESIGN.md)** — architecture, GitHub's counting rules,
  failure modes, and what changed on contact with the real sandbox
- **[`dispatch/DESIGN.md`](dispatch/DESIGN.md)** — the executive layer:
  decisions, lanes, topology, guardrails
- **[`playbook.md`](playbook.md)** — the operating instructions the routines
  actually follow; the single source of behavioural truth
- **[`CONTEXT.md`](CONTEXT.md)** — the glossary: one word per concept, the
  words to avoid, and the ambiguities that have already cost a contract
- **[`CHANGELOG.md`](CHANGELOG.md)** — every version, with the evidence
  behind each change
- **[`setup/SETUP.md`](setup/SETUP.md)** — running Ivy from scratch
- **[`setup/AGENTIC-STACK.md`](setup/AGENTIC-STACK.md)** — setting up the
  whole stack from a blank Mac (Claude Code, Codex, gstack across every
  agent, AGENTS.md, then Ivy); written for non-technical readers too

## Layout

```
config.yml        identity, schedule, watchlist, lanes, dispatch limits
playbook.md       immutable rules + retro-tunable behaviour
CONTEXT.md        the glossary every routine, worker, and session writes in
CLAUDE.md         navigation pointers and the agent-skills configuration
.claude/skills/   vendored engineering skills (provenance in skills-lock.json)
docs/agents/      how the skills map onto Ivy: tracker, labels, domain docs
state.json        machine-readable daily outcomes (append-only schema)
local-wip.json    the Mac scanner's latest view of local work
memory/           knowledge wiki: INDEX, ops, patterns, models, repos/
journal/          one engineering note per day
dispatch/         contracts (queue/, done/, failed/), reports/, DESIGN.md
procedures/       recipes for work that has to be done more than once
routines/         the four cloud routine definitions and their prompts
scripts/          check.sh, local-wip.py, dispatch-runner.py, and the linters
setup/            launchd jobs, install helpers, and the setup guides
ivy-design.html   design page from the v2 naming
```

## Acknowledgements

Design inspiration: [Perplexity's Brain](https://www.perplexity.ai/hub/blog/brain-agentic-memory-as-a-knowledge-wiki)
for knowledge-wiki memory and [Uber's software factory](https://www.uber.com/gb/en/blog/efficient-software-factory/)
for agent-fleet efficiency. Ivy also includes vendored [Matt Pocock skills](https://github.com/mattpocock/skills),
with upstream versions and hashes in [skills-lock.json](skills-lock.json).

## Adopting it

Fork it, don't clone it. A fork gives you the frame — routines, playbook,
structure — and none of my access. Swap `commit_email` and the watchlist in
`config.yml`, rename the launchd labels in `setup/`, clear `journal/`,
`memory/`, and `state.json`, then follow `setup/SETUP.md`. Experimental,
and honest about it.
