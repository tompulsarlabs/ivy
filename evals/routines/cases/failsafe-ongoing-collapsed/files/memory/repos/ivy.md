---
subject: tompulsarlabs/ivy
type: repo
updated: 2026-09-22
---

# ivy

Public. The system itself: config, playbook, memory, journal, state, scripts.
Renamed from `evergreen` on 2026-08-24 when the agent got its name.

Being public matters operationally — a green day confirmed by a commit here
needs no "private contributions" toggle to show on the graph [cite:2026-08-24].
It is the fallback proof when the day's real work landed somewhere private
([[repos/countersign]], [[repos/talent-radar]]).

## `state.json` is a published contract

[[repos/tomgreen.ai]] reads this repo's `state.json` for its live proof strip
[cite:2026-08-24]. Keys are consumed outside this repo by code that cloud runs
cannot see [[ops]], so treat the schema as append-only: add keys, shorten
values, never rename or remove.

## The local-WIP carry-over pattern

The Mac checkout of this repo repeatedly held work the cloud clone could not
see: 1 unpushed commit flagged on both 2026-08-25 and 2026-08-26, carried over
unresolved and named as the day's top pick both times [cite:2026-08-25]
[cite:2026-08-26]. Resolved by 2026-08-27, when the scan showed all five
tracked repos clean [cite:2026-08-27].

The pattern is worth remembering: "push the Mac's unpushed commit" is the
cheapest real ship available, it recurs, and it is invisible to any cloud-only
check — it depends entirely on `local-wip.json` being fresh [[ops]].

The same channel caught an attribution problem on 2026-08-30: 1 unpushed
commit dated 08-29 with `last_commit_email_ok: false` — the scout nudged
same-morning per the outranking rule, before it reached `main`
[cite:2026-08-30] [[ops]] [[patterns]].

The scanner itself has been dark since `local-wip.json` last landed
2026-09-08T15:45 CEST (`generated_at` unchanged at 2026-09-08T15:45:06Z):
28 missed windows / 14 calendar days at the 2026-09-22 failsafe, eleven
days past the playbook's 3-day outranking bar [cite:2026-09-11]
[cite:2026-09-22]. While it stays dark, the carry-over pattern above goes
blind: no candidate can surface from it, and a sleeping Mac reads as a
clean tree. The retro reads the outage as the likely driver of the
failsafe's fire-rate step [[patterns]] [cite:2026-09-20].

A second signal on the same Mac: `dispatch/runner-status.json`'s
`last_tick` shifted from `+02:00` (CEST) to `+01:00` on 2026-09-16, a
day before any real CEST→CET flip, and was back to `+02:00` by 09-18,
with a stale heartbeat on both days [cite:2026-09-17][cite:2026-09-18]
[[ops]].

## Activity

7 non-bot commits on 2026-08-24 (the ladder build) [cite:2026-08-24]; 4 on
2026-08-26 [cite:2026-08-26]; 3 on 2026-08-27 (memory-wiki build +
state-schema refactor), plus 2 PRs opened same day [cite:2026-08-27]. Bot-authored
bookkeeping commits are excluded everywhere and never count [[ops]].

## Dispatch runner: dirty-clone recovery (PR #17, 2026-09-04)

A worker killed at its wall-minute budget with edits still in its clone's
tree (`copy-02`, 2026-09-03) left that clone dirty; the runner's next
`git checkout main` on it refused, the exception escaped `ensure_clone`
uncaught, and every tick died at that line — before claiming, before the
heartbeat — from 2026-09-03T10:53 CEST until a same-day reinstall
2026-09-04. Idle and dead looked identical from the cloud side for that
whole span [cite:407cf03]. Fixed same day: `ensure_clone` now
force-checks-out and hard-resets each work clone before use (ignored
installs survive `clean -fd`), and `guarded_main` turns any escaping
runner exception into a `runner_error: <type>` heartbeat so a broken
runner is distinguishable from an idle one going forward [cite:407cf03].
Paired same day with PR #16, parking `c2-client-matrix`
[[repos/c2-client-matrix]] and teaching the scout to rank by revealed
focus over cheapest ship [cite:e7e918b].

## Changelog

- 2026-09-20 (retro) — collapsed the local-WIP outage's daily restatements
  (09-11 through 09-20) into one current-state paragraph and the runner
  heartbeat's into another, keeping each one's first and latest citations;
  the day-by-day detail stays in the cited journals. The daily entries
  below predate the collapse.
- 2026-09-19 (failsafe) — recorded the local-WIP scanner outage's escalation
  to 21 missed windows / 11 calendar days, still open; noted the runner
  ticked once (still CEST, the 09-16 offset shift did not persist) but left
  a ~5-hour gap before the window closed; noted the 09-18 real-work green
  was one day only — today reverted to a failsafe-fired journal-only day
  (streak secured at 27), the seventh such day in the last eight.
- 2026-09-18 (failsafe) — recorded the local-WIP scanner outage's escalation
  to 19 missed windows / 10 calendar days, still open, plus a second
  staleness signal on the same Mac (`runner-status.json` heartbeat now
  ~21+ hours old); noted the grey streak broke today — green by real work
  (`tomgreen.ai` PR #61/#62 + `tompulsarlabs` commits), not a journal entry.
- 2026-09-17 (failsafe) — recorded the local-WIP scanner outage's escalation
  to 18 missed windows / 9 calendar days, still open; sixth consecutive
  failsafe-fired grey day (streak secured at 25 by journal entry, not real
  work); flagged a same-week `runner-status.json` timezone-offset shift
  (CEST→CET a day early) alongside it as a possible same-machine cause.
- 2026-09-16 (failsafe) — recorded the local-WIP scanner outage's escalation
  to 16 missed windows / 8 calendar days, still open; noted it now coincides
  with the run's fifth consecutive failsafe-fired grey day (streak secured
  at 24 by journal entry, not real work).
- 2026-09-14 (failsafe) — recorded the local-WIP scanner outage's escalation
  to 12 missed windows / 6 calendar days, still open; noted it now coincides
  with the run's third consecutive failsafe-fired grey day (streak secured
  at 22 by journal entry, not real work).
- 2026-09-13 (failsafe) — recorded the local-WIP scanner outage's escalation
  to 9 missed windows / 5 calendar days, still open; noted it now coincides
  with both failsafe-fired grey days of the run (streak secured at 20, then
  21, by journal entry, not real work).
- 2026-09-12 (failsafe) — recorded the local-WIP scanner outage's escalation
  to 7 missed windows / 4 calendar days, still open; noted it coincides with
  the run's first failsafe-fired grey day (streak secured at 20 by journal
  entry, not real work).
- 2026-09-11 (failsafe) — recorded the local-WIP scanner's 5-missed-window,
  3-day outage (blocker since 09-08, still open).
- 2026-09-04 — recorded the dispatch-runner dirty-clone bug (PR #17) and
  the guardrail it added; both PR #16 and #17 merged same day, real work.
- 2026-08-30 (retro) — added the pre-push attribution catch on this repo's
  own Mac checkout.
- 2026-08-27 — page created from journals 2026-08-23→27, `state.json`, and
  `CHANGELOG.md`.
- 2026-08-27 (failsafe) — added 2026-08-27 activity row: the memory system
  documented on this page shipped the same day, on this repo, by real work.
