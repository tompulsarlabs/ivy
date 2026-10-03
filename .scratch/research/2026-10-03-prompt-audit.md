# Prompt audit: Ivy's own prompts, 2026-10-03

This audit covers the text Ivy sends to models:

- the four routine prompts and the files the routines read
- the dispatch worker prompt
- the routine eval's wrapper
- the agent configuration in this repository

It follows the `claude-api` skill's `prompt-audit`: Steps 0 to 7 and its keep list. It is read-only, so nothing outside this file and its patches was changed. Each finding that proposes an edit has its own patch in `2026-10-03-prompt-audit/`, and each patch applies on its own:

```bash
git apply .scratch/research/2026-10-03-prompt-audit/<file>.patch
```

## Assumptions

**Scope.** Everything in the working tree that reaches a model as text, with four exclusions:

- **`.claude/skills/`.** It is vendored from `mattpocock/skills`, pinned by `skills-lock.json`, and replaced by `npx skills update`. The 2026-09-23 audit (`2026-09-23-vendored-skills-audit.md`) covered it. Here I only checked whether that audit's open items still reach Ivy's own files (F5).
- **`evals/routines/live-prompts/*.txt`.** These are the eval's frozen baseline (`routines/*.md:21-22`), so they are listed but not edited.
- **Records.** Journals, contracts, reports, `state.json` and memory pages are data. I read them only to check a claim an instruction file makes.
- **User-level configuration.** `~/.claude/CLAUDE.md` is outside the repository and was not read. No settings files are tracked.

**Target models.** Each surface is audited against the model that reads it.

- **The routines.** This covers `playbook.md` and the files the routines load. Their model is the current Sonnet (`claude-sonnet-5`): the four live triggers run it (read 2026-10-03), and it is the default in `scripts/eval-routines.py:45`. A newer Sonnet exists. Moving to it is Tom's call (Immutable guardrail 5), and this audit should run again when it happens.
- **The dispatch worker prompt.** Both Anthropic lanes run the previous Opus (`claude-opus-5`) today. The newest Opus is the documented destination (`config.yml:68-71`), so the prompt is checked against both.
- **`CLAUDE.md`, `docs/agents/` and `procedures/`.** Interactive sessions and the routines both read these, so they are checked against both targets.

**Other providers.** `build_prompt` (`scripts/dispatch-runner.py:335`) also feeds the Codex harness (`gpt-5.6-sol` and `gpt-5.6-terra`; `config.yml:76`, `:79`). The reasons in this audit are documented for Claude models only. F4 changes the prompt the Codex lanes get as well.

