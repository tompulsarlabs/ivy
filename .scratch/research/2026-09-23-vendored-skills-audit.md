# Skills audit: dated prompting patterns in the vendored mattpocock/skills

Audit of `.claude/skills/` for the Claude Opus 5.5, Claude Sonnet 5 and Claude Fable 5.1 generation, done on 2026-09-23. It is read-only: nothing in the repository was changed. Each finding carries its proposed edit as replacement text (one hunk per finding). There is no separate patch file: the skills are vendored upstream material, and the branch this audit informed leaves them unforked. The Ivy-side changes are under "Ivy adapter gaps".

**State audited.** The skills tree matches `skills-lock.json` and current upstream. Ivy-side line numbers refer to commit `fbb846d` on branch `claude/skills-playbooks-refresh-784cgk`; the branch's later commits apply G1 to G6, G2's contract convention, and G9.

## Summary

| Pattern group | High | Medium | Low (flag) |
|---|---|---|---|
| 1. Dated prompt text | 1 | 9 | 2 |
| of which 1a: pressure language, hedges, default-to-tool | | 6 (F2, F3, F6, F7, F10, F11) | 2 (F12, F13) |
| of which 1b/1f: numeric output caps | 1 (F1) | | |
| of which: verification scaffolding (Step 3 and the migration notes) | | 2 (F4, F5) | |
| of which 1e: style prohibitions | | 1 (F9) | |
| 2. Brittle skill files | | 1 (F8) | 1 (F14) |
| 3. Descriptions and trigger text | 0 | 0 | 0 |
| 4. Request config | 0 | 0 | 0 (the skills contain none) |
| Outside the four groups: interactive waits in runs where nobody can answer | | | 2 flags (F15, F16) |

The totals are 1 High, 10 Medium, 3 Low and 2 out-of-group flags. 14 of the 25 skills had no finding in the four groups. Nothing in the tree matched these patterns:

- think-step-by-step or scratchpad scaffolds
- prefills or JSON forcing
- grader vocabulary
- retired model names
- narration suppressors
- rules against formatting
- instructions re-inserted on a cadence
- identity stubs
- history narratives

The three findings with the most impact:

1. **code-review's sub-agent briefs end "Under 400 words."** (`code-review/SKILL.md:64`, `:70`). The Standards brief asks for "every place the diff violates a documented standard" and then caps the report. The migration notes document that Sonnet 5 and Opus 5 apply a review prompt's stated bar faithfully: they find the issues, then leave out whatever falls below the bar. A word ceiling is such a bar, so findings get dropped to fit. This skill is upstream's general review path, and it is the review discipline Ivy names for every review and build worker. Ivy's runner, new on this branch, gives the worker a concrete bar with severity and confidence, which is the form the review guidance recommends. That bar sits in the orchestrating prompt, though, and the skill still hands its sub-agents the capped brief (gap G1).
2. **writing-for-agents says that when a word like "be thorough" is a no-op, "the fix is a stronger word (_relentless_)"** (`writing-for-agents/SKILL.md:81`). For that exact example, the audit guide's documented fix on current models is to delete the word, because intensity words over-apply. Ivy's Sunday retro loads this skill every week to prune playbook.md, the routines and procedures. That makes this the one line that can put the pressure register back into the files every Ivy run reads (gap G3).
3. **Two model-invoked skills assume a person is present to answer** (outside the four groups). tdd says "confirm them with the user. No test is written at an unconfirmed seam" (`tdd/SKILL.md:22`). code-review asks the user for the fixed point and the spec, or sends them to run setup (`code-review/SKILL.md:13`, `:19`, `:32`). Both run under `claude -p` in Ivy's workers, where nobody answers. Upstream already has the fix pattern in two other skills (`diagnosing-bugs/SKILL.md:98`, `prototype/SKILL.md:17`). Ivy's runner, new on this branch, tells workers the run is unattended. The residue is that no build contract names its seams (gap G2).

There are 9 Ivy adapter gaps: 5 medium and 4 low. Seven are partly covered already, and two (G4, G9) are not covered.

## Method, inventory, provenance

- **Method.** I followed `claude-api/shared/prompt-audit.md` Steps 0 to 5 and its keep list. For background I used the two sections of `model-migration.md` I was asked to read ("Migrating to Claude Opus 5 → Behavioral shifts" and "Migrating to Claude Opus 5.5"). I also read two short passages that findings depend on:
  - "Migrating to Claude Sonnet 5 → Behavioral shifts", because Sonnet 5 is the routines' model (lines 1250-1282).
  - The Opus 4.7 "Code review" paragraph, which the Opus 5 severity-filter note points to (lines 779-785).

  I did not read the Fable 5.1 sections. Their rows specific to Fable (rules against formatting, update suppressors, re-inserted instructions) matched nothing in the tree.
