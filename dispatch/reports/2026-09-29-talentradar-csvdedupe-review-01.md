# Report — 2026-09-29-talentradar-csvdedupe-review-01

Produced by the workhorse/openai lane, 10.2 wall-minutes.

# PR #7 CSV de-duplication review

## Verdict: PASS

## Findings

No actionable findings.

`src/lib/market/import.ts:46` uses the specified seven-part JSON key. Distinct undated rows now survive when round/amount/currency differ, and when investors alone differs; rows matching all seven fields still collapse.

The extended case beginning at `tests/market-signals.test.ts:16` is a genuine regression test: both distinct undated pairs would return one row under the old three-field key, while the exact duplicate still expects one row.

Missing optional fields normalise to empty strings before keying; JSON serialization is unambiguous. Leading/trailing investor whitespace is trimmed. Case and internal-whitespace variants remain distinct, which is an unstated normalisation policy rather than a breach of the exact-seven-field contract.

The disclosed `announcementUrl`-only last-wins case is correctly out of scope: blank rows differing only there match all seven specified identity fields, so adding it to the key would contradict this PR’s stated contract.

GitHub CI run 242 succeeded; the PR diff is whitespace-clean.

Read-only constraint honoured: no report file, commit, or push was created.
