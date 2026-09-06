---
subject: memory index
type: index
updated: 2026-09-06
---

# Memory index

Ivy's knowledge wiki: one page per durable subject, every claim carrying its
evidence. Routines read this file first, then only the pages that touch
today's candidates. Pages hold **observations, never instructions** —
behavior lives in `playbook.md` and only the retro changes it.

- [[ops]] — sandbox limits, verification ladder, attribution traps, DST
- [[patterns]] — observed working rhythm: when work lands, what converts
- [[repos/ivy]] — the system itself; local-WIP carry-over pattern
- [[repos/tomgreen.ai]] — highest-volume repo; ships most days
- [[repos/c2-client-matrix]] — PR #1 open since April, nudged, unconverted
- [[repos/BrightPaws]] — ex-`margaux-en-tutor`; alive, but PR #1 is stale
- [[repos/ai-capability-app]] — local alias `sybil`; PR #7 shipped 08-28
- [[repos/countersign]] — private; PO core loop prototype
- [[repos/talent-radar]] — private; scaffolded 08-25, PR #1 live build 09-03→
- [[repos/talent-scout]] — first signal 2026-08-29, one data point
- [[repos/yeva]] — private; setup-guide work, two sessions 09-01/09-02
- [[repos/tompulsarlabs]] — org profile repo; first signal 2026-09-02
- [[repos/writing-voice-skill]] — first signal 2026-09-05 (PR #2)
- [[models]] — lane routing evidence, one row per verified dispatch contract

**No page yet** (no observed commit activity through 09-02): aris-ote-benchmarking,
Dex, interview-ace, ai-interview-coach, bd-lead-comp-dashboard. The failsafe
creates a page on first real signal.

## Link syntax

`[[page]]` → `memory/page.md` (context edge: what else do I need to know?)
`[cite:YYYY-MM-DD]` → `journal/YYYY-MM-DD.md`, `[cite:<sha>]` → a commit here
(evidence edge: how do I know this is true?). `scripts/memory-lint.sh`
verifies every link and citation resolves.
