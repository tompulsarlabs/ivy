# Report — 2026-09-24-ivy-harnesseffort-review-01

Produced by the workhorse/anthropic lane, 9.3 wall-minutes.

# Review — PR #23 "Apply harness effort settings and record execution provenance"

**Head reviewed:** `e23037c` (`codex/ivy-harness-settings`), base `main` `083f1fc`, merge-base `2aa1829`.
**Files:** `scripts/dispatch-runner.py`, `config.yml`, `docs/harness-settings.md`, `scripts/harness-settings-test.py`, `evals/harness-settings.json`, `.github/workflows/harness-settings.yml`.

## What was verified, and how

Read-only review from the local clone (all PR refs were already fetched). `gh`, network fetches, `python3 -c`, file writes outside the repo, and reads outside the working directory were all refused by this sandbox — so **no test in this PR was executed here**, and the notes below say where a claim rests on reading rather than running. One primary-source check did succeed: `claude --help` on this Mac.

## Confirmations (claims that hold)

**1. Effort reaches the Claude CLI, and frontier now differs from workhorse.**
`scripts/dispatch-runner.py:236-238` appends `["--effort", effort]` to the `claude -p` argv; `config.yml:66` (`effort: xhigh`) and `config.yml:69` (`effort: medium`) resolve through `harness_argv` to two different argv lists. At the merge-base the same function had no effort branch at all, so both lanes produced byte-identical commands — **the PR body's premise is accurate**. `claude --help` on this machine lists `--effort <level>  Effort level for the current session (low, medium, high, xhigh, max)`, exactly the value set registered for `claude-opus-5` at `scripts/dispatch-runner.py:46`. The flag is real and the registry matches it.

**2. Codex: the argv is constructed, but no configured lane exercises it.**
`scripts/dispatch-runner.py:246-247` emits `-c model_reasoning_effort="high"` (via `json.dumps`, so the value is TOML-quoted and injection-proof; `harness-settings-test.py:48` covers a newline-injection attempt). However **no `openai` lane in `config.yml` carries an `effort` key** (`:67`, `:70`), so on merge only the Anthropic lanes change behaviour; the codex path is exercised solely by the synthetic entry in HS02. Not a defect — but read the "both CLIs" claim as *code-complete for codex, config-inert for now*. Unverified here: `codex --help` was blocked, so the `-c model_reasoning_effort=` syntax and the seven-value set at `:50-51` (`none…ultra`) rest on the doc's cited source, not on the local CLI.

**3. Rejection genuinely precedes both claim and project clone.**
Order in `main()`: `harness_argv` validation at `:399-403` → `resolve_harness` `:404` → `ensure_clone(clone, …)` `:412` → `execution_metadata` `:428` → `set_state(…, "claimed")` `:429` → claim push `:430`. An unregistered model/harness/effort raises `ValueError` at `:231-234`, is caught at `:402`, and the contract is left `open` with `reason: invalid_harness_config`. No clone, no claim, no push. `harness-settings-test.py:161-192` asserts exactly this with `claim.assert_not_called()`, `worker.assert_not_called()`, and the contract file byte-unchanged. The runner's *own* IVY self-sync (`:365`) still runs, as it must; that is not a task clone.

**4. Haiku 4.5's effort is removed, not defaulted.**
`config.yml:72` drops the field; `scripts/dispatch-runner.py:48` maps `claude-haiku-4-5` to an empty set, so any explicit effort raises; `:237` omits `--effort` when effort is `None`. HS05 covers both halves. At the argv level this is a real removal — **subject to finding 1 below**, which is the one path by which an effort can still reach a Haiku worker.

**5. Route preview is inspect-only on both paths it claims.**
The `--preview-routes` branch at `:346-351` sits above `WORKROOT.mkdir`, the flock, `ensure_clone(IVY, …)` and every `publish_status` call, and returns directly. `preview_routes` `:294-312` calls only `load_config` and `harness_argv` — no `resolve_harness`, no `harness_version`, no `subprocess`, no writes. Success path: prints JSON, returns 0. Invalid-combination path: marks the entry `invalid_configuration`, returns 1, still no side effect. Crash path (missing/malformed config): the exception reaches `guarded_main`, and `:493-494` returns 1 *before* `publish_status`, so no status file write and no bot commit. HS08/HS09/HS10 assert all three. **The claim holds.**

## Findings

### F1 — Medium. An inherited `CLAUDE_CODE_EFFORT_LEVEL` still reaches effort-less Claude lanes
`scripts/dispatch-runner.py:254-259`

