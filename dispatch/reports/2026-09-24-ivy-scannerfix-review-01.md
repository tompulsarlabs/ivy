# Report — 2026-09-24-ivy-scannerfix-review-01

Produced by the workhorse/anthropic lane, 18.2 wall-minutes.

# Findings — PR #22 "Restore local work visibility and isolate scanner publication"

**Contract:** `2026-09-24-ivy-scannerfix-review-01` · **Reviewed head:** `173a9e6` (as specified)

## 0. Scope and state notes (read first)

- **The reviewed head is not the branch head, and the PR is already merged.** `173a9e6` is the second of three commits on `codex/ivy-scanner-reliability`; `dc236fc` ("Isolate scanner Git context and publication identity") follows it, and the branch merged to `main` at `2524ad9`. All line numbers below are anchored at `173a9e6` (`git show 173a9e6:<path>`); `dc236fc` shifts `scripts/local-wip.py` by ~24 lines. Every finding carries a **status**: open on `main`, or closed at `dc236fc`.
- **`launchd` installation/activation is deferred, correctly and explicitly.** This PR ships the installer (`setup/install-wip-scanner.sh`) and documents it (`setup/SETUP.md:41-44`); `setup/install-wip-scanner.sh:12-15` refuses to install from anything but `main`, and `evals/local-scanner.json:172` records `launchd_install: "not_run"`. **The original blocker is therefore not closed by this PR.** Its `main` precondition is now satisfied (merge `2524ad9`), so the install step is available and unperformed. Worth noting for the runbook: the one live publication that proves the new path works (`1c6da31`, `local-wip.json:2`, `generated_at 2026-09-24T08:43:47Z` = 10:43 CEST) fell in neither scheduled window (08:45/17:45 local; prior scheduled runs landed at `15:45:06Z`), so it was a manual run. Nothing yet demonstrates the `launchd` path fires.
- **Verification limits.** This session's sandbox blocked executing `scripts/local-wip-test.py`, `launchctl`, `gh`, and any read outside the working directory (`~/Build`, `~/Library/LaunchAgents`). **No pass of the 23 controls is claimed here** — they were read, not run. CI status unverified.

---

## Findings

### F1 — `last_commit_email_ok` reports the repo's highest-priority alarm on unborn repos, transient git failures, and legitimately bot-authored HEADs (open on `main`)

`scripts/local-wip.py:204-206`, and `:134` for the same pattern in `next_author_email`.

```python
"last_commit_email_ok": ((git(repo, "log", "-1", "--format=%ae") or "") in connected_emails),
```

Three separate ways to a false `false`:

1. **Unborn repo.** `:200` guards `last_commit` with `has_commits`; `:204-206` is not guarded. `git init ~/Build/thing` with no commit → `git log -1` exits 128 → `git()` returns `None` → `"" in connected` → `false`.
2. **Transient failure.** These two fields alone use the non-raising `git()` rather than `required_git()`. A 60s timeout (`:46`) or a lock collision publishes `false` as a *verdict*, not as a failure — so the PR-body claim "failed reads remain failures" holds for every field except the two with the highest consequence.
3. **Bot-authored HEAD — already firing in production.** `local-wip.json:222` shows `ivy-paperclip-release: last_commit_email_ok: false`. I checked its HEAD: `origin/codex/ivy-acceptance-scaffold` is authored `ivy-bot <bot@ivy.invalid>`. `playbook.md:295` states bot commits never count *by design*; the scanner reports that design as a misattribution. This is pre-existing logic (identical at `2aa1829`) — the pre-PR snapshot `35c8228` already showed `false` on the root `ivy` row — but it now flaps across four `tompulsarlabs/ivy` rows instead of one, because worktree discovery added three.

**Consequence:** `playbook.md:169-176` makes `last_commit_email_ok: false` outrank every other candidate, lead the journal, and break the scout's silent rule with an immediate nudge. Any of the three paths above pages the operator about work that is fine.

**Fix:** `"last_commit_email_ok": True if not has_commits else (required_git(repo, "log", "-1", "--format=%ae") in connected_emails)`, plus a bot exemption: treat `bot@ivy.invalid` / `bot@evergreen.invalid` (`playbook.md:295`) as not-an-alarm, e.g. emit `last_commit_bot: true` and have the playbook rule skip those rows. Extend WIP05 (`scripts/local-wip-test.py:93-95`) to assert both identity fields on an unborn repo — as written it asserts only `unpushed_commits`/`last_commit`, so it passes today.

### F2 — repo-wide count is duplicated into every worktree row with no grouping key, and `playbook.md` was not updated (open on `main`)

