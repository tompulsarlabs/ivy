# Changelog

## v7 — 2026-09-06

**Retro: review lane stepped down; a missed memory page caught.** Reviewed
`state.json` 2026-08-23→09-05 (14 recorded days) plus `memory/patterns.md`
and `memory/models.md`. Failsafe fire rate: still 0/14 — every day has gone
green by real work before 22:30; the floor keeps doing its job by never
being needed, no timing change follows. Nudge→conversion: still exactly one
grey-check nudge ever sent (2026-08-24, unconverted) — n=1 is still too
thin to safely tune nudge timing, wording, or channel, same conclusion as
every prior retro. Shipped work: `tomgreen.ai` remains the dominant repo by
a wide margin, `ivy` ships steadily, `talent-radar` graduated from
dormant-scaffold to a live PR #1 build; `c2-client-matrix` stays parked
with no reactivation signal since 2026-09-03.

**Adjustment (1 of 2 used): `review` contracts now default to `lane:
workhorse`, down from `frontier`.** `memory/models.md` recorded 5 straight
verified first-pass `review` outcomes on frontier/openai — the Pareto rule
for lane moves (`playbook.md`, ≥3 verified outcomes) is squarely met, and
the page's own "Reading" section had already flagged the trial as ready.
`playbook.md`'s scout section now states the default explicitly (it had
never been written down — scout was defaulting every review contract to
`frontier` by unwritten convention, confirmed against three weeks of
contract files); `frontier` stays available as an explicit per-contract
pin when a candidate calls for it. No second adjustment made this week —
the other candidates (nudge timing, watchlist excludes) remain evidence-thin
or already correctly resolved.

**Doc-accuracy fix (free of the cap — no behavior change).** `playbook.md`
and `config.yml` both described the scout's watchlist sync as `gh api
user/repos`, but `gh` has never been available in the cloud sandbox
(`memory/ops.md`); journals since 2026-08-29 show the scout has actually
been using `search_repositories org:tompulsarlabs` all along. Corrected
both to name the tool actually in use.

**Memory curation.** Created `memory/repos/writing-voice-skill.md` on its
first real signal (PR #2, opened 2026-09-05) — this was the failsafe's job
the night it happened and was missed; caught in this pass, `INDEX.md`
updated. Spot-checked `c2-client-matrix.md`, `ai-capability-app.md`, and
`talent-radar.md` against their citations — all current, no correction or
pruning needed. Added the week's fleet-metrics row to `memory/models.md`
(7 newly verified, first real waste and first expired-unexecuted contract,
both `tomgreen.ai` `build`) and recorded the lane-move decision there.
`scripts/memory-lint.sh` clean.

**Tag gap found, not backfilled — and this run couldn't close it either.**
`git tag -l` shows only `v1` and `v2` exist, though this file documents
releases through `v6` — `v3`–`v6` were never tagged (a gap in the
retro/release process itself, not caught until this run). Not backfilling
those retroactively: the exact commit each should point to is a guess this
far after the fact, and inventing historical tag placement is the same
category of problem as backdating a commit. This entry advances the count
to `v7`, the durable record kept in this file — but `git push origin v7`
403s from this cloud session every time (4 retries, `memory/ops.md`): the
session can push commits to `main`, not tag refs. So `v7` exists here and
in the local clone, not on the remote — the same backfill decision as
`v3`–`v6`, now one entry longer, for a human to run `git tag v7 <sha> && git
push origin v7` from a session that can.

## v6 — 2026-09-02

**A glossary and a skill layer; the runner's gate fixed.** Adopted
[mattpocock/skills](https://github.com/mattpocock/skills) (plugin v1.2.3,
upstream `6654f6b`): the 25 promoted skills vendored under `.claude/skills/`
via skills.sh (`skills-lock.json` pins hashes) so cloud routines load them
from the checkout; `CLAUDE.md` added as navigation pointers plus the
`## Agent skills` block; `docs/agents/` maps the skills onto Ivy — the issue
tracker is `dispatch/queue/` (tickets from `/to-tickets` publish as a chain
of contracts), specs and decision tickets live under `.scratch/`, triage
roles map onto contract states. `CONTEXT.md` written: Ivy's glossary, with
the ambiguities that already cost work recorded as resolved (nudge vs pick,
claimed vs verified done, "the" connected address).

