# Report — 2026-09-10-tomgreenai-planetarymap-review-01

Produced by the workhorse/openai lane, 2.0 wall-minutes.

# PR #54 review — 2026-09-10

## Findings

### P1 — Route arrival restores focus to the hidden-map trigger, not the arrived content

[src/components/orbit-portal.tsx:221](src/components/orbit-portal.tsx#L221)

`close()` unconditionally focuses `.sphere-home`, including the `"landing"` path called after the clock has pushed a destination route. This leaves keyboard and screen-reader users at the navigation trigger rather than at the newly arrived document, despite the visual capture resolving to that document.

Proposed fix: restore `.sphere-home` focus only for `"dismissed"` exits. For `"landing"`, focus a meaningful arrival target (`main`, the page `h1`, or an explicit route-arrival focus target) after the route has committed. Add an E2E assertion for focus after a captured leaf lands.

### P2 — Validation results are asserted without reviewable evidence

[docs/FABLE-DESIGN-HANDOFF.md:55](docs/FABLE-DESIGN-HANDOFF.md#L55)

The stated “289 unit tests,” lint, TypeScript, production build, content guard, and 26 E2E checks are not accompanied by command output, a CI run URL, or an artifact. Source structure supports the claimed scope: the content guard contains 12 routes, and the three cited planetary/capture/page-arrival suites expand to 26 E2E cases. However, pass status and the exact unit-test total cannot be established from the diff alone.

Proposed fix: link the successful CI run (or attach concise command outputs) and state the exact commands used, including the production-build precondition for E2E/content checks.

## Confirmations

- The timing implementation matches the stated 1.4-second first approach and 0.9-second repeat approach: [src/lib/capture-timing.ts:18](src/lib/capture-timing.ts#L18), [src/lib/capture-timing.ts:37](src/lib/capture-timing.ts#L37), with direct unit coverage at [src/lib/capture-timing.test.ts:22](src/lib/capture-timing.test.ts#L22) and [src/lib/capture-timing.test.ts:62](src/lib/capture-timing.test.ts#L62).
- The capture no longer fetches retired video plates: the live path only selects a rendering tier and arms the clock, while E2E aborts all retired-media routes and asserts no requests: [src/components/orbit-portal.tsx:535](src/components/orbit-portal.tsx#L535), [e2e/capture-engine.spec.ts:52](e2e/capture-engine.spec.ts#L52).
- The page dissolve is clock-driven and alpha-reveals the underlying document rather than sampling video media: [src/components/golden-path-layer.tsx:34](src/components/golden-path-layer.tsx#L34).
- The map → system → destination and browser-Back sequence has substantive E2E coverage across every world: [e2e/planetary-fidelity.spec.ts:113](e2e/planetary-fidelity.spec.ts#L113), [e2e/golden-path.spec.ts:113](e2e/golden-path.spec.ts#L113).
- Reduced-motion, Save-Data, unavailable-WebGL, and context-loss fallbacks preserve keyboard-accessible destination links and transfer existing focus between live labels and fallback links: [src/components/operating-orbit-live.tsx:49](src/components/operating-orbit-live.tsx#L49), [src/components/operating-orbit-live.tsx:114](src/components/operating-orbit-live.tsx#L114), [e2e/planetary-fidelity.spec.ts:176](e2e/planetary-fidelity.spec.ts#L176).