`scripts/local-wip.py:198-199`; consumer rule at `playbook.md:163-166`; guidance placed at `setup/SETUP.md:61-63`.

Live proof in `local-wip.json`: `Talent Radar` (`:9`) and `talent-radar-pilot` (`:152`) both report `unpushed_commits: 2, checkout_unpushed_commits: 0` — the *same* 2 commits, on the same repo, as two independent first-class candidates. Neither checkout's HEAD holds them, so the scout cannot even name which branch to push.

`setup/SETUP.md:61-63` does warn "Do not sum repository-wide counts across worktrees of the same repository" — but the scout reads `playbook.md`, never `SETUP.md`, and `CLAUDE.md` states that `playbook.md` is the only place behaviour lives. `playbook.md:163-166` still keys solely on `unpushed_commits > 0` and knows nothing of `checkout_unpushed_commits`.

**Fix:** group by `remote` in the scout rule (all four `ivy` rows share `tompulsarlabs/ivy`), and emit an explicit grouping key for the `remote: "none"`/`"other"` cases where that is not enough. The `playbook.md` edit is an Immutable-section change needing a human commit — file it as a follow-up contract rather than folding it into the scanner.

### F3 — inherited Git environment was not isolated at the reviewed head (closed at `dc236fc`)

`scripts/local-wip.py:47`: `env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}`. `git -C` does not override `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE`, so a scan launched from a shell carrying those would read the wrong repository, and `-c user.email=bot@ivy.invalid` (`:38`, `:252`) loses to an inherited `GIT_COMMITTER_EMAIL` — the publish commit's *committer* could be the operator, or any override. This was reproducible inside the suite itself: the fixture exports `GIT_COMMITTER_EMAIL=fixture@example.invalid` (`scripts/local-wip-test.py:39`), and WIP16 asserts only `%ae` (`:177`), never `%ce`.

`dc236fc` closes it (`GIT_LOCAL_ENV` scrub + forced `GIT_{AUTHOR,COMMITTER}_{NAME,EMAIL}`) and adds two controls that confirm the defect was real: `test_inherited_git_repository_cannot_redirect_a_scan` and `test_publication_ignores_inherited_checkout_and_commit_identity` (asserting `%an|%ae|%cn|%ce` all `ivy-bot|bot@ivy.invalid`). **No action — recorded so the review record matches the code.**

### F4 — one unreadable checkout suppresses the entire snapshot, and from the cloud that is indistinguishable from a sleeping Mac (open on `main`)

`scripts/local-wip.py:78` (`required_git(repo, "worktree", "list", ...)`), `:174-192`, propagating to `:293-297` → exit 1, nothing published.

Failure: one repo under `~/Build` with a corrupt `.git`, a permission-denied directory, or a `git status` that exceeds the 60s timeout (`:46` — a large untracked tree or a network mount) → every run of the scanner publishes nothing, for all 21 checkouts, indefinitely. The scout sees only staleness and applies the 36h rule (`playbook.md:166-169`), i.e. the same "local WIP unknown" as the outage this PR fixes. Fail-loud is the right instinct (WIP04, WIP09 pin it), but all-or-nothing is not.

Related, same failure shape: `git worktree list --porcelain -z` (`:78`) requires Git ≥ 2.36; an older `git` on the operator's PATH (`scripts/local-wip.sh:5` pins `/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin`) fails every scan with no version check.

**Fix:** keep the nonzero exit, but make the snapshot survivable — collect per-repo read failures into an `errors: [{name, stage}]` list and publish "20 read, 1 failed" rather than nothing. The heartbeat then keeps carrying signal, and the scout sees a named broken repo instead of an absence. Add a control for it; note also that no current control exercises the `except (RuntimeError, OSError)` handler at `:292-297` at all, because it lives under `__main__` and the tests import the module.

### F5 — the "published snapshot is newer" guard has no recovery path (open on `main`)

`scripts/local-wip.py:225-226`. If a snapshot whose `generated_at` is ahead of the Mac's clock ever lands on `main` (clock skew, a hand-edit, a second publisher), `should_publish` raises and the run exits 1. It self-clears once wall-clock passes that timestamp — but a far-future timestamp wedges the scanner permanently, silently, in exactly the shape of the original blocker. WIP14 (`scripts/local-wip-test.py:156-158`) pins the refusal; nothing covers recovery.

**Fix:** bound it — raise only when `old - new` exceeds a tolerance (say 24h); below that, skip publication and exit 0 with a clear message. Above it, keep the refusal but print the offending timestamp so the operator can act.

### F6 — discovery widened what gets published from clone names to worktree basenames (open on `main`)

