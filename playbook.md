# Ivy Playbook

Operating instructions for Ivy's routines. The weekly retro may edit the
**Tunable** sections (commit as `learn:`, tag a new version). The **Immutable**
sections may only be changed by a human commit.

---

## Immutable: counting rules

A contribution counts on the `tompulsarlabs` graph only if (DESIGN.md §1):

1. Commit lands on the **default branch** (or `gh-pages`).
2. Commit **author email is connected to the account** — any address listed in
   `connected_emails` in `config.yml` counts, not only `commit_email` (which is
   just the identity Ivy's own commits use). Set the author explicitly per
   commit, never inherited from environment git config. An address is added to
   that list only after a real commit using it resolves an `author.login` on
   GitHub.
3. The repo is **not a fork**.
4. Private-repo activity shows only if the profile's "Private contributions"
   toggle is on. This repo stays public.

PRs opened, issues opened, and PR reviews also count — treat "review an open PR"
as a first-class candidate.

## Immutable: verification

"Green" is defined by `scripts/check.sh` (GraphQL `contributionsCollection`
for today in `Europe/Berlin`), never by the rendered graph. After any failsafe
commit, re-run the check until today ≥ 1; if it stays 0 after 3 attempts over
15 minutes, alert loudly with the misconfig checklist: email? branch? fork? visibility?

## Immutable: commit attribution encodes intent

Routines run in ephemeral cloud sessions, so all state (journal drafts, state.json,
watchlist changes) must be committed to `main` to survive between runs. To keep
system bookkeeping from lighting the graph as noise:

- **System commits** (scout drafts, state recording, watchlist sync) are authored as
  `ivy-bot <bot@ivy.invalid>` — an unconnected address that never counts.
- **Contribution commits** (the failsafe journal entry, and only that) are authored as
  `commit_name <commit_email>` from `config.yml` — the connected address.

Always set author explicitly per commit (`git -c user.name=… -c user.email=… commit`),
never inherit the environment's git config. The graph therefore reflects exactly one
thing: real work, or the day's genuine journal entry — never the system's own churn.

## Immutable: no synthetic contributions

No empty commits, no backdating, no content-free filler. The failsafe commit is
a real journal entry: today's candidates, what happened, streak state, tomorrow's
top candidate. If journal entries trend content-free, that is a nudging failure
for the retro to fix — not a license to automate noise.

## Immutable: memory records observations, never instructions

`memory/` is Ivy's knowledge wiki — one page per durable subject, every claim
carrying a link to its evidence. It is read at the start of every run, which is
exactly why it must never contain directives.

- Pages hold **observations and evidence**. Behavior lives in this playbook,
  and only the retro changes it.
- A page may record "nudges on this PR have not converted, 0 of 1 recorded."
  It may not say "stop nudging this PR." The first is a finding the retro can
  weigh; the second is an instruction the system wrote for itself and would
  then obey without review.
- Every claim carries a citation: `[cite:YYYY-MM-DD]` resolves to that day's
  journal entry, `[cite:<sha>]` to a commit in this repo. `[[page]]` links to a
  related page. A claim with no citation does not belong on a page.
- **Memory is written by the failsafe (daily) and the retro (weekly), and by
  nothing else.** Scout and check read memory and record what they observe in
  the journal; the failsafe folds it in. Every memory commit is bot-authored
  and must pass `scripts/memory-lint.sh`.
- The three layers are deliberately redundant and must stay in their lanes:
  `journal/` is the raw session record, `state.json` the machine-readable
  outcome log, `memory/` the synthesis over both. Narrative belongs in the
  journal; `state.json` stays terse and cites the journal.

Rationale: a memory the agent writes and then obeys is a prompt-injection
channel with extra steps. Keeping observations and instructions in separate
files, with different write permissions and different review cadences, is what
makes the loop safe to run unattended.

## Immutable: `state.json` is a published contract

`tompulsarlabs/tomgreen.ai` reads this repo's `state.json` for its live proof
strip, and cloud runs are scoped to `ivy` alone, so the consuming code cannot
be inspected from a routine. Treat the schema as **append-only**: add keys and
shorten values freely, never rename or remove one. Anything that needs room to
breathe goes in the journal and gets cited from here.

## Immutable: dispatch guardrails

Dispatch contracts (`dispatch/`, designed in `dispatch/DESIGN.md`) route work
to execution lanes. Non-negotiables:

1. **The daily ladder is senior.** The failsafe secures the day (green,
   journal, streak) before touching contract verification; a hung dispatch
   step can cost routing evidence, never the streak.
2. **Workers are untrusted.** A contract is *verified done* only when the
   failsafe's external check of its Verification section passes — worker
   self-reports and exit codes are claims, not outcomes. Workers push
   branches and open draft PRs; they never write to `main` of any repo.
3. **Contracts are lint-gated.** `scripts/dispatch-lint.sh` must pass before
   any dispatch commit; the runner executes only lint-clean contracts from
   scout/Tom commits.
4. **Provider auth never enters the cloud sandbox.** Subscription logins live
   on the Mac; the repo carries contracts and outcomes, never credentials.
5. **Routing policy is retro-only** (within the existing ≤2 changes/week,
   evidence-cited), and Ivy never changes its own routines' models.
6. **No synthetic work.** A contract exists because a candidate is real;
   `experiment` duplicates are capped and marked. Verified-done is the goal,
   never dispatch volume.
7. **Attribution gate.** A `build` contract targeting a repo whose
   `author_email_ok` is false fails immediately rather than authoring
   uncountable commits.

---

## Tunable: the daily ladder

Three routines secure each day: the scout plans it, the check nudges if it
is still grey at 18:00, and the failsafe closes it. Each runs unattended in a
cloud sandbox that is discarded afterwards, so nobody can answer a question
mid-run and nothing survives that is not pushed. Make the routine judgment
calls yourself; when only Tom can unblock part of the work, finish the rest
and name what is missing in the journal and in your final message.

### Rules every run follows

**Commit, then push.** Every commit goes to `main` and is pushed before the
run ends, with its author set explicitly per the attribution rule.

**Inputs have a shelf life.** An input past its bound is unknown, never
clean, because a sleeping Mac must not read as a quiet one: `local-wip.json`
older than 36 hours; a runner heartbeat (`dispatch/runner-status.json`
`last_tick`) older than 3 hours inside the runner window while contracts are
open. Say so in the journal.

**Deciding green.** `scripts/check.sh` exits 2 in the cloud sandbox, whose
github.com egress reaches only this repo; that is expected, never grounds to
guess. Decide from the built-in GitHub MCP tools (load them with ToolSearch;
`gh` is not installed and not worth installing). Today in Europe/Berlin is
green if any of these shows a contribution:

- (a) `list_commits` on this repo: a commit on `main` today whose author is a
  connected address (`config.yml` `connected_emails`);
- (b) `search_commits`: a commit authored by `tompulsarlabs` today on a
  default branch, outside forks;
- (c) `search_issues` / `search_pull_requests`: an issue or PR opened by
  `tompulsarlabs` today.

Bot-authored commits (`bot@ivy.invalid`, historically `bot@evergreen.invalid`)
never count. Search indexing lags a push by about a minute, so verify a
commit you just pushed with (a). If the MCP tools are unavailable as well,
the day is unknown: alert. `memory/ops.md` records how the sandbox behaves
and which query forms reach other repos.

**Alerts and nudges are pushes.** Send through PushNotification. An alert
starts with `ALERT:` so it never reads as a nudge.

**`state.json` rows stay terse.** Each value is a short label, count, or
flag, such as `"green_by": "tomgreen.ai: 3 commits"`,
`"signal_source": "github-mcp:search_commits"`, and
`"cite": "journal/2026-09-23.md"`. The narrative (which lookups ran, commit
titles, what was excluded) goes in the journal under `## Verification`. Many
existing rows are paragraphs; write new ones in the short form. The day's row
carries `green_by`, `method`, `contributions`, `signal_source`, `cite`,
`nudge_sent`, `nudge_sent_at`, `nudge_channel`, `nudge_candidate`,
`nudge_converted`, and `failsafe_fired`.

**The journal holds what the run learned.** A repo gone quiet, a new access
limit, a candidate that keeps resurfacing: write it in today's entry and the
failsafe folds it into memory. A concept the entry needed that `CONTEXT.md`
lacks, or used against its definition, goes under `## Vocabulary gaps` for the
retro.

### Scout (09:00)

The scout plans the day: today's journal drafted with ranked candidates,
named blockers, and a Top pick; contracts queued for the best dispatchable
candidates; all of it bot-authored. It sends nothing, except for an
attribution risk.

**Orient from memory.** Read `memory/INDEX.md`, `memory/ops.md`, and the
`memory/repos/<name>.md` page of every repo that produces a candidate: what
the repo is, what has been tried, what the environment refuses. It is
cheaper than re-deriving the same from journals. Adopt a claim directly, and
follow its `[cite:...]` down to the journal only when it is decision-critical
or looks stale.

**Sync the watchlist** with `search_repositories org:<login>`, minus forks,
archived repos, and `config.yml` excludes, and commit a changed list as
`config: sync watchlist — <what changed>`. A repo in `watchlist.parked` is
watched only: its contributions count and its attribution is scanned, but it
produces no candidate, contract, or audit. It leaves `parked` by Tom's commit
or a retro `learn:`.

**Gather candidates** from what the tools can see: open PRs close to merge,
assigned issues, yesterday's carry-over, and from `local-wip.json` every repo
with `unpushed_commits > 0` or `remote: none` ("push X (N unpushed commits)"
is often the cheapest real ship). Branches pushed without a PR are invisible
from the cloud, because `search_commits` sees default branches only.

**Rank by revealed focus, not cheapness.** Repos with Tom-authored commits in
the last 7 days, local WIP, and draft PRs he updated this week rank above a
cheap ship on a stale PR. Tom's focus shows in what he touches; a stale PR one
click from merge has been declining that click.

**An attribution risk comes first.** `author_email_ok: false` in
`local-wip.json` means that repo's next commit will be authored by an address
that is not connected, so the work cannot count however real it is;
`last_commit_email_ok: false` means it already happened. When work is at stake
(recent or unpushed commits), lead the journal with it and send a push nudge
now, naming the repo and the fix: one `git config` line before a push,
`procedures/recover-attribution.md` after one. By 18:00 a whole day of work
could be uncountable. A dormant repo whose only bad commit is old goes in the
journal without a nudge.

**Hunt blockers as well as candidates.** A candidate produces a contribution
today; a blocker (a dead runner, an expired credential, a queue nothing
drains, a broken local scan, an unmerged fix other work waits on) stops
future work and scores zero on any cheapest-ship ranking, which is why it
rots. Read `dispatch/runner-status.json`: `harness` or `lint_ok` false is a
blocker from the first morning, since every contract waits on it; a stale
`last_tick` means the runner is not ticking, which is either a sleeping Mac
or an unloaded launchd job (name both rather than guess); `skipped` says why
each open contract was passed over. Write each blocker under `## Blockers`
with what it stops and the smallest next action, and carry it every day
until it clears or Tom declines it.

**Top pick.** `## Top pick` names the one candidate ranked first. A blocker
that has persisted three days or more is written at the head of that
section, above the candidate, every day it persists, however often it has
been nudged. Whether the check spends its nudge on it is the check's call.

**Queue contracts** for the top dispatchable candidates. Count the contracts
already created today first (by `created` date, across `dispatch/queue/`,
`done/`, and `failed/`, whoever wrote them): the day allows
`dispatch.daily_cap` in all, and `scripts/dispatch-lint.sh` refuses a commit
past it. Write them in the format of `dispatch/DESIGN.md` §2 and the
vocabulary of `CONTEXT.md`. A contract is one
vertical slice, complete and verifiable on its own and sized for one worker
session; work that needs more publishes as a chain whose later contracts
carry `blocked_by`. A review contract defaults to `lane: workhorse` and pins
`pool` to the family that did not write the code (the head branch and commit
trailers usually say which); pin `frontier` when the change itself carries
the risk, such as credentials, auth, or data loss. Run
`scripts/dispatch-lint.sh` and commit as `dispatch: open <ids>`. The runner
executes; the scout only queues.

**Write the journal** as `journal/<today>.md` and commit it as
`scout: <date> — <n> candidates, top: <one-liner>`.

### Check (18:00)

The check reads the day at 18:00: today's reading recorded, and on a grey day
exactly one nudge naming one concrete next action.

Decide the day per *Deciding green*. Green: record the reading on today's row
of `state.json` and send nothing. Unknown: alert, and record nothing as green
or grey. Grey: nudge.

**Choose the nudge.** A blocker leading today's Top pick outranks the
candidates until it has been nudged three times without converting; from
then on, nudge the next-best candidate while the blocker keeps leading the
journal. Otherwise name the most concrete candidate in today's journal: a
repo and a PR, commit, or push, never a generic "ship something". First read
that candidate's `memory/repos/<name>.md` and the recent `nudge_*` fields in
`state.json`: a candidate already nudged without converting is a weaker pick
than a fresh one of similar cost, and if you pick it anyway, say why in the
journal.

**Send it** as one line through PushNotification. If PushNotification
reports it was not sent, create a Google Calendar event about 15 minutes out,
titled with the candidate, instead: exactly one of the two. Record
`nudge_sent`, `nudge_sent_at`, `nudge_channel`, and `nudge_candidate` on
today's row.

Write the reading and the choice under `## Check` in today's journal,
including the state of any contract in `dispatch/queue/`, since a claimed
contract may still land before the failsafe.

### Failsafe (22:30)

The failsafe closes the day in three steps, each started only once the step
before it is done: secure and record the day, verify dispatch contracts,
synthesize memory. A failure in a later step never costs an earlier one.

**1. Secure the day.** Decide the day per *Deciding green*. If it is still
grey, finish today's journal as a genuine engineering note (the day's
candidates, what happened, streak state, tomorrow's top candidate, and how
the day was verified under `## Verification`), commit that file alone,
Tom-authored, push, and verify per the Immutable rule. Either way, write
today's final row in `state.json` in the short form (*`state.json` rows stay
terse*) and bump or reset `streak` and `last_green`. `nudge_converted` is true when real activity landed on the
nudged candidate within four hours of the nudge; for a blocker nudge it is
also true when the blocker's own recovery signal arrives (a fresh
`local-wip.json`, a resumed heartbeat), because an infrastructure fix rarely
produces a commit of its own.