`harness_environment` copies `os.environ` wholesale and sets the variable *only* when the lane has an explicit effort. For `fast-cheap` (Haiku, no effort) — and for any future Claude lane with effort unset — a value present in the runner's environment passes straight through to the child, while `execution_metadata` records `requested_effort: unset` (`:280`). That is precisely the silent default the PR sets out to close, and it contradicts `docs/harness-settings.md:4-6`, which frames the environment as pinned. HS07 only tests the *explicit*-effort direction, so the gap is untested. (Separately: `CLAUDE_CODE_EFFORT_LEVEL` does not appear in this machine's `claude --help`, and the doc cites only the `--effort` page for it — if the variable name is wrong, the pin is inert in both directions. Worth a citation in the doc.)

**Fix:** pop before setting, unconditionally for the Claude harness —
```python
env.pop("CLAUDE_CODE_EFFORT_LEVEL", None)
if entry["harness"] == "claude-code" and entry.get("effort") is not None:
    env["CLAUDE_CODE_EFFORT_LEVEL"] = entry["effort"]
```
and add the mirror-image assertion to HS07: an unset lane yields a child environment with no effort variable.

### F2 — Medium. A malformed `config.yml` now halts every lane, and looks healthy from the cloud
`scripts/dispatch-runner.py:119-124`

The new per-item `re.fullmatch` raises `ValueError("malformed or duplicate harness setting")` for any key outside `{harness, model, effort}`, any duplicate, and any junk the greedy `^    ([a-z]+):\s*\{(.*)\}` pulls in (a `}` inside a trailing comment would do it). `load_config()` is called at `:388`, outside the per-contract loop, so the exception propagates to `guarded_main` `:486` and aborts the whole tick — not one lane. The predecessor `dict(re.findall(...))` tolerated unknown keys, so this is a new blast radius on a block `config.yml:64` explicitly labels "data, retro-tunable", and PR #21 is about to add comment lines inside it.

Worse, the failure is invisible to the scout's own tests: `publish_status("runner_error: ValueError", [], True, now)` writes `harness: true`, `lint_ok: true`, an empty `skipped`, and a **fresh** `last_tick`. `playbook.md:150-154` names exactly three blocker triggers — `harness` false, `lint_ok` false, `last_tick` stale — and none of them fire. The queue stops draining while the heartbeat reads green.

**Fix (either, ideally both):** (a) scope the failure — catch the `ValueError` per pool entry in `load_config` and store a sentinel (e.g. `{"model": "MALFORMED"}`) so only contracts routed there skip, leaving other lanes live; (b) add the strict lane parse to `scripts/dispatch-lint.sh` so a bad edit is caught at commit time rather than at the next tick.

### F3 — Low/Medium. `execution_metadata` adds a new tick-fatal raise between clone and claim
`scripts/dispatch-runner.py:275-278`, called at `:428`

`run(["git", "rev-parse", "HEAD"], cwd=clone)` uses the default `check=True`, and the explicit `raise RuntimeError("source revision unavailable")` follows. Either escapes the per-contract loop and kills the tick with `runner_error`, where every neighbouring failure in this loop (`lane_unresolved`, `invalid_harness_config`, `harness_missing`, `attribution_gate`) is deliberately handled as a per-contract skip so one bad contract cannot stop the others. Unlikely to fire after `ensure_clone`'s `reset --hard`, but it is a new single point of tick failure introduced by a provenance feature — provenance capture should not be able to stop dispatch.

**Fix:** wrap the call at `:428` in `try/except (RuntimeError, OSError)` and `continue` with `skipped.append({"id": cid, "reason": "provenance_unavailable"})`, consistent with the block above it.

### F4 — Low. `--preview-routes` can preview a config the runner will not use
`scripts/dispatch-runner.py:349`, `docs/harness-settings.md:9-13`

The default is `Path(__file__).resolve().parent.parent / "config.yml"` — the checkout the command was invoked from. Live dispatch reads `IVY / "config.yml"` (`:104`, hashed at `:287`). The module docstring (`:23-26`) states the whole reason this matters: the launchd entry point is a dev checkout that only moves when a human pulls, while the runner execs the synced copy under `~/.ivy-dispatch/ivy`. Running the preview from the dev checkout therefore reports routes that need not match the next tick's, under a doc line that says "current configuration".

**Fix:** default to `IVY / "config.yml"` when it exists, falling back to the script-adjacent path; and emit the resolved path plus its `config_sha256` in the printed profiles so the output states which file it described.