- **Signals grepped over the whole tree:**
  - emphasis: caps emphasis, `!!`, intensity words
  - hedges and trait claims: `try to` / `if possible` / `ideally` / `where possible`; trait claims about the model
  - scaffolds: step-by-step and scratchpad instructions, sampling and thinking-budget parameters, cadence choreography, word caps, `STEP`-style numbered imperatives
  - prohibitions and padding: runs of three or more prohibitions, `hallucinate` / `Remember,` / `grade` / `rubric`
  - fossils: retired model names, narration suppressors, bans on tags, OCR or formatting, reminder cadences, `now` / `no longer`, identity stubs
  - volatile specifics: URLs, version pins and dates, past-tense history
  - areas I was asked to check: verify and double-check, severity filters, ask / confirm / wait (for runs where nobody answers), sub-agent and background-agent delegation, token and context-size figures
- **Inventory.**
  - The tree holds 25 skills: 47 Markdown files, 2,945 lines.
  - Not in scope: `agents/openai.yaml` and the two shell templates (`diagnosing-bugs/scripts/hitl-loop.template.sh`, `wizard/template.sh`).
  - 11 skills are model-invoked, so their descriptions load in every routine run: code-review, codebase-design, diagnosing-bugs, domain-modeling, grilling, prototype, research, resolving-merge-conflicts, tdd, wizard, writing-for-agents.
  - 14 are user-invoked: ask-matt, grill-me, grill-with-docs, handoff, implement, improve-codebase-architecture, setup-matt-pocock-skills, teach, to-questionnaire, to-spec, to-tickets, triage, wait-what, wayfinder.
  - The retro calls writing-for-agents and domain-modeling (playbook.md:381, :395).
  - Workers are told to use code-review for review contracts and tdd plus code-review for build contracts (`scripts/dispatch-runner.py:260-273`).
  - Before this branch, the Anthropic worker lanes ran claude-opus-5. config.yml:72, :75 (new on this branch) moves them to claude-opus-5-5, at high and medium effort. The worker runs cited below all used claude-opus-5.
- **Provenance.** Every line blames to a78bf80 (2026-09-02, the vendoring commit). I did not consult upstream history, so no finding rests on blame. Dating rests on target-model documentation and on idiom.
- **Confidence scale.**
  - **High:** the migration notes document the target-model behaviour that makes the text harmful, for a model that actually runs it.
  - **Medium:** the text matches a documented audit-guide row whose reason is the guide's general statement about current models, or the behaviour is documented for Opus 5 and carries to Opus 5.5 as its starting point (model-migration.md:1864, :2039).
  - **Low:** heuristic or idiom-dating. Flagged, with no edit proposed.

## Findings

### High

**F1. A word cap on both review briefs**
- Location: `code-review/SKILL.md:64`, `:70`
- Evidence:
  - Standards brief: "Report, per file/hunk where relevant, (a) every place the diff violates a documented standard ... and (b) any baseline smell you spot ... Skip anything tooling enforces. Under 400 words."
  - Spec brief: "... Quote the spec line for each finding. Under 400 words."
- Pattern: hard word caps (1b) and numeric output ceilings (1f). In a review brief, the cap acts as a severity filter.
- Why obsolete for the target models:
  - The migration notes document that Sonnet 5 and Opus 5 apply a review prompt's stated bar faithfully. They investigate just as thoroughly, then leave out what falls below the bar (model-migration.md:1128, :1272). A 400-word ceiling works as such a bar: on a diff with more findings than fit, the sub-agent has to drop some, and the brief's own "every place" loses to the cap.
  - The documented fix asks for every finding with a confidence and a severity, filtered in a later step (:1274). The audit guide lists word caps among the scaffolds to delete, and says a stated operational reason doesn't turn a numeric clamp into a keeper.
  - The aggregation step (`:78`) wants "the worst issue within each axis", which needs severities that the briefs never ask for.
- Confidence: High
- Reach:
  - Tom's interactive reviews (Opus 5.5).
  - Any Ivy review worker that loads the skill. The runner (new on this branch) sets a concrete bar with severity and confidence in the orchestrating prompt, but that doesn't reach the sub-agent briefs (G1).
  - So far the skill's two-axis shape shows up in 1 of 22 worker reports, so the cap has not yet measurably cut Ivy's reviews.
- Action (rewrite): in both briefs, replace "Under 400 words." with: "Report every finding, including ones you are unsure of or judge minor, with a confidence and a severity for each, so the aggregate can rank within the axis. Keep each finding to what a reader needs to act on it."

### Medium

**F2. An intensity booster on the feedback-loop phase**
- Location: `diagnosing-bugs/SKILL.md:22`
- Evidence: "Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to give up.**"
- Pattern: 1a pressure language (the "Be thorough. Do not be lazy. Do not stop early." row)
- Why obsolete:
  - Current models are proactive by default, and forcefulness written for older models over-applies.
  - Here it also competes with the skill's own stop rule (`:53-55`: "Stop and say so explicitly. List what you tried."). That stop is the behaviour the current Opus guidance asks for: "If you genuinely can't complete something, do the rest and state plainly what's missing and why" (model-migration.md:1081). A run told to "refuse to give up" is less likely to reach it.
