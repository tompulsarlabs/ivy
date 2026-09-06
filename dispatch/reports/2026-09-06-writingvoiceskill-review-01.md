# Report — 2026-09-06-writingvoiceskill-review-01

Produced by the frontier/openai lane, 5.4 wall-minutes.

# PR #2 adversarial review

**Head reviewed:** `6872b5ef37ee83c678ccc424d81aa8d2735aa1f5`  
**Verdict:** Changes requested. The PR removes the forced 10% cut and adds useful controls, but conflicting absolute rules and underspecified checks still permit meaning drift and false-confidence rewrites.

## Findings

### 1. High — Meaning preservation is asserted but not operationally checked

**Locations:** `writing-voice-custom/SKILL.md:27`, `writing-voice-custom/SKILL.md:31`, `writing-voice-custom/SKILL.md:266`, `writing-voice-custom/SKILL.md:293`, `writing-voice-custom/eval.md:53`

The process reduces intent to one “core argument” and ends with a subjective restraint check. That does not protect secondary claims, negation, quantities, scope, attribution, causal status, conditions, exceptions, or degrees of certainty. “Qualifications supported by the evidence” is also ambiguous when the editor has no evidence beyond the draft.

**Proposed fix:** Add a before/after semantic-invariant check. Before editing, record each claim’s actor/action, polarity, quantities and dates, quantifier, attribution, causal status, conditions/exceptions, and certainty level. After editing, compare them one-for-one. No invariant may change unless the user requested it or supplied supporting evidence; otherwise retain or flag the passage. Mirror these criteria explicitly in P.1.

### 2. High — The specificity examples teach unsupported invention

**Locations:** `writing-voice-custom/SKILL.md:199`, `writing-voice-custom/SKILL.md:201`, `writing-voice-custom/SKILL.md:236`, `writing-voice-custom/SKILL.md:237`, `writing-voice-custom/SKILL.md:238`, `writing-voice-custom/eval.md:97`, `writing-voice-custom/eval.md:99`, `writing-voice-custom/eval.md:107`, `writing-voice-custom/eval.md:109`

C3 supplies only “rightsize,” yet its expected result equates that with layoffs. Rightsizing could also mean attrition, redeployment, hiring freezes, or other changes. The “fifteen leaders” example invents evidence unless that evidence existed elsewhere, while the two AI examples replace the author’s proposition with different unsupported propositions. C5 likewise demands a rewrite scaled to “stated evidence,” although the case contains no evidence.

**Proposed fix:** State that specificity may only come from the draft or supplied sources. If a euphemism’s referent is unknown, flag it and ask for the concrete event rather than guessing. Give C3 explicit source facts, or make its expected result an ambiguity flag. Prefix the line 236 examples with their source evidence, and make C5’s correct response flag insufficient support instead of generating a replacement claim.

### 3. High — The remaining hedge rules contradict warranted uncertainty

**Locations:** `writing-voice-custom/SKILL.md:52`, `writing-voice-custom/SKILL.md:54`, `writing-voice-custom/SKILL.md:58`, `writing-voice-custom/SKILL.md:222`, `writing-voice-custom/SKILL.md:234`, `writing-voice-custom/SKILL.md:235`, `writing-voice-custom/eval.md:154`

“Kill Qualifiers and Hedges,” “almost never,” “both are dishonest,” and “fix without hedging” remain categorical instructions. They compete directly with the new preservation clause. Removing “I think,” “may,” “approximately,” or “to some extent” can change attribution, commitment, statistical precision, legal discretion, or epistemic confidence.

**Proposed fix:** Rename the section “Remove empty qualification; preserve semantic qualification.” Replace the categorical language with a test: if deletion changes truth conditions, degree, scope, attribution, obligation, or confidence, retain it. Treat source-language uncertainty as meaning unless the user asks for fact-checking and provides stronger evidence. Remove “no hedging” from the documentation-writing rule.

### 4. High — “Take a position” can manufacture an unsupported conclusion

**Locations:** `writing-voice-custom/SKILL.md:244`, `writing-voice-custom/SKILL.md:290`, `writing-voice-custom/SKILL.md:324`, `writing-voice-custom/SKILL.md:343`, `writing-voice-custom/eval.md:49`, `writing-voice-custom/eval.md:114`

The new checklist correctly limits this rule to argumentative writing, but the editorial layer, full-edit process, ghostwriting process, and rubric still apply it universally. A factual report, options memo, scientific result, or genuinely inconclusive analysis may correctly end conditionally or with “it depends.” C6 requires a position despite supplying no supporting evidence.

**Proposed fix:** Scope the rule consistently to persuasive writing and preservation of the author’s existing thesis. For factual or analytical work, require the conclusion to match the evidence, including inconclusive or conditional outcomes. Revise L3.5 accordingly and add a control case where “it depends” is correct because named conditions produce different results.

### 5. Medium — The “precise verb” examples are not meaning-equivalent

**Locations:** `writing-voice-custom/SKILL.md:44`, `writing-voice-custom/SKILL.md:46`, `writing-voice-custom/SKILL.md:47`, `writing-voice-custom/SKILL.md:73`, `writing-voice-custom/eval.md:89`

