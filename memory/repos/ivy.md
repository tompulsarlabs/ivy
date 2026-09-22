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

The scanner itself has now gone dark for an extended stretch: `local-wip.json`
last landed 2026-09-08T15:45 CEST and has missed nine straight windows
(09-09 08:45/17:45, 09-10 08:45/17:45, 09-11 08:45/17:45, 09-12 08:45/17:45,
09-13 08:45), crossing the playbook's 3-day outranking bar on 2026-09-11 and
still open two full calendar days later [cite:2026-09-13]. Every day it
stays dark, the carry-over pattern above goes blind — no candidate can
surface from it, and a sleeping Mac reads as a clean tree. This same outage
window now covers *three consecutive* grey days of the run (2026-09-12,
2026-09-13, 2026-09-14, failsafe fired all three times, journal secured
the streak at 20, then 21, then 22): whether a same-day local push would
have gone green instead is unknowable while the scanner stays dark
[cite:2026-09-12][cite:2026-09-13][cite:2026-09-14]. Still dark as of the
2026-09-15 failsafe — now 14 missed windows / 7 calendar days, four days
past the playbook's 3-day outranking bar. The outage now covers *four
consecutive* grey days (2026-09-12 through 2026-09-15, failsafe fired all
four times, journal secured the streak at 20, 21, 22, then 23)
[cite:2026-09-15]. Still dark as of the 2026-09-16 failsafe — now 16
missed windows / 8 calendar days, five days past the bar. The outage now
covers *five consecutive* grey days (2026-09-12 through 2026-09-16,
failsafe fired all five times, journal secured the streak at 20, 21, 22,
23, then 24) [cite:2026-09-16]. Still dark as of the 2026-09-17
failsafe — now 18 missed windows / 9 calendar days, six days past the
bar. The outage now covers *six consecutive* grey days (2026-09-12
through 2026-09-17, failsafe fired all six times, journal secured the
streak at 20, 21, 22, 23, 24, then 25) [cite:2026-09-17]. Separately, one
`dispatch/runner-status.json` `last_tick` shifted from `+02:00` (CEST) to
`+01:00` on 2026-09-16 — a full day before the real CEST→CET flip the
playbook's DST note expects in late October — read as a Mac clock/timezone
change rather than a code change; flagged alongside the scanner outage
since both point at the same machine [cite:2026-09-17] [[ops]]. Still dark
as of the 2026-09-18 failsafe — now 19 missed windows / 10 calendar days,
seven days past the bar, with `runner-status.json`'s `last_tick` unchanged
from the 09-17 read (now ~21+ hours stale, a second consecutive day past
the "at least every 6 hours inside the window" cadence) — the same Mac
showing two independent staleness signals at once [cite:2026-09-18]. The
day itself broke the grey streak: real work (`tomgreen.ai` PR #61 + #62
merged, 4 `tompulsarlabs` commits) went green well before the check,
ending a six-day run of failsafe-fired journal-only days
[cite:2026-09-18]. Still dark as of the 2026-09-19 failsafe — now 21
missed windows / 11 calendar days, eight days past the bar, with
`runner-status.json` ticking once during the day (`last_tick` moved to
2026-09-18T15:55:52+02:00, still `+02:00` CEST — the 09-16 timezone-offset
shift did not persist) but leaving a ~5-hour gap before the runner window
closed. The 09-18 real-work green was one day only: today reverted to a
failsafe-fired journal-only day, the seventh in eight days
(2026-09-12 through 2026-09-19, only 09-18 breaking the run)
[cite:2026-09-19]. Still dark at the 2026-09-20 retro — 23 missed
windows / 12 calendar days, nine days past the bar, `local-wip.json`
unchanged at `generated_at: 2026-09-08T15:45:06Z` [cite:2026-09-20].
Retro read this outage as the likely driver of the failsafe's 0/20→7/8
fire-rate step [[patterns]], too Mac-side to fix with a playbook/config
tune directly, but acted on the six identical unconverted nudges it
produced (09-12→17): `playbook.md` now caps identical blocker-nudge
repeats at 3 before falling back to a fresh candidate, and credits a
blocker nudge as converted on its own recovery signal, not only a GitHub
contribution [[patterns]]. Still dark at the 2026-09-20 failsafe — same
23 missed windows / 12 calendar days the same-morning retro already
recorded, `local-wip.json` unchanged. Today itself reverted to a
failsafe-fired journal-only day (streak secured at 28), the ninth such
day in the last ten (2026-09-12 through 2026-09-20, only 09-18 breaking
the run on real work) [cite:2026-09-20]. Still dark at the 2026-09-21
failsafe — `generated_at` unchanged at 2026-09-08T15:45:06Z, now 26
missed windows / 13 calendar days, eleven days past the bar. Today broke
the grey streak a second time: real work went green before the 18:00
check and kept landing after it (`gstack-security-patches` commit,
`talent-scout` PR #1, `tomgreen.ai` PR #63 merged at 18:56 CEST) — only
the second real-work day (with 09-18) in the eleven days since 09-12
[cite:2026-09-21]. Still dark at the 2026-09-22 failsafe —
`generated_at` unchanged at 2026-09-08T15:45:06Z, now 28 missed windows /
14 calendar days, eleven days past the bar. Today extended the real-work
run to a third day: `tomgreen.ai` PR #64 and #65 both merged before the
18:00 check, the third real-work green day (with 09-18, 09-21) in the
eleven days since 09-12 [cite:2026-09-22].

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

- 2026-09-22 (failsafe) — recorded the local-WIP scanner outage's escalation
  to 28 missed windows / 14 calendar days, still open; noted today made it
  three real-work green days (09-18, 09-21, 09-22) in the eleven days
  since 09-12, on `tomgreen.ai` PR #64 + #65 merged before the check.
- 2026-09-21 (failsafe) — recorded the local-WIP scanner outage's escalation
  to 26 missed windows / 13 calendar days, still open; noted today broke
  the grey streak on real work (`gstack-security-patches` commit,
  `talent-scout` PR #1, `tomgreen.ai` PR #63), only the second such day
  since 09-12.
- 2026-09-20 (failsafe) — recorded today's outcome: local-WIP scanner
  unchanged from the same-morning retro read (23 missed windows / 12
  calendar days); failsafe fired, journal-only grey day, streak secured
  at 28, the ninth such day in the last ten.
- 2026-09-20 (retro) — escalated the outage to 23 missed windows / 12
  calendar days, still dark; recorded the retro's read that it is the
  likely driver of the failsafe fire-rate step and the two playbook
  changes it prompted (blocker-nudge decay cap, corrected
  `nudge_converted` scoring).
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
