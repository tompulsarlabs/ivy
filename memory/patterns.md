---
subject: observed working rhythm
type: patterns
updated: 2026-09-24
---

# Patterns: how the work actually happens

Observations about the rhythm of real work, drawn from outcome history. These
are findings, not directives — the retro decides whether any of them should
change the ladder, and `playbook.md` is the only place behavior lives.

## The failsafe fire rate stepped from 0/20 to 7/8, entirely inside the scanner outage

Real work carried every one of the first 20 recorded days (2026-08-23→11):
never once did the floor need to fire [cite:2026-08-28][cite:2026-08-29].
That ended 2026-09-12 and has since become the norm, not the exception:
the failsafe fired 09-12, 13, 14, 15, 16, 17, 19, and 20 — eight of the
thirteen days since, with 09-18, 09-21, 09-22, 09-23 and 09-24 breaking
the run on real work (`tomgreen.ai` PR #61/#62 + `tompulsarlabs` commits
on 09-18; `gstack-security-patches` + `talent-scout` PR #1 + `tomgreen.ai`
PR #63 on 09-21; `tomgreen.ai` PR #64 + #65 on 09-22; three draft PRs
opened on `ivy` itself, #21/#22/#23, on 09-23; `ivy` PR #22/#23 +
`tomgreen.ai` PR #66/#67/#68 + `talent-radar` PR #1/#2 merged on 09-24,
the widest repo spread of any day since 09-10)
[cite:2026-09-12][cite:2026-09-13][cite:2026-09-14][cite:2026-09-15]
[cite:2026-09-16][cite:2026-09-17][cite:2026-09-18][cite:2026-09-19]
[cite:2026-09-20][cite:2026-09-21][cite:2026-09-22][cite:2026-09-23]
[cite:2026-09-24].
Every one of those eight fires falls inside the local-WIP scanner outage.
**The outage itself showed its first scheduled-window publish on 09-24**,
16 calendar days / 32 missed windows after going dark, following the
09-23 fix PR (`ivy` PR #22) merging that same morning [[repos/ivy]]. This
was already a large enough, tight enough coincidence to be a real
candidate explanation, not just a thin correlation: a dark scanner means
"push X (N unpushed commits)" — the cheapest real ship on a quiet day, per
the pattern below — cannot surface as a candidate at all, so a day that
would have gone green on a two-minute local push instead runs the full
grey-check-nudge-fail-safe ladder. Still not provable causally (the
counterfactual "would he have pushed" is unknowable without the scanner),
and was not something a playbook/config tune could fix directly — the
scanner is Mac-side infra, the same category as the D1-era dispatch-runner
gap below. Worth watching whether the fire rate now drops now that the fix
has landed and published inside a window at least once — one publish is
not yet proof the outage is over [[repos/ivy]].

## Volume is bursty, not steady

Contributions per day: 9, 19, 2, 31 [cite:2026-08-23][cite:2026-08-24]
[cite:2026-08-25][cite:2026-08-26]. A single day (2026-08-26) carried more
than the other three combined. A quiet day is therefore weak evidence of a
stalling week, and the 2-contribution day (2026-08-25) still cleared the bar.

## Work routinely continues past the 18:00 check

On 2026-08-24 and 2026-08-26 real commits kept landing well after the check —
2026-08-26 ran 11:17 to 20:52 local [cite:2026-08-26]. On 2026-08-25 nothing
landed after 18:00 [cite:2026-08-25]. Work also starts early: six commits
between 06:42 and 07:55, before the 09:00 scout, on 2026-08-27
[cite:2026-08-27]. So the check sits inside the working day rather than after
it, and a grey reading at 18:00 has often been a *mid-day* reading. Even a
*green* reading can be mid-day: on 2026-09-05 two more `tomgreen.ai` PRs
(#28, #29) were opened and merged between 18:20 and 19:30 CEST, after the
18:00 check had already recorded green off 16 events [cite:2026-09-05].

## New work outcompetes old open PRs, consistently

Across 2026-08-23→27 the three open PRs (opened April and May) drew zero
activity, while two new repos were created (`talent-radar`, `countersign`) and
`tomgreen.ai` alone took 26 commits in one day [cite:2026-08-26]
[cite:2026-08-27]. The revealed preference is for shipping new work over
clearing old review queues.

This matters for candidate ranking: `c2-client-matrix` #1 has been the scout's
"cheapest real contribution" pick repeatedly and has never been taken
[[repos/c2-client-matrix]].

## Nudge conversion is 0 for 9 — but the metric can't score a blocker fix

Nine *grey-check* nudges have ever been sent, all push channel, all
recorded `nudge_converted: false`: 2026-08-24 (`c2-client-matrix #1`)
[cite:2026-08-24]; six identical repeats of the local-WIP scanner outage,
2026-09-12 through 2026-09-17 [cite:2026-09-12][cite:2026-09-13]
[cite:2026-09-14][cite:2026-09-15][cite:2026-09-16][cite:2026-09-17]; and
2026-09-19 and 2026-09-20 (both `talent-radar` PR #2's two open review
findings, a fresh candidate, sent verbatim a second day)
[cite:2026-09-19][cite:2026-09-20]. Every other day through 09-11, and
09-18, was green before the 18:00 check, so no grey-check nudge fired on
those days.

n=9 is enough to stop reading this as "too thin," but not to conclude
"nudging doesn't work" — 6 of the 9 rows are the *same* blocker, and
`nudge_converted` is scored against GitHub contributions, which a Mac
`launchd` fix would never produce even if Tom acted on every single one.
Retro 2026-09-20 read this as a measurement gap, not proof of an ignored
nudge, and changed `playbook.md`'s failsafe bullet so a blocker nudge also
counts as converted on the blocker's own recovery signal (a fresh
`local-wip.json`, a resumed runner heartbeat) — future rows on this page
should be readable against that corrected definition, not the old
GitHub-only one this count used.

Separately, six identical repeats of the same unconverted blocker nudge
(09-12→17) before the check switched to a fresh candidate on 09-19 is
itself the finding that motivated the other 2026-09-20 change: `check`
now falls back to the next-best candidate after 3 identical unconverted
blocker nudges rather than repeating verbatim — the blocker still leads
`## Blockers` and the Top Pick write-up every day regardless.

## A second nudge type fired early, then fired false: attribution nudges

2026-08-30 saw the scout fire a nudge *before* the 09:00 candidate list was
even drafted — an unpushed `ivy` commit on the Mac carried a disconnected
author identity, and the playbook's attribution rule outranks every other
candidate for exactly this reason [cite:2026-08-30]. This is a different
nudge class from the 18:00 grey-check nudge above (different trigger, same
channel): it exists to catch a misconfig while it is still a one-line
`git config` fix, before it becomes a public history rewrite like the
2026-08-27 `tomgreen.ai` incident [[ops]] [[repos/tomgreen.ai]]. First
observed use of the class the scout section was written to prevent.

**Correction, 2026-09-01.** Most of those nudges were false positives. The
scanner tested the author address for equality against `commit_email`
alone, so repos correctly configured with `tom@pulsarlabsai.com` — verified
on the account, 72 commits, every one resolving `author.login` — reported
`author_email_ok: false` [cite:2026-09-01]. The 08-30 and 08-31 nudges on
`tomgreen.ai` and `talent-scout` had nothing to fix, which is why they
never converted; non-conversion was the correct response to a false alarm,
not a nudging failure. Fixed by making the check membership over
`connected_emails` [[ops]]. Genuine cases do remain — `ai-capability-app`
`24cda31` carries an invented `tom@C2-LAP32-TomGreen.local` and is still
uncounted — so the class keeps its severity ordering; it was the test that
was wrong, not the rule.

**Discrepancy resolved (2026-08-27, contract 2026-08-27-ivy-nudge-audit-01):**
journals described two, then three "nudge cycles" [cite:2026-08-26]
[cite:2026-08-27], but the inflation came from counting scout *top-picks and
carry-overs* as nudges. The "earlier" nudge claimed on 2026-08-26 is
impossible — the system did not exist before 2026-08-23 [cite:2026-08-23],
and 2026-08-23 sent none. The 2026-08-25 journal is consistent with the
single recorded nudge [cite:2026-08-25]. True count: **1 nudge, 0
conversions** — real but n=1; still too thin to tune on alone. Journals'
"nudge cycle" language should be read as "scout pick" unless `state.json`
records a send [cite:2026-08-27].

## The watchlist grows fast

11 → 12 → 14 repos over three days [cite:2026-08-24][cite:2026-08-25]
[cite:2026-08-26], plus one rename in place (`margaux-en-tutor` → `BrightPaws`)
that arrived as a simultaneous add and drop [cite:2026-08-27]. Auto-sync
earns its keep; a hand-curated list would already be wrong.

## Dispatch queue has stalled since D1

Three contracts (`2026-08-27-c2cm-review-01`, two 08-28 `tomgreen.ai` build
contracts) have sat unclaimed in `dispatch/queue/` since 2026-08-27→28 —
none expired, none claimed — because the D2 Mac runner is not live yet
[cite:2026-08-29][cite:2026-08-30]. Not a policy problem (routing config is
untouched and correct); it is an infrastructure gap outside what a
config/playbook tune can fix. Worth tracking so it doesn't read as "no
demand" when it is actually "no runner."

## Changelog

- 2026-09-24 (failsafe) — updated the fire-rate note: 8 of the last 13
  days since 09-12 (was 8/12), with 09-24 joining 09-18, 09-21, 09-22 and
  09-23 as a real-work green day breaking the run — widest repo spread
  (`ivy`, `tomgreen.ai`, `talent-radar`) of any day since 09-10; recorded
  the scanner outage's first scheduled-window publish, 16 days after going
  dark. No nudge sent today (green all day), so the nudge-conversion count
  is unchanged.
- 2026-09-23 (failsafe) — updated the fire-rate note: 8 of the last 12
  days since 09-12 (was 8/11), with 09-23 joining 09-18, 09-21 and 09-22
  as a real-work green day breaking the run — this time on `ivy` itself
  (three draft PRs), not one of the usual product repos; noted a fix for
  the scanner outage (`ivy` PR #22) opened the same evening. No nudge
  conversion (nudged `tomgreen.ai` PR #34, which the green day did not
  touch), so the nudge-conversion count is unchanged at n=9, 0 converted.
- 2026-09-22 (failsafe) — updated the fire-rate note: 8 of the last 11
  days since 09-12 (was 8/10), with 09-22 joining 09-18 and 09-21 as a
  real-work green day breaking the run. No nudge sent today (green before
  the 18:00 check), so the nudge-conversion count is unchanged.
- 2026-09-21 (failsafe) — updated the fire-rate note: 8 of the last 10
  days since 09-12 (was 8/9), with 09-21 joining 09-18 as a real-work
  green day breaking the run. No nudge sent today (green before the 18:00
  check), so the nudge-conversion count is unchanged.
- 2026-09-20 (failsafe) — extended both sections with today's outcome:
  fire rate now 8/9 days since 09-12 (was 7/8); nudge conversion now n=9,
  0 converted (was n=8) — today's nudge repeated the 09-19 `talent-radar`
  PR #2 candidate verbatim, still unconverted.
- 2026-09-20 (retro) — rewrote both stale sections against the full
  window: failsafe fire rate updated from 2/22 to 7/28 (7 of the last 8
  days), all inside the local-WIP scanner outage, now read as a real
  candidate explanation rather than a thin correlation; nudge conversion
  updated from n=3 to n=8 and reread as a measurement gap (6 of 8 rows
  are the same blocker, scored against a metric that can't register an
  infra fix) rather than proof nudging fails — both readings fed two
  `playbook.md` adjustments this retro (blocker-nudge decay cap at 3
  repeats; `nudge_converted` also true on a blocker's own recovery
  signal). See `CHANGELOG.md` v9.
- 2026-09-13 (retro) — corrected two stale claims: the never-fired-failsafe
  note (fired once, 2026-09-12, streak 20) and the nudge count (now 2,
  both unconverted, second one a blocker not a candidate). Both sections
  had gone unedited since 09-05 while the daily failsafe recorded the
  underlying facts elsewhere (`state.json`, `[[repos/ivy]]`) without
  updating this page — a synthesis gap, not a wrong observation at the
  time it was written.
- 2026-09-05 — recorded that even a green 18:00 reading can be mid-day:
  two more `tomgreen.ai` PRs landed 18:20→19:30 CEST tonight, after the
  check had already recorded green.
- 2026-09-01 — attribution-nudge pattern corrected: the 08-30/08-31 nudges
  were false positives from a too-narrow address check; non-conversion was
  the right response. Rule kept, test fixed.
- 2026-08-30 (retro) — extended never-fired-failsafe note to 7 days;
  recorded the first same-morning attribution nudge as a distinct pattern;
  logged the stalled dispatch queue; no ladder change made this week (n=1
  nudge, 0/7 failsafe fires — both read as healthy, not undertuned).
- 2026-08-27 — nudge-count discrepancy resolved: journals had counted scout
  picks as nudge cycles; recorded count (1 nudge, 0 conversions) confirmed
  against primary sources (contract 2026-08-27-ivy-nudge-audit-01).
- 2026-08-27 — page created from `state.json` outcome history and journals
  2026-08-23→27.
- 2026-08-27 (failsafe) — extended the never-fired streak note to 5 recorded
  days; no other pattern changed today.
