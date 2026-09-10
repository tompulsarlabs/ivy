---
id: 2026-09-10-tomgreenai-planetarymap-review-01
type: review
state: open
repo: tompulsarlabs/tomgreen.ai
lane: workhorse
pool: openai
created: 2026-09-10T09:00:00+02:00
created_by: scout
expires: 2026-09-12T09:00:00+02:00
budget: { wall_minutes: 30 }
---

## Task

Review PR #54 ("Refine planetary map materials, motion and navigation") on
its current head. Adversarial pass: correctness of the new gravitational-well
approach/capture path (timing claims of 1.4s first journey / 0.9s repeat,
camera-drag perspective changes, the clock-driven dissolve replacing the old
video-plate capture), regressions to the previously-shipped navigation
contract (map → system → destination, browser Back, focus restoration,
reduced-motion/WebGL fallbacks), and whether the PR body's validation claims
(289 unit tests, 26 E2E checks, 12-route content guard, TypeScript/ESLint/
production build) hold against the actual diff. Flag anything that reads as
asserted but not shown. Findings as file:line with a proposed fix each, or a
plain confirmation where a section is genuinely sound.

## Definition of done

A findings report exists at
dispatch/reports/2026-09-10-tomgreenai-planetarymap-review-01.md, each
finding tied to file:line, committed and pushed.

## Verification (cloud-checkable)

The report file exists on main of ivy, is non-empty, and every referenced
path exists on the PR head.