Dispatch: `blocked_by: [id, id]` on contracts — the runner skips a contract
until every id is in `dispatch/done/`, the lint refuses unknown ids
(`dispatch/DESIGN.md` §2). The worker prompt names `code-review` (review)
and `tdd` + `code-review` (build), conditionally. **Runner bug fixed:** the
attribution gate tested `commit_email` alone, the same narrow check the
scanner lost on 09-01; on 2026-09-01 17:01 it refused three `tomgreen.ai`
builds on a clone correctly configured with `tom@pulsarlabsai.com`. Now
membership over `connected_emails`, locked by
`scripts/dispatch-runner-test.py` (red on the old code, green now). The
three contracts re-queued as `-02` with an establish-current-state step,
plus `2026-09-02-tomgreenai-context-01` to draft that repo's glossary.
The launchd job runs the script from `~/Build/ivy`, so the fix lands on the
Mac at the next `git pull` there.

Playbook (Tunable only): scout contracts are tickets — one vertical slice,
chains via `blocked_by`, glossary vocabulary; failsafe records
`## Vocabulary gaps` in the journal; retro gains a third job — prune the
steering files with `writing-for-agents` (no-ops, restatements, negation,
disclosure; provable no-behaviour-change deletions are free of the two-change
cap) and curate `CONTEXT.md` with `domain-modeling`, ADRs to `docs/adr/`
only when hard to reverse, surprising, and a real trade-off.

Same day, later: gstack vs Matt's skills reconciled in
`setup/AGENTIC-STACK.md` ("Which one for what") — no name clashes, three
shared trigger phrases (`review`/`code-review`, `investigate`/
`diagnosing-bugs`, two retros), and two things gstack must not do in this
repo: `/spec --execute` and `/ship` (a second executor and a `VERSION` bump
past Ivy's guardrails), `/learn`/gbrain/`/retro` (agent-written memory the
agent then obeys). gstack's CLAUDE.md block belongs in `~/.claude/CLAUDE.md`,
not here; `.context/` ignored defensively.

2026-09-03: first `build` contracts executed end to end. Two runner faults
found and fixed on the Mac (Tom, `fb4ac9e`, `3fd6151`): the launchd entry
point ran a stale checkout (runner now execs the synced copy), and launchd's
PATH lacked `claude`, stranding two claims (harness resolved before
claiming; PATH declared in the plist). `context-01` done in 14.5 min →
tomgreen.ai #14 (a 344-line glossary draft); `copy-02` recorded as a
40-minute timeout although its draft PR #15 had landed at 10:32 with
tests, e2e, and `/code-review` green. Playbook: the failsafe now verifies
`timeout`/`no_report` failures and promotes a passing one to `done/`, and
re-opens claims older than budget × 3 — the latter promised in
`dispatch/DESIGN.md` since D0 but never specified anywhere a routine reads.
Later the same day: `dispatch/runner-status.json`, the runner's heartbeat —
after the log tail could not be read from the cloud and three contracts sat
open with no claim, the runner now commits its own state (harness found,
lint, result, skipped-with-reason) on change and every six hours; the scout
reads it under `## Blockers`.

2026-09-03, Tom: `watchlist.parked` — repos watched for counting and
attribution but never proposed. `c2-client-matrix` parked ("not WIP or
something to devote my time to atm"; #1 was the fallback pick eight runs
running, zero conversions — `memory/patterns.md` had recorded the revealed
preference for new work since 08-27). Scout ranks by revealed focus (recent
Tom-authored commits, local WIP, drafts he touched) over cheapest ship; the
lint refuses a new contract on a parked repo.

2026-09-04: the silent day explained. `copy-02`'s worker was killed at its
budget on its own branch with edits in the tree; the runner's next
`git checkout main` refused, the exception escaped, and every tick from
2026-09-03 10:53 until the reinstall on 09-04 died at that line before it
could claim or write a heartbeat. `ensure_clone` now forces the checkout,
pins to origin, and cleans untracked files (ignored installs survive);
`guarded_main` turns any escaping exception into a `runner_error` heartbeat.
Both locked by tests against a real temporary git remote.

## v5 — 2026-08-30

**First retro: no change — evidence still too thin to tune.** Reviewed
2026-08-23→29 (`state.json`, 7 recorded days) plus the in-progress 08-30
journal. Failsafe fire rate: 0/7 — every day went green by real work before
22:30, so the floor has never been tested in anger; that's the floor doing
its job, not a timing problem to fix. Nudge→conversion: exactly one
grey-check nudge has ever been sent (2026-08-24, `c2-client-matrix` #1,
unconverted) — n=1 is too thin to safely retune nudge timing, wording, or
channel without overfitting to a single data point. Shipped work concentrated
in `tomgreen.ai` (highest volume by a wide margin), `ivy`, and one-off
revivals (`ai-capability-app` #7 after two months dormant, `talent-scout`'s
first commit); `c2-client-matrix` #1 has been the scout's fallback pick for
7 straight runs with zero conversion, but the same n=1 problem blocks a
confident ranking demotion — reviewed explicitly this retro
(`memory/repos/c2-client-matrix.md`) and left unchanged. Dispatch fleet
metrics: still 1 verified contract, 0 waste, Pareto bar (≥3 verified
outcomes) unmet, so no lane move; the binding constraint there is D2 runner
capacity, not routing policy, which a config tune can't fix anyway.
`playbook.md` and `config.yml` are unchanged this week.

