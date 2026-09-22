# Report — 2026-09-22-talentscout-research-review-01

Produced by the workhorse/openai lane, 1.4 wall-minutes.

# PR #1 review — Scout research demo

Reviewed `52122c2..96f3f4c` (`codex/notion-search-demo`), the two commits corresponding to PR #1. This is a read-only review; no report file, commit, or push was made.

## Findings

- **P2 — claimed “73 interaction checks” is not supported by the committed checker.** `demos/notion-search/qa.js:2` increments `results` once per `assert`; its two loops contribute 10 company assertions (`:8`) and 30 packet assertions (`:10`), while the remaining assertions total 24. The script therefore returns 64 checks, not 73. `wide-check.js:4-14` is a separate responsive checker and does not yield nine additional interaction checks.  
  Proposed fix: change `demos/notion-search/README.md:11` and `docs/HANDOFF.md:20` to “64 interaction checks,” or commit the missing nine assertions and a reproducible run record.

- **P2 — workspace isolation is documented as intended, but not proven by the included evidence.** `demos/notion-search/verification/2026-09-21-notion-access.json:1-4` records only page/database IDs; each packet is marked `withinScoutSubtree` (`:7-185`), but there is no root-page permission, workspace identity, build-record sibling, or independent-recipient result. The same file explicitly records `guestAccessVerified: false` (`:187`). The handoff accurately calls this out (`docs/HANDOFF.md:32-34,42`), so the PR should not be described as having verified isolation for an invited user.  
  Proposed fix: keep the current “not cleared for sharing” status and, before sharing, record a redacted root/subtree/build-record hierarchy plus an independent invited-viewer test showing access to only the intended subtree.

## Confirmations

- **No runtime backend is merged in PR #1.** The diff adds only the static demo package, documentation, and an ignore rule; it does not modify `src/`, API routes, Supabase migrations, deployment configuration, or dependencies. The build reads local JSON/template/JS and writes a static HTML attachment (`demos/notion-search/build.py:1-18`); the interaction layer only mutates in-memory preview state (`demos/notion-search/interaction.js:1-33`). This supports the scoped claim in `docs/designs/SCOUT-RADAR-SHARED-CORE.md:39-43`.

- **The generated preview itself makes no runtime network or model calls.** The template embeds all data and interaction code (`demos/notion-search/template.html:224-231`), and the committed QA explicitly rejects external script resources (`demos/notion-search/qa.js:22`). Links open only on user action from research packets (`demos/notion-search/interaction.js:14,27`); they are not automatic backend or Notion API calls.

- **The private-Notion-artifact scope is appropriately described, with one important limit.** The repository contains a live Notion URL (`demos/notion-search/README.md:13`) and the handoff says the generated artifact was uploaded (`docs/HANDOFF.md:7-10`), but no upload client, Notion token, API call, provisioning code, or permission change is in the PR. Thus the code diff does not itself reach a shared/production Notion workspace; the actual Notion state remains externally asserted and only owner-readability is evidenced (`verification/2026-09-21-notion-access.json:7-185`).

- **Native Notion priorities/notes are kept distinct from temporary preview controls.** Preview changes exist only in JavaScript memory (`demos/notion-search/interaction.js:2-3,19-24`), while the UI explicitly directs lasting decisions to the native Notion record (`:14`, `demos/notion-search/template.html:224`). This matches the documented boundary (`docs/HANDOFF.md:14-15`).

- **PR #2 requires no corrective change to PR #1’s static demo.** The stacked branch adds product workspace files under `src/` and leaves `demos/notion-search/` unchanged. Its handoff explicitly preserves the Notion source/workspace (`docs/HANDOFF.md:17` on the stacked branch). The only follow-up is to retain the PR #1 boundary language until recipient-access verification is completed.

- **Whitespace check:** `git diff --check 52122c2..96f3f4c` produced no whitespace errors.
