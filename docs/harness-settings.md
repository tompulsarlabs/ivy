# Dispatch settings and execution evidence

The runner now sends configured effort to native CLI arguments: Claude Code's
`--effort` and Codex's `-c model_reasoning_effort=…`. An explicit Claude effort
also replaces an inherited `CLAUDE_CODE_EFFORT_LEVEL` in the child environment;
the parent environment is unchanged. Model IDs and lane selection are unchanged.
The unsupported `effort: low` field is removed from Haiku 4.5's configuration.

Inspect current configuration without network, clones, locks or harness calls:

```sh
python3 -B scripts/dispatch-runner.py --preview-routes
python3 -B scripts/dispatch-runner.py --preview-routes --config /path/to/config.yml
```

This is distinct from the historical `--dry-run`, which syncs runner/project
clones. Preview validates local command construction, not account access, model
availability, effective provider settings, permissions or worker quality.
Unknown model/harness/effort combinations fail validation; live dispatch leaves
the task open with `invalid_harness_config`, before claiming it or preparing its
project clone. Other eligible contracts may proceed. New models require explicit
compatibility registration and evaluation; no Sol/Astra migration is included.

Completed and failed started attempts record requested model/effort, a bounded
CLI version probe, source revision and SHA-256 identities for the runner,
configuration and constructed prompt. No raw prompt, environment, auth or CLI
diagnostic output is added to those fields. Unknown version output stays unknown.
Effective model and effort remain **unknown**: flags, provider fallback, managed
caps and harness settings do not prove what the backend actually used.

`context_capture: runner_prompt_only` explicitly excludes auto-loaded repository
instructions, skills, hooks, tool configuration and other harness context.
`usage_capture: unavailable` is not a zero-use claim. Structured provider events,
full context identity, isolated auth and real-agent acceptance remain follow-up
work. Completion still means claimed done pending independent verification.

Validation uses `scripts/harness-settings-test.py`, the existing runner tests,
and `evals/harness-settings.json`. The fixed-worker integration case executes a
local program that checks its argv/environment and prints a fixture report. It
does not call a model or establish model quality. Existing permissions, task
budgets and provider selection are preserved.

## Rollout

Keep the PR draft until reviewed. On merge, the existing runner update mechanism
loads the synchronized script and config together on its next tick. Applying a
previously ignored effort setting can change consumption and output, so validate
one explicitly selected real task before promoting broader routing changes.
Retain the previous reviewed revision for rollback. Do not restore a setting
silently by claiming it is effective: absent settings are recorded as `unset`.

CLI help inspected locally: Claude Code 2.1.277; Codex CLI 0.155.1.
Compatibility sources checked 23 September 2026:

- [Claude Code model/effort configuration](https://code.claude.com/docs/en/model-config#adjust-effort-level)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)

Claude's documentation lists effort-capable models and excludes Haiku 4.5.
The checked source also requires Claude Code 2.1.280 for Opus 5.5; the current
2.1.277 installation is not used to claim that model is ready. No CLI upgrade or
model availability probe was performed.
