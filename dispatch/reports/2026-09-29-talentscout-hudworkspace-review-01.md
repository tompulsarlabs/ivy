# Report — 2026-09-29-talentscout-hudworkspace-review-01

Produced by the workhorse/openai lane, 10.4 wall-minutes.

# PR #3 review — request changes

Reviewed head `ae4cfc3` against the PR body. No count overstatement was found, but two evidence/decision-context defects make the workspace unsuitable as a reliable hiring packet.

## Findings

### P1 — Three OpenAI profile identities lack the displayed source needed to prove them

**Locations:** `demos/hud-search/research.ts:54`, `:359`, `:368`, `:377`

The facts for Theophile Sautory, Robert Tinn, and Josiah Grace say both that the Cookbook registry attributes an artifact to an alias and that its author directory maps that alias to the named person. Each packet links only `u.registry`; `u.authors` is declared but unused. The registry establishes aliases, while the [authors directory](https://github.com/openai/openai-cookbook/blob/main/authors.yaml) supplies the human-name mapping.

This contradicts the PR body’s claim of 51 person-evidence links and full research packets: a reviewer cannot verify the displayed identity from the packet’s clickable evidence.

**Proposed fix:** Split each attribution into registry and author-directory evidence, or use one immutable source containing both mappings. Add a regression test for alias-to-name citation coverage. Recompute the advertised 51-link total if this adds a distinct displayed URL.

### P1 — Per-profile feasibility and decision-change data is prepared but not shown

**Locations:** `demos/hud-search/app/SearchWorkbench.tsx:86-93`; `demos/hud-search/workbench-model.ts:25`; `demos/hud-search/research.ts:68-73`

The drawer renders evidence, counter-case, and route, but never renders `selected.location`, `selected.wouldChange`, or `selected.next`. The Markdown shortlist omits all three and additionally drops the relationship-aware route. Those fields carry the profile-specific current-remit, location/timezone, interest, and “what would change priority” caveats for all expanded entries.

The PR body says recruiting feasibility remains explicit and promises full research packets plus a working Markdown shortlist. Generic “not confirmed” boilerplate is not a substitute for the profile-specific caveat.

**Proposed fix:** Render labelled “Current status / feasibility,” “What would change priority,” and “Next research step” sections in the drawer; include those fields and `route` in `shortlistMarkdown`. Add data and browser/export tests covering an original and an expanded profile.

### P2 — Verification documentation names a different deployment than the PR and its evidence

**Locations:** `demos/hud-search/README.md:49`; `demos/hud-search/verification/production.json:3`; `demos/hud-search/verification/browser.json:24`

The README identifies `dpl_EutmxsusveJ8gUWeF1otc7jsdwn6`; the PR body and both verification artifacts identify `dpl_4xGYzLV38fXMd1qrC6J4BQTTF8Pu`.

**Proposed fix:** Update the README to the verified deployment ID, or explicitly document both deployments and which checks each supports.

### P2 — Core advertised coverage is not regression-protected

**Location:** `src/lib/scout/hud-demo.test.ts:10-26`

The PR body claims 14 distinct pools and 51 distinct person-evidence links. The test verifies 40 distinct people, 20 per role, a nonempty fact, and a valid context URL, but not either advertised aggregate. `verification/browser.json` is a manual checklist, not executable regression coverage.

**Proposed fix:** Add deterministic assertions for the 14-pool union and 51 unique displayed person-evidence URLs, plus browser coverage for the packet/export fields above.

## Reconciled claims and non-findings

- The committed data currently supports 20 people per role, 40 distinct people, 10 commercial plus 9 engineering pools with a 14-pool union, and 51 unique displayed person-evidence URLs. No current count discrepancy found.
- `verification/source-links.json` supports the PR’s dated reachability arithmetic: 69 URLs, 64 HTTP 200, two HUD HTTP 429s, and three LinkedIn HTTP 999s. It is not proof of claim accuracy.
- No application-originated live model, Notion, or backend call was found in the HUD graph: it is a static export (`demos/hud-search/next.config.mjs:1`), has fixed role params (`app/[role]/page.tsx:5-14`), and uses local storage plus local Blob export (`SearchWorkbench.tsx:20-50`; `src/lib/scout/review-state.ts:35-42`). User-clicked evidence links are the only intended external navigation.
- No additional operating-map source/coverage defect was confirmed.

## Verification limits

`git diff --check` completed cleanly. I did not rerun the PR’s build, test suite, or production browser checks from this read-only checkout, so the claimed passing execution remains self-attested.

Per the explicit read-only rule, this report was emitted only: no file was written, committed, or pushed.