Also did the retro's memory-curation pass: folded in 08-28→30 facts that
two green days' failsafe runs hadn't synthesized yet (`ai-capability-app`
dormancy note pruned — PR #7 shipped; new `talent-scout` page on first
signal; attribution-nudge working pre-push, first observed case), and
logged the stalled dispatch queue as an infra gap rather than a policy one.
`scripts/memory-lint.sh` clean, 12 pages.

## v4 — 2026-08-27

**Dispatch D0+D1: the executive layer.** Designed (`dispatch/DESIGN.md`) and
plumbed: scouted candidates become dispatch contracts — markdown+frontmatter
files under `dispatch/`, lint-gated (`scripts/dispatch-lint.sh`), routed
across coarse lanes (frontier/workhorse/fast-cheap) mapped in `config.yml`
onto two flat-rate pools (Anthropic; OpenAI via Codex CLI, models pinned
during D2). Repo is the message bus; execution splits cloud (Anthropic
lanes) / Mac runner (everything else, 09:15–21:00 every 30 min); workers are
untrusted, push draft PRs only, and a contract is done only when the
failsafe's external check verifies it. Guardrails adopted as a new immutable
playbook section — the daily ladder stays senior. Cap 6 contracts/day.
D1 exit criterion met with a real contract (nudge-count reconciliation:
journals had counted scout picks as nudges; confirmed 1 nudge, 0
conversions) run open → done → verified, first evidence row in
`memory/models.md`. D2 next: Mac runner + cross-family review lane.

## v3 — 2026-08-27

**Memory: the knowledge wiki.** Added `memory/` — Markdown pages, one per
durable subject, synthesized over the two layers that already existed
(`journal/` raw sessions, `state.json` outcomes). Pages carry two kinds of
link: `[[page]]` for lateral context, `[cite:<date>]` / `[cite:<sha>]` for
evidence resolving to a journal entry or a commit in this repo. Every run now
orients from `memory/INDEX.md` rather than re-deriving subject context from
day-keyed entries — the gap that let `c2-client-matrix` #1 be re-picked as
"cheapest candidate" four runs running while its unconverted nudge history sat
smeared across four files.

Written on two cadences: the failsafe attaches the day's facts (always *after*
the day is green, so memory can never eat the failsafe window), and the retro
is the only pass that verifies claims, prunes stale context, and logs
deletions. Marked immutable — pages hold observations, never instructions;
behavior stays in `playbook.md`, which only the retro edits. A memory the agent
writes and then obeys is a prompt-injection channel with extra steps.

Also in v3: `scripts/memory-lint.sh` gates every memory commit (frontmatter,
link and citation resolution, orphan pages, index line budget), verified
against each failure mode. `state.json` slimmed 64% by moving verification
narratives into `## Verification` sections of the journal entries they
describe, with a new `cite` key pointing back — schema kept append-only, since
`tomgreen.ai`'s live proof strip consumes this file. Routine prompts unchanged:
the thin-prompt design meant a whole new responsibility needed no cloud
reconfiguration.

Seeded with 10 pages from journals 2026-08-23→27. Design influence:
Perplexity's Brain.

## v2 — 2026-08-24

The agent has a name: **Ivy** (repo renamed evergreen → ivy; bot identity now
`ivy-bot <bot@ivy.invalid>`, historical `bot@evergreen.invalid` commits remain
valid non-counting bookkeeping). Same system, same rules. Also in v2: Phase 4
local-WIP pipeline (launchd scanner → local-wip.json, 36h staleness rule),
narrative reframe (agentic DevOps daily-shipping), tomgreen.ai now public and
tracked.

## v1 — 2026-08-23

Ladder live: four cloud routines (scout 09:00 / check 18:00 / failsafe 22:30 daily,
retro Sun 10:00, Berlin). Two forced failsafe test runs mapped the cloud sandbox:
all github.com egress is repo-scoped, so verification there goes through the
built-in GitHub MCP tools (playbook ops note); check.sh keeps GraphQL + public-HTML
paths for local/unproxied use. Nudge channel: PushNotification (verified reaching
mobile from cloud), calendar event as fallback. Attribution model enforced:
bot-authored bookkeeping, connected-author journal/work commits only.

## v0 — 2026-08-23

Initial scaffold: design doc, playbook (immutable counting/verification/no-synthetic
rules + tunable ladder), config, state, check script, first journal entry.
Phases 2–3 (cloud routines, weekly retro) pending.
