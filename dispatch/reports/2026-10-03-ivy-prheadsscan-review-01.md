# Report — 2026-10-03-ivy-prheadsscan-review-01

Produced by the workhorse/openai lane, 1.6 wall-minutes.

# PR #25 review — request changes

Reviewed head: `c59a4c4f5c6537e37eb8ce785ca329f35d6e01d3`

## Finding

- **Medium — High confidence:** A malformed `local_wip.roots` configuration exits via `SystemExit`, bypassing the new `scanner_error` publication path. `read_roots()` calls `sys.exit(1)` when the block is present but no roots parse ([scripts/local-wip.py:166](scripts/local-wip.py:166)–[169](scripts/local-wip.py:169)); `main()` only catches `ScanError` and `OSError` around collection before publishing the error ([scripts/local-wip.py:464](scripts/local-wip.py:473)). Thus this real scan/configuration failure leaves the cloud with no `scanner_error`, contrary to the PR claim that failed scans reach it with a fixed code. Proposed fix: raise `ScanError("config_invalid", ...)` from `read_roots()` instead of calling `sys.exit`, and add an end-to-end test asserting the published annotation and unchanged `generated_at`.

## Confirmed

- PR-head discovery uses one `git ls-remote` per submitted watchlist repository, with a real 15-second subprocess timeout, disabled terminal prompting, disabled GCM interaction, and `DEVNULL` stdin ([scripts/local-wip.py:203](scripts/local-wip.py:227)). The six-worker collector has a 120-second `as_completed` budget and cancels queued work on expiry ([scripts/local-wip.py:230](scripts/local-wip.py:248)). The current watchlist has 22 repositories, so its maximum normal timeout schedule is four 15-second waves.
- A failed PR-head lookup returns `None`, while an answered repository with no PRs returns `{}`; only non-`None` results enter `pr_heads` ([scripts/local-wip.py:203](scripts/local-wip.py:227), [scripts/local-wip.py:240](scripts/local-wip.py:243)).
- `scanner_error` is applied by copying the previous snapshot and adding only error fields; `generated_at` is preserved ([scripts/local-wip.py:364](scripts/local-wip.py:380)). Successful snapshots clear it through the content comparison ([scripts/local-wip.py:349](scripts/local-wip.py:361)).
- Word budgets are warn-only by default: `BUDGET_MODE` defaults to `warn` ([scripts/memory-lint.sh:20](scripts/memory-lint.sh:24)), and the default over-budget branch writes a warning without setting `fail` ([scripts/memory-lint.sh:35](scripts/memory-lint.sh:43)). `IVY_MEMORY_BUDGET=fail` alone makes the condition fatal.
- The PR contains 41 scanner tests. Spot checks show substantive new coverage: unreachable repositories are absent ([scripts/local-wip-test.py:326](scripts/local-wip-test.py:330)); error publication preserves the prior snapshot timestamp ([scripts/local-wip-test.py:423](scripts/local-wip-test.py:429)); and a collection `ScanError` is routed to error publication while retaining nonzero behavior ([scripts/local-wip-test.py:452](scripts/local-wip-test.py:460)).
- `git diff --check` reported no whitespace errors.

## Verification limitation

The provided checkout is read-only and the contract also requires leaving checkout branches unchanged. Therefore I could not create, commit, or push `dispatch/reports/2026-10-03-ivy-prheadsscan-review-01.md`. The claimed Python 3.14/3.9.6 test runs and live/network dry-runs were not independently rerun in this restricted environment.
