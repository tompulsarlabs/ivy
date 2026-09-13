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

- **Scout (09:00)** — **orient first:** read `memory/INDEX.md`, then
  `memory/ops.md` and the `memory/repos/<name>.md` page for every repo that
  produces a candidate. That is the standing context — what this repo is, what
  has been tried, what the environment will refuse to do — and it is much
  cheaper than re-deriving it from journal history. Follow a `[cite:...]` down
  to the journal only when a claim is decision-critical or looks stale; adopt
  it directly otherwise.
  Then sync watchlist (`search_repositories org:<login>`, minus
  forks/archived/excludes — `gh` is not available in the cloud sandbox,
  `memory/ops.md`).
  Gather candidates: open PRs close to merge, assigned issues, branches with recent
  pushes but no PR, yesterday's carry-over.
  **Rank by value, not by cheapness.** Tom's focus is revealed, not declared:
  repos with Tom-authored commits in the last 7 days, local WIP, and draft
  PRs he updated this week rank above any "cheapest ship" on a stale PR.
  A repo in `config.yml` `watchlist.parked` is watched only — its
  contributions count and its attribution is scanned — and produces no
  candidate, contract, or audit; it leaves `parked` by Tom's commit or a
  retro `learn:`. Evidence: `c2-client-matrix` #1 was the fallback pick for
  eight runs with zero conversions before Tom parked it (2026-09-03).
  **Also hunt blockers, not just candidates.** A candidate produces a
  contribution today; a blocker stops future work from happening at all —
  a dead runner, an expired credential, a queue nothing is draining, a
  broken local scan, an unmerged fix everything else waits on. Blockers are
  invisible to a "cheapest ship today" ranking because their contribution
  count is zero, which is exactly why they rot. **Read
  `dispatch/runner-status.json`** — the Mac runner's heartbeat, committed when
  its state changes and at least every 6 hours inside the window. `harness`
  false or `lint_ok` false is a blocker from the first morning: every
  contract waits on it. `last_tick` older than 3 hours inside the runner
  window with contracts open means the runner is not ticking — a sleeping
  Mac or an unloaded launchd job; name it, never guess which. `skipped`
  says why each open contract was passed over. Name any blocker in the
  journal under `## Blockers` with what it stops and the smallest next
  action; carry it forward every day until it clears or is explicitly
  declined. A blocker that has persisted three days outranks the day's
  cheapest ship in the nudge. **Also read `local-wip.json`** (pushed by
  the Mac's launchd scanner at 08:45/17:45): repos with `unpushed_commits > 0` or
  `remote: none` are first-class candidates — "push X (N unpushed commits)" is often
  the cheapest real ship of the day. Staleness rule: if its `generated_at` is older
  than 36h, treat local WIP as *unknown* (say so in the journal), never as "nothing
  pending" — a sleeping Mac must not lie to the scout.
  **Attribution check (outranks every other candidate):** any repo with
  `author_email_ok: false` will author its next commit as an address that is not
  connected to the account, so that work cannot count (rule 2) no matter how real
  it is. `last_commit_email_ok: false` means it has already happened. Lead the
  journal with it and nudge immediately rather than waiting for the 18:00 check —
  the fix is one `git config` line while it's cheap, and a history rewrite once
  the commits are pushed. This is the one scout finding that breaks the "silent"
  rule, because by 18:00 a whole day of real work may already be uncountable.
  Draft `journal/<today>.md`
  and commit it **bot-authored** (`scout: <date> — <n> candidates, top:
  <one-liner>`). Silent.
  **Emit dispatch contracts** for the top candidates: up to
  `dispatch.daily_cap` minus contracts already created today, using the
  contract format in `dispatch/DESIGN.md` §2. Review contracts pin the
  family that did not author the PR and default to `lane: workhorse` (down
  from `frontier`, retro 2026-09-06: five straight verified first-pass
  frontier/openai review outcomes met the Pareto bar for a lane-move trial,
  `memory/models.md`) — pin `frontier` explicitly only when a candidate's
  own signal calls for it. Run `scripts/dispatch-lint.sh`, commit
  bot-authored (`dispatch: open <id>`). Execution is the runner's job — the
  scout only queues. A contract is a ticket in the `to-tickets` sense: one
  vertical slice, complete and verifiable on its own, sized for a single
  worker session. Work that needs more than one slice is published as a
  chain — later contracts carry `blocked_by` with the earlier ids — never as
  one oversized contract. Write contracts in `CONTEXT.md` vocabulary.
  Anything learned along the way — a repo that has gone quiet, a new access
  limit, a candidate that keeps resurfacing — goes in the journal entry, not
  into `memory/`. The failsafe folds it in tonight; the scout never edits
  memory pages.
- **Check (18:00)** — run `scripts/check.sh`. Green → record outcome in state
  (bot-authored commit), stay silent. Grey → nudge with the single most concrete
  candidate. **Before picking that candidate, read its
  `memory/repos/<name>.md`** — nudge history and conversion record live there.
  A candidate carrying recorded unconverted nudges is a weaker pick than a
  fresh one of similar cost; say so in the journal when you pick it anyway.
  Note open/claimed contract states (`dispatch/queue/`) when recording the
  check — a claimed contract may land before failsafe.
  Nudge channel: **PushNotification** (verified working from cloud runs
  2026-08-23, "Mobile push requested"). Fallback if PushNotification reports
  not-sent/unavailable: a Google Calendar event ~15 min out titled with the
  candidate. Send through exactly one of the two.
- **Failsafe (22:30)** — still grey → finalize today's journal entry, commit it
  **Tom-authored** per the attribution rule, push, verify per the immutable rule.
  Record outcome either way — `state.json` gets `{date: {green_by, method,
  contributions: <final count from check>, signal_source, cite, nudge_sent,
  nudge_converted, failsafe_fired}}` (bot-authored); bump or reset `streak`.
  Keep `signal_source` to a short source label and put the verification
  narrative in the journal entry under `## Verification`, with `cite` pointing
  at that file.

  **Then verify dispatch contracts** — after the day is secured, never
  before: for each contract in `dispatch/done/` without a `verified:` stamp,
  run its Verification section via cloud-checkable means and stamp
  `verified: true|false`; move contracts past `expires` to `dispatch/failed/`
  with `state: expired`. Two more cases, because the runner's bookkeeping is
  a claim like any worker's:
  - A contract in `dispatch/failed/` whose outcome says `exit: timeout` or
    `no_report` may have finished the work and only missed printing the
    report (2026-09-03: `copy-02` opened its draft PR at 10:32 and was
    recorded as a 40-minute timeout at 10:53). Run its Verification too. If
    it passes, set `state: done`, move it to `dispatch/done/`, stamp
    `verified: true` with a `verified_note` saying the report never landed,
    and count its wall-minutes as work, not waste. If it fails, leave it.
  - A contract in `dispatch/queue/` with `state: claimed` and no outcome
    whose `claimed_at` is older than `budget.wall_minutes × 3` is a runner
    that died mid-task: set `state: open`, drop `claimed_at`, and say so in
    the journal. It runs again on the next tick.
  Run `scripts/dispatch-lint.sh`; commit bot-authored
  (`dispatch: verify <ids>`). Verified outcomes feed `memory/models.md` in
  the synthesis pass below.

  **Then synthesize memory** — always *after* the day is green and recorded,
  never before: a memory problem must never eat the failsafe window. This is
  the daily pass that keeps `memory/` current:
  1. **Attach facts to subjects.** Every observation from today worth keeping
     goes to its page — repo facts to `memory/repos/<name>.md`, environment
     behavior to `memory/ops.md`, rhythm and conversion to
     `memory/patterns.md`. Write the citation as you write the claim.
  2. **Create a page** only for a subject with real, durable signal, and add it
     to `memory/INDEX.md` in the same commit. One quiet day does not earn a
     repo a page; a first real commit does.
     If the day involved a non-obvious operational sequence that will recur,
     write the recipe to `procedures/` while the details are exact — a
     memory page saying "someone should run the same recipe we used for X"
     means that recipe should have been written down.
  3. **Making no change is a valid outcome.** If the wiki is already correct,
     write nothing — an unchanged page is a stronger signal than a page
     restated daily.
     A concept today's journal needed that `CONTEXT.md` lacks, or used
     against its definition, goes in the journal under `## Vocabulary gaps`.
     The failsafe never edits the glossary; the retro does.
  4. Run `scripts/memory-lint.sh`; it must pass before committing. Commit
     bot-authored as `memory: <what changed>` and set
     `memory_last_synthesized` in `state.json` to today.

**Ops note (cloud environment, mapped live 2026-08-23, two test runs):** the routine
sandbox has no `gh` preinstalled and ALL github.com egress is proxy-scoped to this
repo — GraphQL is blocked, unscoped REST is blocked, and even the public
contributions HTML 403s ("sessions are bound to their configured repositories").
`scripts/check.sh` therefore exits 2 (no signal) in the cloud; that is expected,
never a reason to guess. What works: (1) git push/pull to this repo via the
credential proxy; (2) the **built-in GitHub MCP tools** (`mcp__github__*`, load via
ToolSearch), which are user-scoped — `get_me` confirms identity, `list_commits` reads
this repo, and `search_commits` / `search_issues` / `search_pull_requests` see
cross-repo activity. Don't waste run time installing or authenticating `gh`.

**Cloud verification path (when check.sh exits 2):** today is GREEN if any of:
(a) `mcp__github__list_commits` on this repo shows a commit on `main` today
(Europe/Berlin) whose author email is the connected `commit_email`;
(b) `mcp__github__search_commits` finds commits by `author:tompulsarlabs` today
(search covers default branches only, matching counting rule 1 — ignore hits in
forks);
(c) `search_issues` / `search_pull_requests` show an issue or PR opened by
`tompulsarlabs` today.
Bot-authored commits (`bot@ivy.invalid`; historical `bot@evergreen.invalid`) NEVER
count as green — they don't light the graph. If the MCP tools are also unavailable, ALERT; never guess.
Note search indexing can lag a fresh push by a minute — prefer (a) for verifying a
failsafe commit you just made.

**Ops note (DST):** cron schedules are pinned in UTC (07:00 / 16:00 / 20:30). When
Berlin flips CEST→CET in late October, local fire times shift to 08:00 / 17:00 /
21:30 — a safe direction (failsafe moves *earlier*). The retro nearest the flip
should re-pin the UTC crons if the original local times matter.

## Tunable: retro (Sunday 10:00)

Read `memory/INDEX.md` and the pages it lists first — that is the synthesized
view of the trailing window, and cheaper than re-mining raw history. Then read
the last 7–30 days of `state.json` for the numbers. Answer: how often did the
failsafe fire? Did nudges convert to real activity within 4 hours? Which repos
produced shipped work?

The retro then has two jobs.

**Tune behavior.** At most two adjustments (nudge time, wording, ranking,
excludes) by editing the Tunable sections of this file and/or `config.yml`.
Commit as `learn: <what> — <evidence>`, naming the page or journal entry the
evidence came from; tag the next version; summarize in `CHANGELOG.md`.

**Curate memory.** The daily pass only adds — this is the only pass that
removes, and the only one allowed to rewrite a page wholesale:

- **Verify** a sample of claims against their citations, weighted toward the
  ones that have been influencing candidate ranking. A claim its evidence no
  longer supports gets corrected or dropped, never left standing. Contradictions
  between sources are worth recording explicitly rather than silently resolving.
- **Prune** what has stopped being true: a repo gone dormant, an access limit
  that no longer applies, an open thread that closed. Outdated context is worse
  than missing context, because it reads as current.
- **Log** every removal in that page's `## Changelog` with the date and reason.
  Git holds the diff; the changelog line is what makes it findable without
  archaeology.
- **Merge or split** pages when a subject has outgrown or emptied its page, and
  keep `memory/INDEX.md` inside its line budget — it is read on every run, so
  it stays a map, not a summary.
- Re-run `scripts/memory-lint.sh`, then commit bot-authored as
  `memory: retro — <what changed>`.

**Prune the steering files.** `CLAUDE.md`, `playbook.md`, `routines/*.md`,
and `procedures/` are read on every run, so every line costs on every run.
Once a week, call the Skill tool with `writing-for-agents` and apply its
tests to them: delete no-ops (instructions the agent already follows by
default), collapse restatements into a leading word, state a target
positively where a prohibition is not a hard guardrail, and push reference
that only some runs need behind a pointer. A deletion that provably changes
no behaviour does not count toward the two adjustments; a wording change
that does, does. Immutable sections stay untouched. Then curate
`CONTEXT.md`: call the Skill tool with `domain-modeling`, resolve the week's
`## Vocabulary gaps` from the journals, correct any page or journal that used
a term against its definition, and record in `docs/adr/` any decision that
is hard to reverse, surprising without context, and the result of a real
trade-off — all three, or no ADR.

**Run the fleet, not the sessions.** The retro optimizes lane *policy* against
per-class targets, never individual runs (adapted from Uber's software-factory
findings, 2026-08-28):

- **Per-class target metrics** — review: share of findings that survive
  triage; build: first-pass verified-done rate; chore: wall-minutes per
  verified-done; every class: zero waste. Judge lanes on these, not vibes.
- **Waste is the first lever, model choice the last.** Waste = wall-minutes
  on `dispatch/failed/` contracts + contracts that expired unexecuted +
  repeated unresolvable-lane skips. Compute it weekly before touching lane
  assignments — eliminating zero-value consumption beats downgrading a lane
  and losing quality.
- **Pareto rule for lane moves.** Step a task class down to a cheaper lane
  only when its target metric held there (experiment evidence or ≥3 verified
  outcomes); step it up when failures show quality is the binding
  constraint. Never trade a target metric for cost — flat-rate pools make
  that a bad trade by definition.
- **Experiments are the benchmark instrument.** When a lane decision is
  pending and the evidence is thin, spend that week's one `experiment`
  contract on exactly that comparison rather than waiting for organic
  volume.
- **Record fleet metrics weekly** in `memory/models.md` (verified-done
  count, waste minutes, per-class rates, throttles) so trends are one page,
  not an archaeology dig.

## Tunable: commit message conventions

`journal:` daily entries · `learn:` retro adjustments · `config:` config/scaffold
changes · `scout:` candidate updates worth committing · `memory:` knowledge-wiki
synthesis (failsafe daily, retro weekly) · `dispatch:` contract state changes. One-line messages, evidence in the body
when it matters.