- Confidence: Medium
- Reach: the skill is model-invoked, and its description ("reports something broken/throwing/failing/slow") is in every routine run and every session.
- Action (rewrite): "Spend most of your effort here, working down the options below. If none of them yields a loop, stop as described under *When you genuinely cannot build a loop*."

**F3. "The fix is a stronger word"**
- Location: `writing-for-agents/SKILL.md:81`, the last two sentences
- Evidence: "The test also grades leading words: a word too weak to beat the default (_be thorough_ when the agent is already thorough-ish) is a no-op, and the fix is a stronger word (_relentless_), not a different technique."
- Pattern: 1a, escalating emphasis offered as the default repair
- Why obsolete:
  - For this exact example, the guide's row says delete. Current models are proactive by default, and forcefulness over-applies in both directions: over-triggering and rigid behaviour.
  - The rest of the bullet is sound and agrees with the guide: delete no-ops, the test depends on the model, settle it by running the document. Only the repair is dated.
  - The skill's own "Demand" lever (`:50`, raising the completion criterion) is the current-model way to get more than the default.
- Confidence: Medium
- Reach: Ivy's weekly retro, running headless on Sonnet 5, applies this skill's tests to CLAUDE.md, playbook.md, routines/*.md and procedures/ (playbook.md:379-386). The playbook's new prompt-audit clause (:386-390) runs only after a model change, so the weekly pass still applies line 81. Ivy-side mitigation: G3.
- Action (rewrite the two sentences): "The test also grades leading words: a word too weak to beat the default (_be thorough_ when the agent is already thorough-ish) is a no-op, so delete it. If the behaviour it reached for still matters, state the target or raise the completion criterion's demand (see Steps and completion criteria). Reach for a stronger word only when running the document shows the plain statement falls short: current models over-apply intensity."

**F4. Self-review sub-agents as the last step of every implementation**
- Location: `implement/SKILL.md:13`, plus the matching description of the flow at `ask-matt/SKILL.md:26`
- Evidence: "Once done, use /code-review to review the work." / "then closes out by running **`/code-review`**, a two-axis review (Standards + Spec) of the diff, before committing."
- Pattern: verification scaffolding, i.e. behaviour the model already does unprompted (Step 3; the migration notes name it for Opus 5)
- Why obsolete:
  - The notes say "Claude Opus 5 verifies its own work without being asked. Instructions that tell it to verify (... 'use a subagent to verify') now cause over-verification. Removing them reduces over-verification with no capability regression" (model-migration.md:1077).
  - The delegation guidance lists "Review, verification, or to double check your work" as work not to hand to sub-agents (:1096).
  - /code-review at the end of /implement is two sub-agents reviewing the diff the same session just wrote.
  - Opus 5.5 starts from the Opus 5 prompt patterns and asks for them to be re-tested (:1864, :2039). Sonnet 5 "will ... run self-verification loops more readily" (:1260).
- Confidence: Medium. The behaviour is documented for Opus 5 and Sonnet 5; re-test on Opus 5.5.
- Reach:
  - /implement is user-invoked, in Tom's sessions.
  - Ivy's build workers get the same shape from the runner: "review the diff against the Task before opening the PR" (`scripts/dispatch-runner.py:271-273`). See "Workflow observation".
- Action (remove):
  - Delete the line from /implement.
  - At ask-matt:26, replace "then closes out by running /code-review ... before committing" with "then commits; run /code-review on the branch as its own step when you want the two-axis review".
  - If upstream wants the review gate by design, the documented alternative is an independent reviewer: a separate session or another model family. That is what Ivy's cross-family review contracts already are.

**F5. A verification cadence**
- Location: `implement/SKILL.md:11`
- Evidence: "Run typechecking regularly, single test files regularly, and the full test suite once at the end."
- Pattern: verification scaffolding with a cadence (Step 3; the cadence choreography row in 1b)
- Why obsolete:
  - The same over-verification note as F4 applies (:1077, :1260).
  - The /tdd loop this skill drives already runs single test files on every slice.
  - What still does work here is the gate before committing and "the full suite once". Keep the typecheck in that gate: test runners that transpile without type checking don't catch type errors.
- Confidence: Medium
- Reach: user-invoked, interactive.
- Action (rewrite): "Before committing, typecheck and run the full test suite (once, at the end)."

**F6. Every fact lookup delegated to a sub-agent**
- Location: `grilling/SKILL.md:26`
- Evidence: "When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself."
- Pattern: 1a "Default to [tool]", applied to delegation
- Why obsolete:
  - The Opus 5 notes document that it "reaches for [subagents] freely, which multiplies cost and latency". They list "a few file reads ... a simple search task" as work not to delegate (model-migration.md:1085, :1095), and Opus 5.5 starts from those patterns.
  - The line's real reason, not blocking the interview on a slow lookup, holds only for long explorations.
- Confidence: Medium
- Reach: model-invoked. grilling also runs inside grill-me, grill-with-docs, triage, wayfinder and improve-codebase-architecture, in Tom's interactive sessions.
- Action (rewrite): "Finding _facts_ is your job, never the user's: look up anything in the environment (filesystem, tools, etc.) yourself instead of asking. Do a quick lookup inline; hand a longer exploration to a sub-agent so it doesn't block: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for its report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait."

**F7. A length booster on the user-story list**
- Location: `to-spec/SKILL.md:33`, `:41`
- Evidence: "A LONG, numbered list of user stories." / "This list of user stories should be extremely extensive and cover all aspects of the feature."
- Pattern: 1a pressure language (caps plus an intensifier), written against models that produced too little
- Why obsolete:
  - Opus 5 already writes longer deliverables to disk than earlier models. The documented calibration is "cover the substance, but do not pad documents with filler sections, redundant summaries, or boilerplate" (model-migration.md:1071-1073), and Opus 5.5 starts from Opus 5's patterns.
  - Sonnet 5 calibrates length to the complexity of the task (:1254).
  - The part that does the work is the coverage requirement. The volume words push toward near-duplicate stories.
- Confidence: Medium
- Reach: user-invoked, interactive.
- Action (rewrite): change :33 to "A numbered list of user stories that covers every aspect of the feature: each actor, each capability, and the edge cases the conversation surfaced. Each user story should be in the format of:" and delete :41.

**F8. Pinned context-size figures**
- Location: `ask-matt/SKILL.md:32`, `ask-matt/PHASE-BOUNDARIES.md:21`, `wayfinder/SKILL.md:57`
- Evidence: "the window (~150k tokens on state-of-the-art models) within which the model still reasons sharply" / "enough smart zone left (~150k tokens)" / "sized to one 100K token agent session"
- Pattern: Group 2 volatile specifics, with the same fact duplicated across files
- Why obsolete:
  - "On state-of-the-art models" ties an undated figure to one model generation.
  - The target models have a 1M-token window (model-migration.md:1864), and Fable 5.1's documented gains include long-context retrieval deep in that window (:1750).
  - I can't tell where the smart zone sits on these models. The finding is that the figure is undated and appears three times as two different numbers, so it will drift.
  - The figure drives compaction, which the skill itself calls lossy, and ticket sizing. to-tickets:33 already states the same constraint without a number ("sized to fit in a single fresh context window").
- Confidence: Medium
- Reach: user-invoked, interactive.
- Action (rewrite):
  - ask-matt:32: "the part of the window within which the model still reasons sharply."
  - PHASE-BOUNDARIES:21: "or you have enough [smart zone](…) left for the next phase to fit."
  - wayfinder:57: "sized to fit one fresh agent session:".
  - Keep any figure in one place, the linked dictionary entry, with a date.

**F9. A banned-phrase list in the report style guide**
- Location: `improve-codebase-architecture/HTML-REPORT.md:123`
- Evidence: "No hedging, no throat-clearing, no "it's worth noting that…"."
- Pattern: 1e, a style prohibition with no stated provenance (a list of tics)
- Why obsolete:
  - It names the tics of an older model. Opus 5.5's documented gain in writing is "less jargon and fewer stock phrases" (model-migration.md:2034).
  - Naming the phrase can pull the model toward it (1c, prohibition lists).
- Confidence: Medium
- Reach: user-invoked, interactive.
- Action (rewrite): make the first sentence "Say each point directly, without qualifiers or preamble." and keep the rest of the line.

**F10. "If in doubt" routing to grilling**
- Location: `wayfinder/SKILL.md:124`
- Evidence: "If in doubt, call the Skill tool twice, for "grilling" and "domain-modeling"."
- Pattern: 1a "If in doubt, use [tool]"
- Why obsolete: current models are highly responsive to this phrasing and over-apply it. "If in doubt" becomes the usual route, pulling a grilling interview (which needs the human) into tickets the skill types as agent-only (research at :77, task at :80).
- Confidence: Medium, with low impact
- Reach: user-invoked, interactive.
- Action (rewrite): "For a grilling ticket, or a decision only the human can make, call the Skill tool twice, for "grilling" and "domain-modeling"."

**F11. A hedge on the skill's stated goal**
- Location: `teach/SKILL.md:41`
- Evidence: "... storage strength is the real goal. Try to design lessons which build long-term retention by desirable difficulty:"
- Pattern: 1a, a hedge attached to a requirement
- Why obsolete: the same sentence calls retention "the real goal". Current models read "try to" literally, as permission to fall short, and Sonnet 5 interprets prompts literally (model-migration.md:1264).
- Confidence: Medium, with low impact
- Reach: user-invoked; Ivy doesn't use it.
- Action (rewrite): "Design lessons for long-term retention through desirable difficulty:"

### Low (flag, no edit proposed)

**F12. An unconditional background agent in /research**
- Location: `research/SKILL.md:6` (see also :3 and :12)
- Evidence: "Spin up a **background agent** to do the research, so you keep working while it reads."
- Pattern: 1a default-to-tool, applied to delegation
- Why flagged:
  - When a user asks for research, the background agent is the point of the skill.
  - The concern is model-invoked use. The description also triggers on "docs or API facts gathered", which turns a small lookup into a spawned agent plus a new file in the repo. The Opus 5 delegation note advises against that.
  - Callers that already run /research inside a sub-agent (wayfinder:77, :115) would spawn a second agent, or can't comply, depending on the harness.
- Confidence: Low
- Suggestion: "If you are already running as a sub-agent, do the research yourself." Ivy side: G5.

**F13. A caps prohibition beside a required check**
- Location: `to-spec/SKILL.md:7`, `:17`
- Evidence: "Do NOT interview the user; just synthesize what you already know." / "Check with the user that these seams match their expectations."
- Why flagged: a caps prohibition, whose reason lives in the description rather than beside it, sits next to a step that asks the user something. A literal reader has to reconcile the two.
- Confidence: Low
- Suggestion: "Synthesize from what you already know; the one thing to check with the user is the seam list in step 2."

**F14. The glossary format file is orphaned and disagrees with the skill**
- Location: `teach/GLOSSARY-FORMAT.md:3`; `teach/SKILL.md:12-20`, `:15`, `:134-136`; `teach/LEARNING-RECORD-FORMAT.md:41`
- Evidence:
  - GLOSSARY-FORMAT.md defines "`GLOSSARY.md` is the canonical language for this teaching workspace".
  - SKILL.md never links that file, and it places glossaries among the `./reference/*.html` documents.
  - LEARNING-RECORD-FORMAT.md cites `[[GLOSSARY.md]]`.
- Pattern: Group 2, duplicated information that has drifted apart. The keep list's exception for working redundancy doesn't apply, because the two places disagree.
- Why flagged: this isn't tied to a model generation. A literal model reconciling the two will pick one.
- Confidence: Low
- Suggestion: list GLOSSARY.md in SKILL.md's workspace list with a link to GLOSSARY-FORMAT.md, and say whether the HTML reference glossary is a rendering of it.

### Outside the four groups: interactive waits in runs where nobody can answer

These aren't dated prompting. They are text that assumes a person will answer, in skills Ivy runs where nobody can. Following the guide, they are flags; the Ivy-side fixes are G1 and G2.

**F15. tdd requires seams to be confirmed with the user**
- Location: `tdd/SKILL.md:22`, `:24`
- Evidence: "Before writing any test, write down the seams under test and confirm them with the user. No test is written at an unconfirmed seam." / "Ask: "What's the public interface, and which seams should we test?""
- Why it matters on the target models:
  - Sonnet 5 "interprets prompts literally ... does not infer requests that weren't made" (model-migration.md:1264).
  - Under `claude -p`, a question ends the run. A literal reading of "no test at an unconfirmed seam" means no tests.
  - Build workers run this skill headless.
- Confidence: Medium on the mechanism. Not observed: no build contract has named seams, and a killed `claude -p` run leaves no transcript.
- Ivy: the runner (new on this branch) covers the question itself. Its prompt now opens: "The run is unattended: nobody can answer questions, so make routine judgment calls yourself" (`scripts/dispatch-runner.py:248-252`). What remains is G2.
- Action (flag). Upstream suggestion, matching the escape hatch the repo already uses at diagnosing-bugs:98 and prototype:17: "If the user isn't reachable, take the seams from the spec or ticket, or else the highest public interface the change touches, and list them at the top of your report."

**F16. code-review asks for the fixed point and the spec, or sends the user to setup**
- Location: `code-review/SKILL.md:13`, `:19`, `:32`
- Evidence: "If `docs/agents/issue-tracker.md` is missing, tell the user to run `/setup-matt-pocock-skills`." / "If they didn't specify one, ask for it." / "If nothing is found, ask the user where the spec is."
- Why it matters:
  - Workers run in clones of other repositories, which have no `docs/agents/`.
  - A review contract names a PR but not a fixed point.
  - The same literal-reading mechanism as F15 applies.
- Confidence: Medium on the mechanism
- Ivy: covered in the runner (new on this branch) by the same unattended line and by "the Task above is the spec axis" (runner:260-261).
- Action (flag). Upstream suggestion: "If the user isn't reachable: the fixed point is the merge-base with the default branch (for a PR, its base); with no spec found, skip the Spec axis and say so; a missing tracker config doesn't block a review."

## Ivy adapter gaps

Sessions and routines in the ivy repo take their adapters from `docs/agents/*.md`, `CONTEXT.md` and the playbook. Workers run in other repositories and never see those files. Their adapter is `build_prompt` in `scripts/dispatch-runner.py:247-277`. The runner test checks that prompt by substring (`dispatch-runner-test.py:194-205`): "every finding", "severity", "confidence", "Definition of done", "unattended" and the report markers must be present, and "failsafe" must be absent. The additions below keep all of those checks passing.

**G1. code-review's word-capped briefs still reach review workers' sub-agents** (medium; partly covered; see F1)
- Skill assumes: the orchestrator pastes briefs ending "Under 400 words." into its two sub-agents (code-review/SKILL.md:60-70).
- Ivy:
  - The review tail (new on this branch) sets a concrete bar: "report every finding that could cause incorrect behaviour, a failing test, a security or data problem, or a claim the code does not back, each with a severity and your confidence; leave out pure style preferences" (runner:254-256). That is the single-pass form the review guidance recommends (model-migration.md:1276).
  - The bar sits in the orchestrator's prompt, while the skill still gives its sub-agents the capped brief, and a literal orchestrator passes it on unchanged.
  - The bar's "leave out pure style preferences" and the skill's smell baseline (Mysterious Name is a naming smell) also pull in different directions. The runner's bar should win.
- Fix, in the runner's review tail, extending the Skills sentence (runner:260-261): "Skills: if a `code-review` skill is installed in this harness, drive the review with it (the Task above is the spec axis), and give its sub-agents the bar above in place of the word limit in its briefs; otherwise review without it."

**G2. Build contracts don't name the seams /tdd needs** (medium; partly covered; see F15)
- Skill assumes: seams are agreed before any test is written, and "No test is written at an unconfirmed seam" (tdd/SKILL.md:22).
- Ivy:
  - The runner covers the question itself (runner:248-252) and says "build test-first at the seams the Task names" (:271-272).
  - The build-contract convention (docs/agents/issue-tracker.md:28-32) doesn't ask a Task to name seams, and none of the six build contracts so far has (all six are tomgreen.ai site work).
  - "The seams the Task names" is therefore usually an empty set, and the literal default is no tests.
- Fix in `docs/agents/issue-tracker.md`, a new Conventions bullet after :28-32: "A build contract that changes behaviour names its seams in `## Task`: the public interfaces the tests go through. Those are the pre-agreed seams `/tdd` asks for, since the worker has no one to confirm them with." If the scout ever emits build contracts, the same sentence belongs with the format it follows (dispatch/DESIGN.md §2).
- Fix in the runner's build tail, after "at the seams the Task names" (:272): "(if it names none, choose them yourself and list them in your summary)".

**G3. The retro inherits writing-for-agents' stronger-word advice** (medium; partly covered; see F3)
- Ivy:
  - The retro is told to "Call the Skill tool with `writing-for-agents` and apply its tests: delete no-ops ..." (playbook.md:380-384). The list doesn't mention strengthening words, but "apply its tests" brings in the whole skill, including line 81.
  - The new prompt-audit clause (:386-390) runs only after a model change.
- Fix in playbook.md, "Tunable: retro", after "...push reference that only some runs need behind a pointer." (:384): "Where a word is too weak to change behaviour, delete it; if the behaviour it aimed at still matters, state the target or its completion criterion rather than a stronger word."

**G4. Ivy's CONTEXT.md departs from domain-modeling's format, and nothing says whether that is intended** (medium; not covered)
- Skill assumes:
  - CONTEXT.md is "totally devoid of implementation details ... a glossary and nothing else" (domain-modeling/SKILL.md:64).
  - Definitions are "One or two sentences max" (CONTEXT-FORMAT.md:28).
  - The template has only `## Language`.
- Ivy:
  - CONTEXT.md also keeps `## Relationships` (:223) and `## Flagged ambiguities` (:234).
  - Several definitions name the file they refer to and run past two sentences: Runner (:169, `scripts/dispatch-runner.py`), Runner status (:174) and Report (:208).
  - The retro loads domain-modeling every week, headless, and edits this file (playbook.md:395-399). docs/agents/domain.md doesn't say these departures are deliberate, so a literal retro may normalise them.
- Fix, if they are deliberate, in `docs/agents/domain.md` under "Before exploring, read these" (after :19): "Ivy's `CONTEXT.md` keeps two sections beyond `/domain-modeling`'s format, `## Relationships` and `## Flagged ambiguities`; a resolved ambiguity is recorded in the latter. A definition may name the file, script, or config key the term refers to (Runner, Runner status, Report): that is the term's referent, not an implementation detail." If they aren't deliberate, say so instead, and the retro will trim them.

**G5. No location for /research output** (medium; partly covered; see F12)
- Skill assumes: "Save it where the repo already keeps such notes; match the existing convention" (research/SKILL.md:12).
- Ivy:
  - Its convention for cited notes is `memory/`, which only the failsafe and the retro may write (playbook.md:71, Immutable).
  - Ladder routines put what they learn in the journal (playbook.md:171-175). That covers routines, but not a session in the ivy repo, which is where /research, a model-invoked skill, will most often run.
- Fix in `docs/agents/domain.md`, a new section: "## Research notes: `/research` writes to `.scratch/research/<slug>.md`, cited, and never to `memory/`: memory is written only by the failsafe and the retro, which may cite the note. In a routine, the finding goes in the journal entry instead."

**G6. The rule that routines run unattended doesn't reach the retro** (low; partly covered)
- Skill assumes: domain-modeling, which the retro loads, is interactive: "call it out immediately ... Which is it?" (:46), "force the user to be precise" (:54), "Offer ADRs sparingly" (:66-74).
- Ivy:
  - The unattended rule, new on this branch ("nobody can answer a question mid-run. Make the routine judgment calls yourself", playbook.md:123-128) sits in the ladder section.
  - The retro prompt points only to "Tunable: retro" and the Immutable sections (routines/retro.md).
  - The retro section's own wording ("resolve", "record in `docs/adr/`", :395-399) covers the two main questions the skill would ask, but not the general case.
- Fix in playbook.md, the first paragraph of "Tunable: retro" (after :347): "Like the ladder, the retro runs unattended: where a skill it loads asks the user something, decide, and say what you decided in `CHANGELOG.md`."

**G7. /to-spec's ready-for-agent label on a spec** (low; partly covered)
- Skill: "publish it to the project issue tracker. Apply the `ready-for-agent` triage label" (to-spec/SKILL.md:19).
- Ivy: specs go to `.scratch/<feature-slug>/spec.md` (issue-tracker.md:41-42), but ready-for-agent maps to a contract with `state: open` (triage-labels.md:12). A literal reading could publish the spec as a contract.
- Fix: issue-tracker.md:41-42 becomes "A spec from `/to-spec`: `.scratch/<feature-slug>/spec.md`, with no status line. A spec is not executable, so `/to-spec`'s `ready-for-agent` doesn't apply to it; only the contracts `/to-tickets` publishes from it open. Those contracts cite the spec path in `## Task`."

**G8. code-review inside the ivy repo: where the standards and the issue references are** (low; partly covered)
- Skill: standards come from files "such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`" (:36), and the spec from "Issue references in the commit messages (`#123`, `Closes #45` ...)" (:29).
- Ivy:
  - The repo has neither file. Its rules live in the playbook's Immutable sections, dispatch/DESIGN.md §2 and docs/agents/.
  - Its commits cite contract ids (`dispatch: open <id>`), and worker branches are `dispatch/<id>`. issue-tracker.md:47-50 says how to fetch a contract but not how to recognise a reference to one.
  - This applies to sessions in ivy and to review workers on ivy PRs (three on 2026-09-06).
- Fix: append to issue-tracker.md, "When a skill says 'fetch the relevant ticket'": "An issue reference here is a contract id (`YYYY-MM-DD-<slug>-<kind>-NN`) in a commit message or a `dispatch/<id>` branch name. For `/code-review`'s Standards axis, this repository's standards are the Immutable sections of `playbook.md`, the contract format in `dispatch/DESIGN.md` §2, and the conventions in `docs/agents/`; `scripts/dispatch-lint.sh` and `scripts/memory-lint.sh` enforce part of them, so skip what they check."

**G9. "sub-agent" in the skills collides with Ivy's glossary** (low; not covered)
- Skills: "sub-agent" means a helper context inside one session (code-review:11, grilling:26, DESIGN-IT-TWICE:21).
- Ivy: CONTEXT.md:184 lists `sub-agent` under Worker's _Avoid_. A journal that correctly says a session used a sub-agent could be "corrected" to "worker" by the retro's glossary pass.
- Fix: CONTEXT.md:184 becomes "_Avoid_: agent, sub-agent (in the skills, a sub-agent is a helper inside one session, never a worker)".

**Already covered** (no change needed):
- Questions that workers can't get answered (code-review's fixed point, spec and setup check; tdd's confirmation): covered by the unattended opening and "the Task above is the spec axis" (runner:248-252, :260-261, new on this branch). The residue is G1 and G2.
- Questions and human-only steps in the ladder routines (diagnosing-bugs, wizard or grilling, if a routine loads one): covered by playbook.md:123-128 (new on this branch). A step only Tom can take goes to the journal and under `## Blockers` (triage-labels.md:13).
- /to-tickets tickets become contracts with `blocked_by` (issue-tracker.md:36-40).
- Triage roles: triage-labels.md. /triage and PRs as a request surface are off (issue-tracker.md:68-71).
- Wayfinder's map and tickets: issue-tracker.md:52-66.
- ADR location, numbering and historical decisions: domain.md:5-19.
- domain-modeling's "offer an ADR" and "Which is it?" in the retro, which the playbook turns into "resolve" and "record" (playbook.md:395-399).
- The `## Agent skills` block: CLAUDE.md.
- Before this branch, config.yml's lane `effort` was never passed to the CLI. The runner on this branch passes it (runner:227-241).

**Workflow observation** (no change proposed):
- Build workers are asked to "review the diff against the Task before opening the PR" (runner:271-273). That is the self-review shape in F4. It now runs on claude-opus-5-5, where the Opus 5 over-verification note carries over as something to re-test. Ivy already verifies externally (dispatch/DESIGN.md D5) and runs cross-family review contracts.
- Both Claude build runs to date used their whole budget:
  - `2026-09-02-tomgreenai-copy-02` opened its draft PR at minute 19 and was killed at 40.
  - `2026-09-02-tomgreenai-layout-02` was killed at 45.
- `claude -p` prints only its final message, so a killed run leaves no output tail (runner:413 keeps the last 1,500 characters of stdout). What those workers did after opening the PR is unrecorded. A question would have ended the run early, so these were not stalls waiting on an answer.
- The skill's two-axis report shape appears in 1 of 22 reports (a Codex run on an ivy PR). The three claude-opus-5 reports follow the contract Task's format. Whether workers load the skills at all isn't recorded anywhere.
- Before deciding whether the review inside the worker is worth its minutes, the prerequisite is capturing worker transcripts.

## Clean skills

These had no finding in the four pattern groups:

- codebase-design (with DEEPENING and DESIGN-IT-TWICE)
- domain-modeling (with ADR-FORMAT and CONTEXT-FORMAT); Ivy gap G4 only
- grill-me
- grill-with-docs
- handoff
- prototype (with LOGIC and UI)
- resolving-merge-conflicts
- setup-matt-pocock-skills (with its 5 templates)
- tdd (with tests and mocking); the out-of-group flag F15 only
- to-questionnaire
- to-tickets
- triage (with AGENT-BRIEF and OUT-OF-SCOPE)
- wait-what
- wizard

Considered and kept, with the keep-list reason, so these aren't raised again:
- grilling:6 "relentlessly": names the behaviour the user asked for, and :28 gives it a stop condition.
- Single, scoped caps or bold that carries a real constraint or a reason: to-tickets:31 and :67, to-spec:55, improve-codebase-architecture:60, triage:13 "must" (a disclosure policy), resolving-merge-conflicts:10 "never --abort".
- code-review:23: a cheap check that fails fast on a bad ref, with its reason. It is not self-verification.
- code-review:41 and :64, "Skip anything tooling enforces": a concrete bar, which is the form the review guidance recommends. It is not a severity filter.
- Sub-agents for independent or wide work (code-review:11, DESIGN-IT-TWICE:21, improve-codebase-architecture:27, wayfinder:115): the case the delegation notes endorse.
- diagnosing-bugs' ordered phases and the bold stop at :66: a method whose order has reasons. :98 already lets the run proceed when the user is away.
- Runs of prohibitions that each carry a reason (prototype/LOGIC.md:62-67, triage/AGENT-BRIEF.md:15-17), and deliberate recaps at the end of a file.
- Format specs for output where format matters: HTML-REPORT.md:50-52 ("one sentence", "≤6 words"), CONTEXT-FORMAT.md:28, GLOSSARY-FORMAT.md:31, and grilling's round template.
- HTML-REPORT's prescribed look (bg-stone-50, serif headings, monospace and uppercase-tracked labels, badges) resembles the defaults the Opus 5.5 notes list. But it is explicit design direction, which is the form those notes recommend, so it's a matter of taste rather than a finding.
- Sections of general knowledge that state the author's quality bar: codebase-design:67-95 and tdd/mocking.md.
- Tool-contract detail in the setup templates (gh and glab commands, GitHub's issue-dependency endpoint), kept under keep-list item 4. I didn't check it against the live APIs, because Ivy doesn't use those templates.
- The CDN pins in HTML-REPORT.md:13 and :15: library versions, not text dated by model generation. Not checked.
- Hedges that state genuine conditions: implement:9 "where possible", resolving-merge-conflicts:10, and teach:55, :108 and :110.

## Testing the top changes (Step 7)

Each removal is a hypothesis. Small probes to run before sending them upstream:
- F1 and G1: run the Standards brief on a diff seeded with about 15 known violations and smells, with and without the cap, and compare how many are reported against how many were seeded.
- F3, G3 and G6: the routine eval (`evals/README.md`) is the regression check the playbook already names for changes on the retro side.
- F15 and G2: queue one build contract that names its seams and one that doesn't. Check whether tests were written and how long the run took. This needs the worker transcripts described above.
- F4 and F5: run /implement on one small ticket with and without those lines. Compare wall time, the number of verification runs, and whether the review pass changed the commit.