**History.** The clone is shallow: 50 commits, with the boundary at `a562f9e` (2026-09-29). Blame can date anything older only to that boundary. `8dae9d3` (PR #21, 2026-10-02) is the latest change to the playbook, the routines and the runner.

## Summary

The three findings with the most impact:

1. **A session counts the daily cap over two directories, but the playbook and the lint count three.**
   - `docs/agents/issue-tracker.md:23-25` tells a session to check `dispatch/queue/` and `dispatch/done/` for today's count. `playbook.md:263-265` (PR #21) and `scripts/dispatch-lint.sh:118-125` also count `dispatch/failed/`.
   - Today shows the gap. Four contracts were created, and two of them are in `failed/`. A session following the tracker would count two and plan up to four more. The lint would refuse the commit only after those contracts were written.
2. **Build workers are told to review their own diff with `code-review` before opening the PR** (`scripts/dispatch-runner.py:360-363`).
   - Both Anthropic lanes run the previous Opus. Its behavior notes say to delete verification scaffolding, because it verifies its work unprompted. They also say review and verification don't belong in subagents, and `code-review` runs as subagents.
   - Ivy already reviews each build outside the worker: the failsafe checks it, and a cross-family review contract can cover its PR.
   - The line has been on `main` since 2026-10-02. No build contract has run with it yet.
3. **A recovery procedure lists a pending use that Ivy's own records contradict** (`procedures/recover-attribution.md:123-128`).
   - It says `ai-capability-app`'s last commit, from 2026-06-23, has `last_commit_email_ok: false`.
   - Today's scan shows the last commit as 2026-10-02, with `true`.
   - The memory page names a different commit as the uncounted one: `24cda31`, from 2026-06-19.

Findings per group:

| Group | High | Medium | Low |
|---|---|---|---|
| 1. Dated prompt text | | 1 (F4) | 2 flags (F6, F7) |
| 2. Brittle configuration files | 3 (F1, F2, F3) | 1 (F5) | |
| 3. Tool descriptions | not applicable: the repository defines no tools | | |
| 4. Request config and architecture | | 1 flag (F8) | 1 flag (F9) |

## Inventory

| Surface | Where | Read by |
|---|---|---|
| Routine prompts | The Prompt block of `routines/{scout,check,failsafe,retro}.md`; the four live triggers match it byte for byte (checked 2026-10-03) | the current Sonnet, through four cloud triggers |
| Files the routines read | `playbook.md`, `CLAUDE.md`, `CONTEXT.md`, `config.yml`, `procedures/`, `docs/agents/`, `dispatch/DESIGN.md`, `memory/INDEX.md` | the current Sonnet, and interactive sessions |
| Worker prompt | `build_prompt` (`scripts/dispatch-runner.py:335-367`); argv from `harness_argv` (`:249-272`) | the previous Opus (Anthropic lanes), Codex (OpenAI lanes), `claude-haiku-4-5` (fast-cheap lane) |
| Eval wrapper | `SCHEMAS` and `WRAPPER` (`scripts/eval-routines.py:52-108`); argv from `claude_argv` (`:353-369`) | the current Sonnet, inside the eval |
| Eval baseline | `evals/routines/live-prompts/*.txt` | frozen; not edited |
| Vendored skills | `.claude/skills/`, 25 skills | audited 2026-09-23; excluded here |

Workers run as `claude -p <prompt> --model <id> [--effort <level>]`. The eval adds `--restricted`, `--tools`, `--strict-mcp-config` and `--max-budget-usd`. Neither passes:

- sampling parameters
- a thinking budget
- a prefill
- a beta header

## Findings

### F1. The session rule for the daily cap leaves out `failed/` (High)

- **Location:** `docs/agents/issue-tracker.md:23-25`
- **Evidence:** "The daily cap (`config.yml` `dispatch.daily_cap`, counted by `created` date) applies to contracts published from a session too. Check `dispatch/queue/` and `dispatch/done/` for today's count first."
- **Pattern:** Group 2. Two instruction files contradict each other, and the older one has a stale fact.
- **Why it is stale:**
  - `playbook.md:263-265` counts "across `dispatch/queue/`, `done/`, and `failed/`, whoever wrote them". That line blames to `8dae9d3` (2026-10-02). The tracker line predates the clone's boundary.
  - `scripts/dispatch-lint.sh:118` reads all three directories, and its cap check (`:120-125`) refuses a commit past the cap.
  - Two of the four contracts created on 2026-10-03 are in `failed/`.
- **Action:** rewrite (`F1-daily-cap-count.patch`): "…counted by `created` date across `dispatch/queue/`, `done/`, and `failed/`) applies to contracts published from a session too. Count today's first."

### F2. The lanes example gives Haiku an effort setting, which the runner rejects (High)

- **Location:** `dispatch/DESIGN.md:130`
- **Evidence:** `anthropic: { harness: claude-code, model: claude-haiku-4-5, effort: low }`
- **Pattern:** Group 2. The example makes a config claim that the code contradicts.
- **Why it is stale:**
  - `HARNESS_MODELS` registers no effort levels for Haiku (`scripts/dispatch-runner.py:48`). `harness_argv` raises on any effort level that isn't registered (`:254-255`).
  - `scripts/harness-settings-test.py:55-59` tests exactly this case: `effort: low` on Haiku raises.
  - `config.yml:81` notes "model does not support effort", and the API documentation agrees that effort errors on Haiku 4.5.
  - §3 tells the retro that its model IDs "are config data … the retro updates them". A retro that copied this line into `config.yml` would leave the lane as `invalid_configuration`.
- **Action:** rewrite (`F2-haiku-effort.patch`). Drop `effort: low` and use `config.yml`'s comment instead.

### F3. A pending use listed in the recovery procedure is stale (High)

- **Location:** `procedures/recover-attribution.md:123-128`
- **Evidence:** "`ai-capability-app`'s last local commit (2026-06-23) carries `last_commit_email_ok: false` and stays uncountable until this runs [cite:2026-08-29]."
- **Pattern:** Group 2, a stale fact. It is also an observation inside a procedure, and `procedures/README.md:26` puts observations in `memory/`.
- **Why it is stale:**
  - `local-wip.json` (scan of 2026-10-03 06:45 UTC, commit `de6073a`) reports `sybil` → `tompulsarlabs/ai-capability-app` with `last_commit: 2026-10-02` and `last_commit_email_ok: true`.
  - `memory/repos/ai-capability-app.md:30-41` says the uncounted commit is `24cda31`, from 2026-06-19, not a 06-23 commit [cite:2026-09-01].
  - The scout already reads that memory page for every candidate repo (`playbook.md:210-215`).
- **Action:** remove the section (`F3-stale-pending-use.patch`). The memory page keeps the accurate record.

### F4. Build workers review their own diff before opening the PR (Medium)

- **Location:** `scripts/dispatch-runner.py:360-363`
- **Evidence:** "Skills: if `tdd` and `code-review` skills are installed in this harness, build test-first at the seams the Task names (…) and review the diff against the Task before opening the PR; otherwise proceed without them."
- **Pattern:** Group 1, verification scaffolding: telling the model to do something it already does unprompted (Step 3). It also hands that verification to subagents.
- **Why it is obsolete:**
  - The previous Opus's behavior notes say it "verifies its own work without being asked". Instructions to verify "now cause over-verification", and "removing them reduces over-verification with no capability regression".
  - The same notes list "Review, verification, or to double check your work" as work not to give to subagents. `code-review` runs both of its review axes as "parallel sub-agents" (`.claude/skills/code-review/SKILL.md:11`, `:64`, `:70`).
  - The newest Opus keeps those patterns as a starting point and asks for each to be re-tested.
- **Ivy already verifies outside the worker:**
  - The failsafe runs the contract's Verification section (Immutable guardrail 2).
  - A cross-family review contract can cover the build's draft PR, as for any open PR. For example, `talentradar-csvdedupe-build-01` (Anthropic) was reviewed by `talentradar-csvdedupe-review-01` (OpenAI pool) the next day (`memory/models.md`).
- **Provenance:** the line comes from `8dae9d3` (2026-10-02). No build contract has run since, so Ivy has no evidence either way. The 2026-09-23 audit recorded the line as a workflow observation and said worker transcripts were needed first (see F8).
- **Action:** remove the self-review and keep `tdd` (`F4-build-self-review.patch`). The new line reads: "Skills: if a `tdd` skill is installed in this harness, build test-first at the seams the Task names (if it names none, choose them yourself and list them in your summary); otherwise proceed without it."
- **Other files in the patch:**
  - the assertion in `scripts/dispatch-runner-test.py:175`, which required `code-review` in the build prompt
  - `dispatch/DESIGN.md:110-112`
  - `README.md:186-188`
  - `OVERVIEW.md:91-93`
- **Caveat:** the Codex lanes get the same prompt, and nothing used here documents GPT behavior. Taking this hunk changes those lanes on evidence about Claude only. Keeping the self-review for the OpenAI pool would require passing the harness into `build_prompt`.

### F5. Interactive sessions get `writing-for-agents`' stronger-word advice without the playbook's correction (Medium)

- **Location:** `CLAUDE.md:22-24`
- **Evidence:** `CLAUDE.md` says "`writing-for-agents` is the reference for editing this file, `playbook.md`, `routines/*.md`, and `procedures/`." The skill itself says a word "too weak to beat the default (_be thorough_ …) is a no-op, and the fix is a stronger word (_relentless_)" (`.claude/skills/writing-for-agents/SKILL.md:81`).
- **Pattern:** Group 2: two instruction files contradict each other. The harm it risks is Group 1a: pressure language.
- **Why it is a problem:**
  - `playbook.md:433-435` (`8dae9d3`, 2026-10-02) says the opposite: "delete it or state the target plainly instead of reaching for a stronger one: intensity words over-apply on current models". The audit guide documents the same behavior.
  - That correction sits in "Tunable: retro", which interactive sessions don't load. `CLAUDE.md` sends them straight to the skill, so a session editing `playbook.md` can put the pressure language back through a PR.
  - The 2026-09-23 audit's G3 closed this gap for the retro but not for interactive sessions.
  - The skill comes from upstream, so the override goes in `CLAUDE.md`, where Ivy's sessions read it, and names the rule it overrides.
- **Action:** rewrite (`F5-stronger-word-carveout.patch`): "…and `procedures/`; where it says to fix a weak word with a stronger one, delete the word or state the target plainly instead, since intensity words over-apply on current models."

## Flags (no edit proposed)

### F6. The eval asks for JSON in prose and parses it leniently (Low)

- **Location and evidence:** `scripts/eval-routines.py:106-107` says "reply with only a JSON object, no prose around it". `extract_json` (`:246-258`) takes the first JSON object it finds and tolerates a code fence.
- **Pattern:** 1b, JSON requested in prose where a structured-output feature exists. The installed CLI (2.1.288) has `--json-schema`, and its result carries `structured_output`.
- **Why only a flag:**
  - None of the documented harm shows up. All 391 stored eval rows have status `ok`, and none is `unparseable`.
  - There is no prefill, and the request goes through the CLI rather than the API.
  - Switching would change what the eval measures. The four `SCHEMAS` would become JSON Schema, and the baseline would need a re-run.
- **If Tom wants enum values enforced** (for example `day_state` and `channel`), this is the change to make.

### F7. The wrapper calls the run an "Evaluation dry run" (Low)

- **Location:** `scripts/eval-routines.py:98`.
- **Pattern:** 1c, grader vocabulary. Telling the model it is being evaluated can shift its effort toward being watched, and that gap between eval and production is what this eval exists to avoid. "Dry run" alone already explains why the copy is disconnected.
- **Why only a flag:** the evidence is the wording alone, and no effect has been measured. If it changes, re-run the baseline, since the wrapper is the same across variants.

### F8. Worker runs record no usage and no served model (Medium; instrumentation, outside the prompt diff)

- **Location:** `scripts/dispatch-runner.py:304`, `:310-311` record `effective_model: unknown`, `context_capture: runner_prompt_only` and `usage_capture: unavailable`.
- **How the runner reads output:** it reads plain stdout (`:493`). A failed run keeps only the last 12 lines of its final 1,500 characters (`:509-513`).
- **Pattern:** Group 4, no token accounting. Without per-run usage, nobody can measure F4 or any later change to the worker prompt.
- **The eval already does this.** It runs `--output-format stream-json --verbose` (`scripts/eval-routines.py:360-362`) and reads `modelUsage` from the result (`:479`). That records the model that actually served the run, and the eval flags `wrong_model` when it differs.
- **Recommendation:** use the same output path for the claude-code harness and record `num_turns`, usage and the served model under `outcome:`.
  - The report would then come from the result's final message instead of stdout markers.
  - A worker that times out would leave its transcript.
  - On flat-rate pools, wall-minutes stay the cost measure. This is for evidence, not spend.

### F9. Two rules that a script could check are left to the model (Low)

- **Pattern:** Group 4, a model executing a deterministic step, and 1d, rules no code checks. The two rules:
  - **`state.json` is append-only.** `playbook.md:86-92` (Immutable) says keys are never renamed or removed, because `tomgreen.ai` reads the file. No script checks it: `state.json` appears only in the eval scripts.
  - **Stale claims and expired contracts.** `playbook.md:346-351` has the failsafe reopen stale claims and expire old contracts. Both depend only on frontmatter timestamps. The runner already skips expired contracts in code (`scripts/dispatch-runner.py:423`).
- **Why only a flag:** I saw no violation in the records I read.
- **Possible check:** a script beside `memory-lint.sh` that compares `state.json`'s keys with the previous commit's would enforce the Immutable rule. The daily cap is the model for this: the playbook states it and `dispatch-lint.sh` enforces it. The first rule is Immutable, so the decision is Tom's.

## Considered and kept

Listed so they aren't raised again.

**Routine prompts and the playbook**

- **All four routine prompts.** Each is short and opens with context. Each carries one emphasis that gives its reason ("Attribution matters most tonight"), and each ends with a one-line format for a person reading a notification. They match the live triggers.
- **Lines about older data in the playbook.** These are `playbook.md:191-192` ("Many existing rows are paragraphs; write new ones in the short form"), `:281-282` (earlier journals "predate these rules") and `:371-374` (dated restatements "written before these rules").
  - They look like wording written against an earlier version.
  - Each one describes data the run will find in the repository and stops the model from copying it. They are kept.
- **The Immutable verification section.** It defines green by `check.sh` (`:30`), and the Tunable cloud path (`:144-174`) covers how to decide when the script can't run ("exits 2 in the cloud … never grounds to guess"). "Alert loudly" (`:33`) is made concrete at `:184-185`. The eval cases `failsafe-verify-alert` and `check-no-signal` cover both.

**The worker prompt**

- **The review bar** (`dispatch-runner.py:342-350`). It asks for every finding with a severity and a confidence, leaves out pure style, and replaces `code-review`'s word limit for its subagents (2026-09-23, F1 and G1). This is the concrete bar the review guidance recommends.
- **Unattended and scope wording.** The opening says nobody can answer questions, and the build Task line ("deliver what the Task asks, at the scope it intends …") is the previous Opus's scope instruction. The newest Opus keeps these as a starting point to re-test.
- **Fixed-format output.** The report markers and "nothing after END_REPORT" are the format the runner parses (keep-list 7).
- **Guardrails.** "The default branch is Tom's: never push to it" and the git-identity clause are real guardrails, and both give their reasons.

**Other files**

- **`procedures/recover-attribution.md` Steps 0-5.** This is a history rewrite with exact commands, including "MUST show the noreply address" in a command comment. It is a fragile operation, so the exact script stays (keep-list 3).
- **Lane settings for the newest Opus.** `config.yml:68-71` already plans workhorse at `medium`, and frontier at `high` until `xhigh` shows a measured gain. That matches the model's documented `medium` default and its advice to keep `xhigh` and `max` for measured gains. The remaining step, registering the model in `HARNESS_MODELS`, is written there too.
- **The eval's `evidence`, `why_free` and `steps` fields.** These ask for decisions and short explanations, not for the model's reasoning.

## Verification (Step 7)

**Done for this audit:**

- Each patch applies on its own to `70320df` (`git apply --check`), and all five apply together.
- With all five applied, the test suites pass:
  - `dispatch-runner-test.py`: ok
  - `harness-settings-test.py`: 19 tests ok
  - `dispatch-lint.sh`: ok
- The new F4 assertion fails on the current prompt and passes on the patched one.
- **`eval-routines-test.py` could not run here.** The shallow clone lacks `2aa1829`, the baseline commit it archives, and it fails the same way on unmodified `main`.
- **No routine eval was run.** It needs Claude Code on the Mac with the subscription login, and every run costs money.

**Before merging:**

- **F5.** It changes `CLAUDE.md`, which every routine loads. Run the routine eval (`evals/README.md`) with `--steering WORKTREE` against `main`.
- **F1.** The `scout-daily-cap` case has contracts in `queue/` only. A case built from 2026-10-03, with two of four contracts in `failed/`, would test the playbook rule that the tracker now matches.
- **F4.** Compare the next two build contracts on the Anthropic lanes, ideally after F8 is in place: wall-minutes, turns, and what the PR's review contract finds.
  - If the review contract starts finding what the self-review used to catch, restore the line in its shortest form.
- **F2 and F3.** These are documentation and fact fixes. Re-read `config.yml:81` and the memory page.

**Run this audit again** when Tom moves the routines to a newer Sonnet or the lanes move to the newest Opus, as `playbook.md:436-440` already asks.
