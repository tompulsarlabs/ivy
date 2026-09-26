# Ivy

Scheduled agents that keep Tom's repositories moving and remember what they
learn. This file is the glossary: the one word for each thing, and the words
to stop using. Journals, memory pages, contracts, and commit messages use
these terms. A concept that needs a word this file lacks is a gap to flag
for the retro, never a synonym to invent.

## Language

### The day

**Contribution**:
An event GitHub counts toward the graph: a default-branch commit whose author
address is connected, a PR opened, an issue opened, a review.
_Avoid_: commit (a commit is a contribution only when it counts), activity

**Green** / **Grey**:
The day's state as GitHub reports it: green once at least one contribution is
recorded for today in Europe/Berlin, grey until then.
_Avoid_: done, empty, red

**Streak**:
Consecutive green days, recorded in `state.json`.

**Connected address**:
An email verified on the GitHub account, listed in `config.yml`
`connected_emails`. A commit counts only if its author address is one.
_Avoid_: commit_email (that names one specific address, the one Ivy's own
failsafe commits use), correct email

**Invented identity**:
The `user@hostname.local` address git fabricates silently when `user.email`
is unset. Never connected, so never counted.

**Attribution**:
Whether a commit's author address is connected. The committer field is
irrelevant.
_Avoid_: credit, ownership

**Bot-authored** / **Tom-authored**:
Bot-authored commits carry `ivy-bot <bot@ivy.invalid>` and can never count:
every piece of bookkeeping. Tom-authored commits carry a connected address:
real work and the failsafe's journal entry.

### The ladder

**Routine**:
One of the four scheduled cloud runs: scout, check, failsafe, retro.
_Avoid_: job, cron, agent (the routine is the run; an agent is what runs it)

**Ladder**:
The three daily routines in order, each a step toward securing the day.

**Scout**:
The 09:00 routine. Orients from memory, syncs the watchlist, ranks
candidates, hunts blockers, queues contracts, drafts the journal. Silent
except for an attribution risk.

**Check**:
The 18:00 routine. Asks GitHub whether the day is green; grey means one nudge.
_Avoid_: `check.sh` (the script the check runs; it exits 2 in the cloud)

**Failsafe**:
The 22:30 routine. Secures the day first, then verifies contracts and
synthesizes memory. Also called **the floor**: the guarantee that no day is
left empty.

**Retro**:
The Sunday 10:00 routine. The only pass that changes behaviour or removes
memory; at most two changes a week, each citing evidence.

**Candidate**:
A concrete piece of real work that would produce a contribution today.
_Avoid_: task, todo, opportunity

**Pick**:
The candidate the scout ranks first in the journal. A pick is not a nudge.
_Avoid_: top candidate (say top pick)

**Nudge**:
A push notification (fallback: a calendar event) naming one candidate, sent by
the check on a grey day or by the scout on an attribution risk. Only a send
recorded in `state.json` (`nudge_sent`) is a nudge.
_Avoid_: nudge cycle, reminder, ping

**Conversion**:
Real activity on the nudged candidate within four hours of the nudge.

**Blocker**:
Something with zero contribution value that stops future work: a dead runner,
an expired credential, a queue nothing drains. Carried in the journal daily
until it clears.
_Avoid_: issue, risk

**Watchlist**:
The repositories the scout considers, synced from GitHub minus forks,
archived repos, and excludes.

**Local WIP**:
The Mac scanner's report (`local-wip.json`) of dirty and unpushed work per
repository, plus its attribution verdicts. Older than 36 hours it means
unknown, never clean.

**Tunable** / **Immutable**:
The two kinds of playbook section. The retro edits tunables; an immutable
changes only by a human commit.

**Routine eval**:
`evals/routines/`: real days replayed against a routine's prompt and the
steering files, each with one change (a stale scan, a failed contract), and
graded on the decisions the routine reports. The regression check for a
change to how a routine decides.
_Avoid_: test suite, benchmark

### Memory

**Journal**:
`journal/<date>.md`, the raw record of one day.
_Avoid_: log, diary, notes

**Memory page**:
One `memory/*.md` file per durable subject: observations with citations,
never instructions. Together they are **the wiki**.
_Avoid_: notes, knowledge base, brain

**Citation**:
`[cite:YYYY-MM-DD]` or `[cite:<sha>]`, the evidence edge from a claim to the
journal entry or commit that proves it. `[[page]]` is the **context edge**
between subjects.