`scripts/local-wip.py:194` (`"name": repo.name`) against the Privacy contract in the module docstring `:6-12`. Before this PR, names came from `~/Build/*` clone directories; now any registered worktree's basename is published, and worktree directories are task-named. Live example: `local-wip.json:225` publishes `tomgreen-colours-audibene-20260922` — a client-shaped name that was not in the pre-PR snapshot.

I could not confirm `tompulsarlabs/ivy`'s visibility from this sandbox; if the repo is private this is a note rather than a finding, but the docstring asserts it is public and reasons from that.

**Fix:** for linked worktrees, publish the main worktree's name plus a `worktree: true` flag, or the branch alone — the `remote` slug already carries the identifying information the scout needs.

### F7 — module docstring describes a write path this PR deleted (closed at `dc236fc`)

`scripts/local-wip.py:16-17` still claims "written atomically (temp file + `os.replace`) under a lock"; that write is gone — output now goes through the temporary clone. `dc236fc` rewrites the line. **No action.**

### F8 — the six-hour constant is inert against the actual schedule (open on `main`; low)

`scripts/local-wip.py:37` (`HEARTBEAT = 6h`) against `setup/ai.tomgreen.ivy-wip.plist:13-17` (08:45 / 17:45 → gaps of 9h and 15h). Every scheduled run therefore republishes even when nothing changed; the constant only ever suppresses manual re-runs (which is what WIP17 exercises, in-process). That is benign, but the number that matters operationally is the scout's 36h rule, and the two are documented as if they were one mechanism (`setup/SETUP.md:66-68`). Detection latency for a failed scan is consequently ~3 missed windows.

**Fix:** none required in code; state the relationship explicitly where the heartbeat is documented, so a future schedule change doesn't silently cross the 36h line.

### F9 — the "isolated" temp clone still inherits `core.hooksPath` (open on `main`; low)

`scripts/local-wip.py:252-254` passes `-c user.name/-c user.email/-c commit.gpgsign=false` but not `-c core.hooksPath=`. A global `core.hooksPath` runs the operator's `pre-commit`/`commit-msg` hooks inside the clone the PR describes as owned solely by this invocation, and a failing hook turns into "publication failed after 3 attempts."

**Fix:** add `-c core.hooksPath=/dev/null` (or `--no-verify`) to the publish commit.

### F10 — smaller items (open on `main`)

- `scripts/local-wip.py:181-182` vs `:188-192`: the two `rev-list` constructions differ only by `--not --remotes`, with `*(["HEAD"] if has_commits else [])` written twice. Extract one counter.
- `scripts/local-wip.py:186`: the remote regex accepts only `https://github.com/…` and `git@github.com:…`; `ssh://git@github.com/owner/repo` degrades to `"other"`, which also defeats the F2 grouping-by-remote fix for such repos.
- Test command drift across three homes: `evals/local-scanner.json:5` and `.github/workflows/local-scanner.yml:33` require `-W error::ResourceWarning`; `setup/SETUP.md:72` omits it.
- `.github/workflows/local-scanner.yml:9-13` repeats its three `paths:` globs verbatim at `:16-19`.

### F11 — vocabulary (open on `main`; standards axis)

`CONTEXT.md` is the repo's vocabulary, and its unit is the *repository*: `CONTEXT.md:101` ("dirty and unpushed work per repository") is now stale, because rows are per worktree. "Checkout" — used in the payload semantics, the commit subject (`scripts/local-wip.py:253`, `"wip: local scan — {n} checkouts"`), `setup/SETUP.md`, and `evals/local-scanner.json:171` — is not in `CONTEXT.md`. Per `CLAUDE.md`, a word the vocabulary lacks is a gap to flag for the retro. `heartbeat` is a second, milder case: `CONTEXT.md:168` reserves it for the runner's tick, and `scripts/local-wip.py:37` gives it a second sense. `OVERVIEW.md:160-172` and `DESIGN.md:40` also still omit the new `evals/`, `.github/`, `scripts/local-wip-test.py`, and `setup/install-wip-scanner.sh`.

**Fix:** one retro-scoped `CONTEXT.md` entry defining *checkout* against *repository*, refreshing `:101`, and resolving the `heartbeat` collision; a one-line repo-map update in `OVERVIEW.md`/`DESIGN.md`.

---

## Verified as claimed — plain confirmations

