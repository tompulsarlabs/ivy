---
subject: tompulsarlabs/ivy
type: repo
updated: 2026-09-11
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
last landed 2026-09-08T15:45 CEST and missed five straight windows (09-09
08:45/17:45, 09-10 08:45/17:45, 09-11 08:45), crossing the playbook's 3-day
outranking bar on 2026-09-11 [cite:2026-09-11]. Every day it stays dark, the
carry-over pattern above goes blind — no candidate can surface from it, and a
sleeping Mac reads as a clean tree. Not yet resolved as of the 2026-09-11
failsafe.

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