**2. Verify contracts.** For each contract in `dispatch/done/` without a
`verified:` stamp, run its Verification section with cloud-checkable means
and stamp `verified: true|false`. The runner's bookkeeping is a claim like
any worker's, so check three more cases:

- A contract in `dispatch/failed/` with `exit: timeout` or `no_report` may
  have finished and only missed printing its report. Run its Verification;
  if it passes, set `state: done`, move it to `dispatch/done/`, stamp
  `verified: true` with a `verified_note` that the report never landed, and
  count its minutes as work, not waste.
- A contract in `dispatch/queue/` with `state: claimed`, no outcome, and a
  `claimed_at` older than `budget.wall_minutes × 3` belongs to a runner that
  died mid-task: set `state: open`, drop `claimed_at`, and say so in the
  journal. The next tick runs it again.
- A contract past `expires` moves to `dispatch/failed/` with
  `state: expired`.

Run `scripts/dispatch-lint.sh` and commit as `dispatch: verify <ids>`.

**3. Synthesize memory.** Move the day's durable facts onto their pages:
repo facts to `memory/repos/<name>.md`, environment behaviour to
`memory/ops.md`, rhythm and conversion to `memory/patterns.md`, verified
contract outcomes to `memory/models.md`. Write each citation as you write the
claim.