- **Worktree discovery is real and covers what the body claims.** `scripts/local-wip.py:78-85` walks each discovered repo's `worktree list --porcelain -z` and adds existing worktrees regardless of location, skipping prunable entries without touching Git's registry (WIP01/WIP03, `scripts/local-wip-test.py:67-87`). Live corroboration: `local-wip.json` carries four rows with `remote: tompulsarlabs/ivy` (`:82`, `:192`, `:203`, `:214`) — the root checkout plus exactly the 3 Ivy worktrees the body cites — and no absolute path appears anywhere in the payload. *Caveat:* root globbing is depth ≤ 2 (`:70`), so a checkout three levels under `~/Build` is invisible unless it is a registered worktree of a discovered repo; and the "worktree outside the roots" path is exercised by WIP01 but not by the live data (I could not read `~/Build` from this sandbox to confirm which of the three sit outside).
- **The publish path never touches the operator checkout.** The only operations against `IVY` are `remote get-url` (`:286`, read-only) and the lock file at `:36`/`:279` — which `.gitignore` covers (`+.local-wip.lock`). Everything else happens in `tempfile.TemporaryDirectory` (`:233-235`). WIP16 (`scripts/local-wip-test.py:164-177`) pins HEAD, `diff`, and `diff --cached` as unchanged across a publication. Live evidence that the new path is what actually ran: the pre-PR commits `35c8228`/`6799b25` have committer `tompulsarlabs`, and `1c6da31` (post-merge) has committer `ivy-bot` — the operator-checkout path is gone.
- **No invented attribution identity.** `BOT` (`:38`) and `--author=ivy-bot <bot@ivy.invalid>` (`:254`) are exactly the identity the repo already specifies at `CONTEXT.md:42` and `playbook.md:41`, asserted by `scripts/local-wip-test.py:177` and, at `dc236fc`, for committer as well. No `[[ops]]` attribution trap in the publish path. (The trap is on the *reporting* side — F1.)
- **Symlink refusal is real.** `scripts/local-wip.py:242-243` checks `is_symlink()` after clone/reset and before any write, so a symlinked `local-wip.json` on `main` cannot be used to write outside the clone; WIP23 (`scripts/local-wip-test.py:242-252`) exercises it end-to-end and asserts the outside file is preserved.
- **Branch races and failed pushes are handled as described.** `:236-257`: bounded at 3 attempts, `fetch` + `reset --hard origin/main` between attempts, push is always non-force `HEAD:refs/heads/main`, exhaustion raises. WIP18 (`:186-203`) drives a real racing push and asserts the racer's commit survives; WIP19 (`:205-211`) asserts a failed push raises and that a later run can still publish.
- **Duplicate suppression and concurrent locks are covered.** WIP17 (`:179-184`) asserts no commit inside the heartbeat window; WIP21 (`:223-230`) holds the `flock` and asserts `collect_snapshot` is never called; WIP22 (`:232-240`) asserts a stale lock *file* no longer blocks a scan — a real improvement over the pre-PR PID-file scheme at `2aa1829:scripts/local-wip.py` (`acquire_lock`, 15-minute staleness heuristic).
- **The eval inventory is real and honest.** `evals/local-scanner.json` declares 23 cases, and all 23 `test_name` values map 1:1 onto methods that exist in `scripts/local-wip-test.py` — no phantom entries. It sets `model_quality_claim: false` throughout and records its unrun integration steps explicitly (`:170-175`), which is the separation `AGENTS.md` asks for. `dc236fc` takes it to 25. The `.github/workflows/local-scanner.yml` job that runs the suite on 3.11/3.14 is the reported-evidence path for those controls, not scope creep.
- **"Unchanged" vs "scan failed" is distinguishable at the consumer, with a caveat.** `should_publish` (`:218-228`) republishes on change, on a missing/malformed previous, or after 6h; a failed scan publishes nothing and exits 1 (`:293-297`), and the scout's 36h rule (`playbook.md:166-169`) reads that absence as *unknown*, never as "nothing pending". The claim holds — with the exceptions in F1 (two fields report failure as a verdict) and the ~3-window detection latency in F8.
- The eval's "20 checkouts" (`evals/local-scanner.json:171`, dated 2026-09-23) against `1c6da31`'s 21 is a day's drift, not a discrepancy.

---

## Not verified in this session

Execution of `scripts/local-wip-test.py` (sandbox denied); CI status for the PR (`gh` denied); `git -C ~/Build/ivy worktree list` (reads outside the working directory denied); current `launchd` state via `launchctl`/`~/Library/LaunchAgents` (denied). No pass or failure of the 23 controls is asserted here.

## Note on the definition of done

The contract's definition of done asks for `dispatch/reports/2026-09-24-ivy-scannerfix-review-01.md`, committed and pushed. This session's Rules are read-only and instruct that the report be printed between `BEGIN_REPORT`/`END_REPORT` instead; the Rules take precedence, so no file was written and no commit was made by this worker. The text above is the complete report body, ready to be committed verbatim at that path.
