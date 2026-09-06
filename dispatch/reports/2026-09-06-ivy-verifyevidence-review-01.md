# Report — 2026-09-06-ivy-verifyevidence-review-01

Produced by the frontier/openai lane, 7.2 wall-minutes.

# PR #18 adversarial instruction review

Reviewed head `de084f15bece5393630dc6cf57191043a684c379`.

## Findings

### [P1] Receipt authority is broader than Immutable policy permits

`playbook.md:101-104` says only the failsafe’s external check can establish verified-done. However, `procedures/verify-contract.md:27-40` permits a generic “independent verifier,” while `scripts/verification.py:52-57` accepts any non-empty `verifier`. A receipt created by another routine could therefore unlock dependencies despite never being checked by the failsafe.

**Proposed fix:** State explicitly that only the failsafe may author verification receipts and stamps, and make non-failsafe provenance evaluate as unverified. If broader verifier authority is intended, it requires an explicit human change to the Immutable rule.

### [P1] Mutable procedures acquire authority that Immutable policy reserves to the playbook

`playbook.md:3-5` authorizes the retro to edit Tunable sections, and `playbook.md:62-63` says behavior lives in the playbook. `procedures/retro.md:15-18` instead authorizes the retro to edit linked routine procedures, which now contain most operational behavior. A mutable procedure is effectively expanding its own editing authority.

**Proposed fix:** Keep autonomous tuning limited to `playbook.md` and `config.yml`, with procedure changes requiring human authorization, or separately amend the Immutable policy by a human commit to delegate explicitly labeled Tunable procedure sections.

### [P1] One receipt revision cannot represent the multi-repository evidence required by review contracts

`procedures/verify-contract.md:21-34` assigns one receipt-wide revision and requires every check to use it; `scripts/verification.py:31-39` enforces equality. A review contract commonly verifies a report committed in Ivy and paths or behavior at a different PR-head SHA. Those are distinct immutable revisions, so the schema forces either inaccurate revision labeling or incomplete verification.

**Proposed fix:** Bind each check to its own repository/artifact revision, while separately binding the completed output artifact. Alternatively, define and persist a manifest containing every source revision and use its digest as the receipt revision.

### [P2] Scout can miss the cloud-access instructions it needs

`procedures/scout.md:12` instructs the cloud routine to use `gh api`, but `procedures/cloud-verification.md:5-14` records that `gh` is unavailable there and GitHub MCP tools must be used. The conditional routing at `playbook.md:127-129` names contribution checks and schedule changes, not watchlist synchronization or candidate discovery, so the scout has no unambiguous reason to load that reference.

**Proposed fix:** Link `procedures/cloud-verification.md` directly from `procedures/scout.md` before its first GitHub operation, or broaden the playbook condition to all cloud GitHub access.

### [P2] Operational behavior remains unverified

`evals/agents.json:14-59` marks every Ivy routine baseline as `not-run`, and `docs/housekeeping/rollout.md:49-52` confirms that only deterministic infrastructure checks ran. Those checks cannot establish that the newly scoped prompts still load and obey the required instructions.

**Proposed fix:** Before promotion, run the scout, check, failsafe, and retro cases against the exact PR-head instructions in the deployed harness, independently grade the captured outputs, and retain the revision-bound assessment artifacts.

### [P3] Routine schedule references point to a section no longer in the playbook

`routines/check.md:3-4`, `routines/failsafe.md:3-4`, `routines/retro.md:3-4`, and `routines/scout.md:3-4` direct readers to the DST note in `playbook.md`, but that note moved to `procedures/cloud-verification.md:29-32`.

**Proposed fix:** Update all four references to `procedures/cloud-verification.md`.

### [P3] Mutable entry-point text duplicates Immutable guardrails

`AGENTS.md:20-22` repeats the Immutable restrictions on worker main writes and routine changes from `playbook.md:93-117`. This creates a second wording that can drift while also saying permissions come only from the playbook.

**Proposed fix:** Replace the duplicated rules with a direct pointer stating that routine and dispatch authority is defined exclusively by the Immutable dispatch guardrails in `playbook.md`.

## Sound sections

- `playbook.md:9-119` is unchanged from the PR base; the PR does not directly edit an Immutable section.
- `procedures/verify-contract.md:6-19` clearly says checks must be declared before execution, worker completion messages are claims, every source must be inspected, missing access remains unverified, and observed violations fail.
- `scripts/verification.py:18-39` fails closed for empty requirements, missing checks, worker-labeled evidence, blank evidence, unknown statuses, and revision mismatches.
- `CLAUDE.md:1` correctly establishes `AGENTS.md` as the single shared Claude/Codex entry point.
- The routine-specific content removed from `playbook.md` is otherwise preserved in `procedures/scout.md`, `procedures/check.md`, `procedures/failsafe.md`, and `procedures/retro.md`.