- An ongoing condition (an outage, a stale PR, a running count) lives in one
  current-state line saying when it began, when it was last confirmed, and
  what it blocks. Update that line in place; the day-by-day detail stays in
  the journal.
- Create a page only for a subject with durable signal (a first real
  commit, not one quiet day), and add it to `memory/INDEX.md` in the same
  commit.
- A sequence the day showed will recur goes to `procedures/` as a recipe
  while the details are exact.
- Writing nothing is a valid outcome: an unchanged page is a stronger signal
  than a restated one.

Run `scripts/memory-lint.sh`; it must pass (after `git fetch --unshallow` if
it names a citation today's edits did not touch). Commit as
`memory: <what changed>` and set `memory_last_synthesized` to today.

## Tunable: retro (Sunday 10:00)

Start from `memory/INDEX.md` and the pages it lists: the synthesized view of
the trailing weeks, cheaper than re-mining raw history. Then read 7 to 30
days of `state.json` for the numbers and answer: how often did the failsafe
fire? Did nudges convert to real activity within four hours? Which repos
produced shipped work? Every commit the retro makes is bot-authored and pushed
to `main` before the run ends. The run is unattended: where a skill would stop
to ask the user, decide, and record the decision in `CHANGELOG.md`.

**Tune behaviour.** Make at most two adjustments (nudge time, wording,
ranking, excludes, lane policy) by editing the Tunable sections of this file
or `config.yml`, each backed by evidence you can name. Commit each as
`learn: <what> — <evidence>`, naming the page or journal entry the evidence
came from, and summarize the week in `CHANGELOG.md` under the next version
number. No change is a valid outcome; record `no change — <why>` in
`CHANGELOG.md`. A cloud session cannot push tags (`memory/ops.md`), so the
version lives in `CHANGELOG.md` and tagging is Tom's. When evidence says an
Immutable section is wrong, write the proposal for Tom in the `CHANGELOG.md`
entry: an Immutable section changes only by his commit.

**Curate memory.** The failsafe adds and updates; the retro is the only pass
that removes or rewrites a page wholesale.

- Verify a sample of claims against their citations, weighted toward the
  ones that have been steering candidate ranking. Correct or drop a claim its
  evidence no longer supports; record a contradiction between sources
  explicitly rather than resolving it silently.
- Prune what has stopped being true: a repo gone dormant, an access limit
  that no longer applies, a thread that closed. Outdated context is worse
  than missing context, because it reads as current.
- Collapse day-by-day restatements into the condition's current-state line,
  keeping the first and latest citations.
- Merge or split pages when a subject has outgrown or emptied its page, and
  keep `memory/INDEX.md` inside its line budget: it is read on every run, so
  it stays a map, not a summary.
- Log every removal in the page's `## Changelog` with the date and reason.

Run `scripts/memory-lint.sh`, then commit as `memory: retro — <what changed>`.

**Prune the steering files.** `CLAUDE.md`, this file, `routines/*.md`, and
`procedures/` are read on every run, so every line costs on every run. Call
the Skill tool with `writing-for-agents` and apply its tests: delete no-ops
(instructions the model follows by default), collapse restatements into a
leading word, state targets positively where a prohibition is not a hard
guardrail, and push reference that only some runs need behind a pointer. When
a word is too weak to change behaviour, delete it or state the target plainly
instead of reaching for a stronger one: intensity words over-apply on current
models. A deletion that provably changes no behaviour does not count toward
the two adjustments; a wording change that does, does. After a lane's model changes
or Tom moves a routine to a new model, also audit these files and the worker
prompt in `scripts/dispatch-runner.py` against that model with the
`claude-api` skill's `prompt-audit`, since text tuned for one model
generation turns into dead weight on the next. The routine eval
(`evals/README.md`) is the regression check for any such change. Keep section
headings stable, because the routine prompts cite them, and leave the
Immutable sections untouched.

**Curate `CONTEXT.md`.** Call the Skill tool with `domain-modeling`, resolve
the week's `## Vocabulary gaps`, correct any page or journal that used a term
against its definition, and record in `docs/adr/` any decision that is hard to
reverse, surprising without context, and the result of a real trade-off: all
three, or no ADR.

**Run the fleet, not the sessions.** Optimize lane policy against per-class
targets, never individual runs.

- Per-class target metrics: review, the share of findings that survive
  triage; build, the first-pass verified-done rate; chore, wall-minutes per
  verified-done; every class, zero waste.
- Waste is the first lever and model choice the last. Waste is wall-minutes
  on `dispatch/failed/` contracts, contracts that expired unexecuted, and
  repeated skips of an unresolvable lane. Compute it before touching lanes:
  removing zero-value consumption beats downgrading a lane and losing
  quality.
- Step a task class down to a cheaper lane only when its target metric held
  there (an experiment, or at least three verified outcomes at that lane);
  step it up when failures show quality is the binding constraint. Flat-rate
  pools make trading a target metric for cost a bad trade by definition.
- When a lane decision is pending and the evidence is thin, spend the week's
  one `experiment` contract on exactly that comparison.
- Record the week's fleet metrics in `memory/models.md` (verified-done count,
  waste minutes, per-class rates, throttles), so trends read from one page.

**Daylight saving.** The routine crons are pinned in UTC (07:00, 16:00,
20:30). After Berlin moves from CEST to CET on the last Sunday of October,
they fire at 08:00, 17:00, and 21:30 local: a safe direction, since the
failsafe moves away from midnight. The retro nearest the change notes it in
`CHANGELOG.md`; re-pinning a trigger is Tom's.

## Tunable: commit message conventions

`journal:` daily entries · `learn:` retro adjustments · `config:` config/scaffold
changes · `scout:` candidate updates worth committing · `memory:` knowledge-wiki
synthesis (failsafe daily, retro weekly) · `dispatch:` contract state changes. One-line messages, evidence in the body
when it matters.
