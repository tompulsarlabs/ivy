# Report — 2026-10-01-ivy-effortisolation-review-01

Produced by the workhorse/openai lane, 1.5 wall-minutes.

# Review — PR #24

**Head reviewed:** `fbfb4ca5f33196922e78a3396e958751ee20a3d5`  
**Verdict:** request changes

## Finding

### F1 — Medium: unreadable/missing configuration reports `lint_failed`, not the documented `config_invalid`

Live dispatch runs `dispatch-lint.sh` before `load_config()` ([scripts/dispatch-runner.py:398](scripts/dispatch-runner.py:398), [scripts/dispatch-runner.py:404](scripts/dispatch-runner.py:404)). A missing or unreadable `config.yml` makes the linter’s lane/cap extraction empty and exits nonzero ([scripts/dispatch-lint.sh:20](scripts/dispatch-lint.sh:20), [scripts/dispatch-lint.sh:24](scripts/dispatch-lint.sh:24), [scripts/dispatch-lint.sh:128](scripts/dispatch-lint.sh:128)). The runner therefore publishes `lint_failed`, rather than reaching the new `config_invalid` handler ([scripts/dispatch-runner.py:399](scripts/dispatch-runner.py:399), [scripts/dispatch-runner.py:401](scripts/dispatch-runner.py:401), [scripts/dispatch-runner.py:406](scripts/dispatch-runner.py:406)).

This remains fail-safe (`lint_ok: false`) and no contract is claimed, but contradicts the documented guarantee for missing/unreadable configuration ([docs/harness-settings.md:34](docs/harness-settings.md:34), [docs/harness-settings.md:35](docs/harness-settings.md:35)). HS23 masks the ordering by stubbing every `run()` call successful, including the real linter ([scripts/harness-settings-test.py:285](scripts/harness-settings-test.py:285), [scripts/harness-settings-test.py:299](scripts/harness-settings-test.py:299)). Add an integration-level missing/unreadable-config case or route this failure through the intended preflight status.

## Confirmed

- An unset Claude lane cannot inherit `CLAUDE_CODE_EFFORT_LEVEL`: the child environment removes it before optionally setting explicit effort ([scripts/dispatch-runner.py:278](scripts/dispatch-runner.py:278)-[scripts/dispatch-runner.py:285](scripts/dispatch-runner.py:285)); HS20 covers Haiku and unset Opus against an ambient `max` value ([scripts/harness-settings-test.py:93](scripts/harness-settings-test.py:93)-[scripts/harness-settings-test.py:100](scripts/harness-settings-test.py:100)). This fails on base `1305117`, which retained the variable for unset lanes.

- A malformed routing entry reaches the new failed preflight path before queue iteration and publishes `config_invalid`/`lint_ok: false` ([scripts/dispatch-runner.py:404](scripts/dispatch-runner.py:412)); HS21 is red on base because base accepted the empty effort and emitted a healthy result ([scripts/harness-settings-test.py:249](scripts/harness-settings-test.py:249)-[scripts/harness-settings-test.py:268](scripts/harness-settings-test.py:268)).

- Provenance `RuntimeError` and `OSError` leave the affected contract open, record `provenance_unavailable`, and continue the loop ([scripts/dispatch-runner.py:462](scripts/dispatch-runner.py:467)). HS22 supplies both errors, verifies the first contract byte-for-byte unchanged, and verifies dispatch of the next contract ([scripts/harness-settings-test.py:301](scripts/harness-settings-test.py:301)-[scripts/harness-settings-test.py:337](scripts/harness-settings-test.py:337)); base propagates the error.

- The four registrations bring the deterministic-control inventory to 23 ([evals/harness-settings.json:142](evals/harness-settings.json:142)-[evals/harness-settings.json:168](evals/harness-settings.json:168)). Command-construction value tests now use the inline `CONFIG` fixture rather than live `config.yml` ([scripts/harness-settings-test.py:19](scripts/harness-settings-test.py:19)-[scripts/harness-settings-test.py:48](scripts/harness-settings-test.py:48)); related routing parser tests do likewise ([scripts/harness-settings-test.py:134](scripts/harness-settings-test.py:134)-[scripts/harness-settings-test.py:152](scripts/harness-settings-test.py:152)).

Tests were not executed because this review contract requires read-only operation. Per that rule, I did not create, commit, or push the requested report file.