“Sprinted” adds a specific speed and effort not entailed by “ran quickly”; “whispered” adds a vocal mechanism not entailed by “said softly”; replacing “asserted” with “said” can erase the speech act. C1 nevertheless requires a stronger verb and no `-ly`, encouraging semantic substitution to satisfy a surface rule.

**Proposed fix:** Permit folding a modifier into a verb only when context establishes equivalence. Otherwise retain the modifier or recast without strengthening the event. Rewrite C1 so its expected output must preserve gait, volume, and speech-act meaning, and add a false-positive example where an `-ly` modifier carries indispensable meaning.

### 6. Medium — “Banned word” instructions contradict the contextual trigger-word rule

**Locations:** `writing-voice-custom/SKILL.md:113`, `writing-voice-custom/SKILL.md:115`, `writing-voice-custom/SKILL.md:283`, `writing-voice-custom/SKILL.md:302`, `writing-voice-custom/SKILL.md:338`, `writing-voice-custom/eval.md:38`

Layer 2 explicitly says these terms are flags, not bans, but both editing modes and the final checklist call them banned. An agent following the process literally can mechanically delete legitimate terms and fail C8.

**Proposed fix:** Replace every “banned” reference with “flagged-word and filler-phrase check.” In each process step, explicitly require the line 115 contextual test and preservation of earned terms.

### 7. Medium — Requested scope is only protected for Voice Check

**Locations:** `writing-voice-custom/SKILL.md:27`, `writing-voice-custom/SKILL.md:260`, `writing-voice-custom/SKILL.md:275`, `writing-voice-custom/eval.md:135`

The default Full Edit applies every structural and line-edit rule. There is no executable handling for “proofread only,” “fix grammar but keep wording,” “do not shorten,” quoted text, or legally controlled language. C10 verifies only the Voice Check branch.

**Proposed fix:** Add a scope gate before mode selection: explicit user constraints override the default workflow; unqualified “edit/improve” selects Full Edit, while proofreading, grammar-only, formatting-only, and preserve-wording requests prohibit broader rewrites. Add regression cases for a grammar-only request and text containing an exact quotation or controlled legal wording.

### 8. Medium — C9 does not exercise editing and is omitted from mandatory regression guards

**Locations:** `writing-voice-custom/eval.md:130`, `writing-voice-custom/eval.md:133`, `writing-voice-custom/eval.md:158`, `writing-voice-custom/eval.md:175`, `writing-voice-custom/SKILL.md:357`

C9 contains nothing that should be edited, so returning it unchanged passes without proving that an agent can remove real filler while preserving uncertainty. The self-learning loop, precision discussion, and skill note still identify only C7/C8 as required controls, allowing future hedge changes to skip C9/C10.

**Proposed fix:** Make C9 a mixed case containing removable filler plus semantic uncertainty—for example, an observational result with a sample size, numeric range, attribution, “may,” and a non-generalization caveat. List those items as invariants. Require C7–C10 after changes affecting editing policy, and update the precision section and skill note to name all four guards.

### 9. Medium — Public documentation still advertises the behavior this PR removes

**Locations:** `README.md:7`, `README.md:50`, `README.md:51`

The README still promises “10% rule,” “no adverbs,” “kill qualifiers/hedges,” “banned-word list,” and mandatory 10% cuts. Users or integrators following it will expect—and may independently enforce—the old behavior.

**Proposed fix:** Update the overview and mode descriptions to describe judgment-based economy, meaningful modifiers, warranted uncertainty, contextual trigger-word checks, and numeric targets only when requested. Also update “Three editing modes” to account for Ghostwrite or distinguish editing modes from writing mode.

### 10. Medium — The evaluation evidence requirement is absent from its own scorecard format

**Locations:** `writing-voice-custom/eval.md:61`, `writing-voice-custom/eval.md:78`

Line 78 requires model, harness, instruction revision, artifacts, reviewer, and evidence, but the prescribed scorecard has none of those fields. No result artifact exists on the PR head, so the behavior change remains unverified under the file’s own standard.

**Proposed fix:** Add the required metadata fields to the scorecard template and commit a result for C7–C10 with captured inputs, outputs, revision SHA, model/harness identity, and independent grading. Mark absent runs `UNVERIFIED`.

## Sound sections

- `writing-voice-custom/SKILL.md:31`, `writing-voice-custom/SKILL.md:303`, and `writing-voice-custom/SKILL.md:332` correctly remove the unconditional 10% target and prioritize meaning when a requested target conflicts.
- `writing-voice-custom/SKILL.md:111` through `writing-voice-custom/SKILL.md:127` provides a useful contextual test for trigger words; it is concrete and supported by the C8 control.
- `writing-voice-custom/eval.md:116` through `writing-voice-custom/eval.md:126` supplies strong already-tight and legitimate-vocabulary false-positive controls.
- `writing-voice-custom/eval.md:135` through `writing-voice-custom/eval.md:138` clearly and checkably enforces the no-rewrite Voice Check mode.
- `writing-voice-custom/eval.md:78` correctly rejects missing or self-graded evidence as a pass, subject to adding those fields to the actual scorecard.

Static inspection and `git diff --check` completed. No model-quality eval was run, and no files, commits, or remote state were changed.
