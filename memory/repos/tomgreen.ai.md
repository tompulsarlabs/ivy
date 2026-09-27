---
subject: tompulsarlabs/tomgreen.ai
type: repo
updated: 2026-09-24
---

# tomgreen.ai

Public. Created 2026-08-24 and shipped v1 the same day [cite:2026-08-24]. Since
then it has been the highest-volume repo on the account by a wide margin and
the usual reason a day is green.

## Activity

| Date | Non-bot commits | Note |
|------|-----------------|------|
| 2026-08-24 | 12 | v1: all routes, live proof strip, motion pass [cite:2026-08-24] |
| 2026-08-25 | 1 | `f88d03d` Obsidian-style knowledge graph, 14:19 local [cite:2026-08-25] |
| 2026-08-26 | 26 | 11:17–20:52 local; design system round + WebGL rebuild [cite:2026-08-26] |
| 2026-08-27 | 6 | 06:42–07:55 local — **none countable**, see below [cite:2026-08-27] |
| 2026-08-28 | 46 (org total) | 3 merged PRs (#3/#4/#5) + direct pushes; largest day recorded so far [cite:2026-08-28] |
| 2026-08-29→30 | — | PR #6 ("solar system becomes the site") opened 08-28, drafted through 08-29, merged 2026-08-30T00:10 CEST after an 18:09→00:10 run [cite:2026-08-29][cite:2026-08-30] |
| 2026-09-05 | 14 PRs merged | New record: PR #16 (carried from 09-04) through #29, one continuous 08:20→19:30 CEST run — "planetary capture engine," mobile CV/nav/hover fixes, copy clarity, home/lab role split [cite:2026-09-05] |
| 2026-09-24 | 3 PRs merged | PR #66 (10:44 CEST, homepage company/role context), #67 (17:35 CEST, `/lab` made canonical), #68 (19:40 CEST, Substack essay) — spread across the day rather than one run, only one of the day's five merged PRs org-wide [cite:2026-09-24] |

The 2026-08-26 run covered a full design-system round trip (white primary
ground, twilight planetary map, career corridor walkthrough, per-stop company
impact pages, CI green, accessibility hardening) plus a black-hole entrance
rebuilt as a WebGL raymarched Schwarzschild render after the 2D version did not
clear the bar [cite:2026-08-26].

## It consumes Ivy's `state.json`

The site's live proof strip reads GitHub contributions **and Ivy's own
`state.json`** [cite:2026-08-24]. This repo is therefore a downstream consumer
of [[repos/ivy]]: changing the shape of `state.json` is a cross-repo breaking
change, not a local refactor. Ivy's cloud runs are scoped to `ivy` alone
[[ops]], so the consuming code cannot be inspected from a routine — treat
`state.json` keys as a public contract and add rather than rename.

## Attribution incident, 2026-08-27 (recovered 2026-08-28)

Six real commits landed on `main` authored `Tom Green
<tom@Toms-MacBook-Air.local>` — an address not connected to the account, so
none of them counted [cite:2026-08-27]. Cause and detection are in [[ops]].
**Recovered 2026-08-28**: history rewritten on the Mac (author dates
preserved, new SHAs `4cc1d9f`→`bd3274a`), force-pushed, verified — all six
now carry the connected author and count on 2026-08-27, their real day
[cite:2026-08-28]. Note: `main` history before that point was rewritten, so
any stale clone needs `git fetch && git reset --hard origin/main`.

## Open threads

- Launch waits on DNS cutover and the `SITE_LAUNCHED` flag [cite:2026-08-26].
- Vercel hookup pending — the integration lacks project-create permission
  [cite:2026-08-24].
- ~~**Attribution risk recurring, 2026-08-31.**~~ **False alarm, corrected
  2026-09-01** — the checkout is configured with `tom@pulsarlabsai.com`,
  which is verified on the account and counts; the scanner was comparing
  against `commit_email` alone [[ops]] [cite:2026-09-01]. Original entry
  kept below for the record: Local checkout still shows
  `author_email_ok: false` / `last_commit_email_ok: false`, sitting on
  `claude/fable-system-design-retro-qrvdfy` rather than `main`
  [cite:2026-08-31]. Scout nudged same-morning despite `dirty_files: 0` /
  `unpushed_commits: 0` (nothing queued at that instant) because this is the
  exact repo and failure mode behind the 2026-08-27 rewrite
  [cite:2026-08-31]. Unfixed as of the 17:45 CEST scan — not yet converted.

## Changelog

- 2026-09-24 (failsafe) — recorded PR #66/#67/#68 merged, spread across
  10:44→19:40 CEST rather than one continuous run; same day `talent-radar`
  landed its first two merges ([[repos/talent-radar]]), so this repo was
  one contributor to a green day rather than the sole one, for the first
  time since 09-10.
- 2026-09-05 — recorded the highest single-day PR-merge count yet: 14 PRs
  (#16→#29) merged in one continuous 08:20→19:30 CEST run, extending well
  past the 18:00 check. Two review contracts also verified done tonight,
  one against the merged PR #16 directly [[models]].
- 2026-09-01 — 08-31 attribution risk marked a false alarm: the address is
  connected, the scanner's check was too narrow.
- 2026-08-31 (failsafe) — recorded the recurring attribution-risk nudge and
  its non-conversion by day's end.
- 2026-08-30 (retro) — added 08-28 (46-commit day) and 08-29→30 (PR #6
  merge) activity rows.
- 2026-08-28 — attribution incident resolved: six 08-27 commits recovered
  via history rewrite, verified counting.
- 2026-08-27 — page created from journals 2026-08-24→27 and `state.json`.