### F5 — Low. The new tests pin live config values, so a lawful lane re-tune turns CI red
`scripts/harness-settings-test.py:28-34` and `:84-90`; `.github/workflows/harness-settings.yml:29`

`test_config_to_claude_commands_preserves_distinct_lane_efforts` asserts `xhigh`/`medium` against the real `config.yml`, and `test_route_preview_…` asserts `len(profiles) == 5`. `config.yml:64` declares lanes retro-tunable data; PR #21's config comment already plans a move to "workhorse at medium … frontier at high". Both assertions break on a legitimate tuning commit, and the CI workflow triggers on `config.yml` paths, so the break is immediate.

**Fix:** drive the argv-value assertions from an inline fixture config (the pattern `dispatch-runner-test.py:20-33` already uses), and keep one live-config test that asserts only the invariant — every lane entry parses and validates, and no two lanes with different efforts produce equal argv.

### F6 — Low. New vocabulary lands without a `CONTEXT.md` entry
`CONTEXT.md:149-153`; `docs/harness-settings.md`

`CONTEXT.md` defines a lane as resolving to "a harness and model per pool" — effort is now a routed setting of equal standing, and the PR introduces "execution provenance", "route preview", and the outcome fields `requested_effort` / `effective_effort` / `context_capture` / `usage_capture`, none of which the vocabulary carries. `CLAUDE.md` is explicit that a missing word is a gap to flag for the retro rather than a synonym to invent, and `dispatch/DESIGN.md:82` currently describes the status file's contents without the new skip reason.

**Fix:** extend the **Lane** entry to name `effort` as lane-resolved config, add a short **Provenance** entry covering the `requested_` vs `effective_` distinction, and flag the rest for the retro rather than leaving `docs/harness-settings.md` as the sole definition site.

## PR #21 dependency (merge order — Tom's call, recorded here as asked)

Assumption: `gh` was unavailable in this sandbox, so I matched PR #21 to `origin/claude/skills-playbooks-refresh-784cgk` by its content (playbook/routine re-tune, claude-authored, touches both files). The conflict is real and larger than "same files":

- **`harness_argv` — direct textual conflict.** #21 adds its own effort branches at the identical lines (`if effort: argv += ["--effort", effort]`, and `-c model_reasoning_effort="{effort}"` with the value interpolated **unquoted-by-`json.dumps`**, i.e. raw). #23's registry-validated version is strictly stronger.
- **Pre-claim skip block — conflict.** #21 introduces `lane_problem()` returning `lane_invalid`; #23 uses `harness_argv`'s `ValueError` and the reason `invalid_harness_config`. Two names for one state; the survivors should settle on one, since `skipped` reasons are what `playbook.md:154` tells the scout to read.
- **`config.yml:72` — conflict.** Both PRs remove `effort: low` from Haiku, with different trailing comments.
- **Outcome `base` lines and the module docstring** — both edited in both PRs.
- **The registry dependency is concrete.** #21's new config comment instructs a move of the Anthropic entries to the newest Opus after `claude update` on the Mac. Under #23, such a move **without** a matching entry in `HARNESS_MODELS` (`scripts/dispatch-runner.py:44-53`) makes every Anthropic contract skip with `invalid_harness_config` — the whole Anthropic side of dispatch stops, quietly. If #23 merges first, #21's rebase should drop `lane_problem`/`CLAUDE_EFFORTS` in favour of `HARNESS_MODELS`, and its config comment should say "add the registry entry" alongside "move the entries".
- Note #21's comment claims Claude Code 2.1.280 is required for the newest Opus and that #23 found 2.1.277 installed. `docs/harness-settings.md:52-60` says the same and correctly declines to claim readiness. I could not verify either version here (`claude --version` was blocked), only that `--effort` exists in the installed CLI's help.

## Not verified in this session

- No test in this PR was run (`harness-settings-test.py`, `dispatch-runner-test.py`, `--preview-routes`); the sandbox is read-only and the PR head could not be materialised. `.github/workflows/harness-settings.yml` runs all three on 3.11 and 3.14, so CI on the PR is the evidence to read.
- `codex --help` was blocked: the `-c model_reasoning_effort=` syntax and the registered value set for the gpt-5.6 models are unconfirmed against the local CLI.
- `CLAUDE_CODE_EFFORT_LEVEL` could not be confirmed as a Claude Code environment variable (grep outside the working directory is blocked); see F1.
- Installed CLI versions unconfirmed.
