---
subject: observed working rhythm
type: patterns
updated: 2026-09-13
---

# Patterns: how the work actually happens

Observations about the rhythm of real work, drawn from outcome history. These
are findings, not directives — the retro decides whether any of them should
change the ladder, and `playbook.md` is the only place behavior lives.

## The failsafe fired for the first time on day 21

Real work carried every one of the first 20 recorded days (2026-08-23→11):
never once did the floor need to fire [cite:2026-08-28][cite:2026-08-29].
That ended 2026-09-12 — a genuinely quiet day (no connected-author
commit/PR/issue anywhere org-wide from the 18:00 check through 22:30) —
where the failsafe wrote the journal entry itself and secured the streak at
20 [cite:2026-09-12]. Fire rate now 1/21. This is the floor doing exactly
its designed job the one time it was needed, not evidence of a problem —
still one data point, so no ladder-timing change follows from it. The prior
reading (0/7, then 0/20) was never "the floor is untested," only "the floor
hasn't been needed yet"; it has now been needed once and worked.

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

## Nudge conversion is 0 for 2 — resolved count

Two *grey-check* nudges have ever been sent, both push channel, both
unconverted: 2026-08-24 (`c2-client-matrix #1`) [cite:2026-08-24] and
2026-09-12 (local-WIP scanner outage, sent 18:04:40 CEST, the first time a
*blocker* rather than a candidate was the nudge subject — the
blocker-outranks-cheapest-ship rule picked it correctly over the standing
`tomgreen.ai` PR #59 candidate) [cite:2026-09-12]. Every other day through
09-11 was green before the 18:00 check, so no grey-check nudge fired on
those days. Retro reading (2026-09-13): n=2 is still too thin to safely
tune nudge timing, wording, or channel — same discipline held at n=1 since
2026-08-30, unchanged by one more data point in the same direction.

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