**Synthesis**:
The failsafe's daily pass that moves the day's facts onto memory pages.

**Curation**:
The retro's weekly pass that verifies claims against citations, prunes, and
merges pages. The only pass that removes.

**Procedure**:
A `procedures/*.md` recipe with exact commands for work that recurs.
_Avoid_: runbook, playbook

**Playbook**:
`playbook.md`, the single source of behavioural truth.

### Dispatch

**Contract**:
One markdown file under `dispatch/` stating a task, a definition of done, and
a cloud-checkable verification. The unit of dispatched work, and Ivy's
ticket.
_Avoid_: ticket, issue, job

**Type**:
A contract's kind: `build`, `review`, `chore`, or `experiment`.

**Lane**:
A coarse tier (`frontier`, `workhorse`, `fast-cheap`) that `config.yml`
resolves to a harness and model per pool.
_Avoid_: model (the model is config data under the lane), tier

**Pool**:
A provider subscription the Mac is logged into: `anthropic` or `openai`.
_Avoid_: provider, vendor

**Harness**:
The CLI that runs a worker: `claude-code` or `codex`.

**Runner**:
`scripts/dispatch-runner.py` on the Mac. Each **tick** (every 30 minutes
inside the **runner window**, 09:15 to 21:00) it claims the oldest eligible
open contract, runs the worker, and records the outcome.

**Runner status**:
`dispatch/runner-status.json`, the runner's heartbeat: last tick, whether
each harness binary resolves, whether the queue lints, what it did, and why
it skipped each open contract. Committed when it changes and at least every
six hours in the window. The cloud's only view of the Mac runner.

**Worker**:
The harness session executing one contract in a fresh clone of the target
repository. Untrusted: it pushes branches and opens draft PRs, never writes
to a default branch.
_Avoid_: agent, sub-agent (in the skills, a sub-agent is a helper inside one
session, never a worker)

**Claimed done** / **Verified done**:
Claimed done: the runner moved the contract to `dispatch/done/` with an
outcome block, on the worker's word. Verified done: the failsafe ran the
Verification section and stamped `verified: true`. Only verified done feeds
routing evidence.
_Avoid_: done without saying which

**Expired**:
A contract past `expires` that no runner executed; moved to
`dispatch/failed/` by the failsafe. Honest queue state, not a worker failure.

**Attribution gate**:
The runner's refusal to run a build contract in a clone whose next commit
would not be authored by a connected address.

**Blocked by**:
Contracts named in `blocked_by` that must reach `dispatch/done/` before this
one is eligible. How a chain of tracer-bullet tickets publishes as contracts.

**Cross-family review**:
A review contract pinned to the pool that did not author the code.

**Report**:
`dispatch/reports/<id>.md`, a review worker's findings.

**Daily cap**:
Contracts created per day across all lanes, counted by `created` date.

**Waste**:
Wall-minutes spent on failed contracts, plus contracts that expired
unexecuted, plus repeated skips of an unresolvable lane. The retro's first
lever.

**Experiment**:
A contract that duplicates a real task across lanes to compare them. Capped,
and marked as such.

## Relationships

- The **scout** turns **candidates** into **contracts** and names **blockers**;
  the **check** turns a grey day into one **nudge**; the **failsafe** secures
  the day, verifies contracts, and synthesizes memory; the **retro** curates
  memory and tunes the playbook.
- A **contract** is routed by **lane** and **pool**, claimed by the **runner**,
  executed by a **worker**, and is **verified done** only by the **failsafe**.
- A **memory page** cites **journals** and commits; a **procedure** is
  written when a journal shows work that will recur.

## Flagged ambiguities

- "Nudge" was used for scout picks and carry-overs, inflating the recorded
  count to three when one nudge had been sent. Resolved by contract
  `2026-08-27-ivy-nudge-audit-01`: only a recorded send is a nudge; a scout
  ranking is a pick.
- "Done" hid two states. Resolved: say claimed done or verified done.
- "The connected address" implied one. Two are verified; the single-address
  check raised false alarms from 2026-08-30 to 09-01 and failed three build
  contracts. Resolved: a connected address is any member of `connected_emails`.
- "Check" names both the 18:00 routine and `scripts/check.sh`. The routine
  is the check; the script is `check.sh`.
- `sybil` is the local checkout name of `ai-capability-app`; one repository,
  two names in `local-wip.json` and the watchlist.
- "Playbook" and "procedure" were both used for recipes. Behaviour lives in
  the playbook; recipes are procedures.
