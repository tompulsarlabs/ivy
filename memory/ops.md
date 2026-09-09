---
subject: Ivy's runtime environment
type: ops
updated: 2026-09-09
---

# Ops: how the environment actually behaves

Environment facts learned by running, not by reading docs. Each one cost a
run to discover; none of it is re-derivable cheaply.

## Cloud sandbox egress is repo-scoped

Routines run in Claude Code cloud sandboxes whose github.com egress is scoped
to `tompulsarlabs/ivy` alone. GraphQL is blocked, unscoped REST is blocked,
and even the *public* contributions HTML 403s ("sessions are bound to their
configured repositories") [cite:ada1982]. `scripts/check.sh` therefore exits 2
(no signal) in every cloud run — expected, never a reason to guess.

Repo-scoped MCP tools (`list_branches`, `get_file_contents`) are likewise
restricted to this repo; calls against the other 13 return "not configured for
this session" [cite:2026-08-24][cite:2026-08-25]. **Consequence:** "branch
pushed recently with no PR" is not verifiable from a cloud run at all —
`search_commits` only sees default branches. Open PRs and assigned issues are
fully covered; stranded branches are a blind spot.

What does work: git push/pull to this repo via the credential proxy, and the
built-in `mcp__github__*` tools, which are user-scoped rather than repo-scoped
(`get_me`, `list_commits` here, `search_commits` / `search_issues` /
`search_pull_requests` across the org).

**Branch pushes work; tag pushes don't.** `git push origin main` succeeds
through the credential proxy, but `git push origin <tag>` (annotated or
lightweight, `refs/tags/*`) 403s every time — 4 retries with backoff, same
result, confirmed 2026-09-06 during the retro's `git tag v7` step. The
proxy's own guidance for a 403 is "organization policy denial, don't retry
or route around it" [cite:ada1982], and no `mcp__github__*` tool creates a
ref either (`list_tags`/`get_tag` are read-only). So a cloud routine can
push commits to `main` but cannot publish a new version tag — the retro's
`git tag v<N+1>` step needs a human (or a differently-scoped session) to
run after the fact. `v1`/`v2` are the only tags that exist on the remote
despite `CHANGELOG.md` documenting releases through `v7`
[cite:2026-09-06].

**The repo-scope block only inspects the dedicated `owner`/`repo` parameters,
not free-text query content.** `pull_request_read` and `get_file_contents`
called with `owner`/`repo` set to another repo are denied outright ("not
configured for this session"), which had left every `tomgreen.ai` dispatch
contract's file-list/PR-body verification unstamped on prior nights
[cite:2026-09-03]. But `search_pull_requests` (and presumably the other
`search_*` tools, same parameter shape) called with `repo:owner/name` written
*inside the `query` string* instead of the tool's own `owner`/`repo`
parameters returns the full cross-repo result — title, body, draft state,
timestamps — same as the org-wide query already known to work. Confirmed
2026-09-04: fetched the full bodies of `tomgreen.ai` PRs #14 and #15 this
way and used them to verify two contracts that two prior failsafe runs had
left unstamped for lack of access [cite:2026-09-04]. Still no substitute for
`get_files`/`get_diff` (no file-list or line-level diff this way), but it
closes the PR-body-reference gap that blocked most `build`-contract
verification.

`search_code` takes the same `repo:` in query-string treatment and reaches
cross-repo too — confirmed 2026-09-05 resolving three `tomgreen.ai` file
paths from a review report. But it only indexes **default branches**: a
path that exists solely on an open PR's branch returns zero hits, indistinguishable
from a path that was never added. Verifying `2026-09-05-talentradar-review-01`
against PR #1 (still draft, not merged) hit exactly this — `search_code`
came back empty for `src/lib/board.ts`, which the PR's own body then
confirmed exists. So a review/build contract's file-existence check is only
directly answerable by `search_code` once the underlying PR has merged;
before that, PR-body corroboration is the fallback, not a sign the contract
failed [cite:2026-09-05].

## The default clone is shallow, and memory-lint needs full history

The cloud sandbox's checkout of this repo starts shallow (`git
rev-parse --is-shallow-repository` → true). `scripts/memory-lint.sh`
resolves every `[cite:<sha>]` with a local commit lookup, so a citation to
a real, correctly-formed commit can still fail lint in a session whose
shallow depth doesn't reach it — not a broken citation, a checkout
artifact. Confirmed 2026-09-09: `[cite:60535f0]`, `[cite:ada1982]`,
`[cite:e7e918b]`, `[cite:407cf03]` (all pre-existing, unrelated to that
day's edits) failed lint at session start; `git fetch --unshallow` (took
under a minute, ~230 commits total) made all four resolve with no content
change needed. Run `git fetch --unshallow` once per session before trusting
a memory-lint failure that names a citation nothing else about the day's
edits would explain.

## The contributions signal is not stable

The contributions API flaps — 0/2/3/5 across replicas within minutes — so a
grey reading is only trusted after retries [cite:ada1982]. Separately, commit
*search* indexing lags a fresh push by around a minute: to verify a commit
just made, prefer `list_commits` over `search_commits` [cite:ada1982].

## Attribution traps

Two distinct failure modes, both silent:

1. **The invented identity.** With no `user.email` configured, git does not
   warn — it silently invents `user@hostname.local` at commit time. So
   `git config user.email` reads as merely *unset* in exactly the case that
   bites. `git var GIT_AUTHOR_IDENT` reports what the next commit would
   actually use, which is why the scanner reports `author_email_ok` /
   `last_commit_email_ok` as booleans derived from it [cite:60535f0]. Booleans,
   not addresses: the invented identity embeds the machine hostname and
   `local-wip.json` is public [cite:2026-08-27].
   Observed live — six real `tomgreen.ai` commits on 2026-08-27 authored
   `tom@Toms-MacBook-Air.local`, none of them countable [cite:2026-08-27].
   A second invented identity exists from another machine:
   `tom@C2-LAP32-TomGreen.local`, on `ai-capability-app` `24cda31`
   (2026-06-19) — no resolved `author.login`, still uncounted
   [cite:2026-09-01]. The hostname varies by machine, so the check must ask
   "is the author one of the verified addresses", never "is it not this one
   known-bad string".
   **Recovered 2026-08-28**: identity fixed on the Mac, history rewritten
   (`filter-branch --env-filter`, author dates preserved), force-pushed;
   all six now carry the connected author with a resolved GitHub login, and
   zero commits org-wide remain on the invented address [cite:2026-08-28].
   Cost of the day's delay: a one-line config fix became a public-main
   history rewrite — the escalation curve the scout's same-morning nudge
   exists to prevent.
   **Caught pre-push, 2026-08-30:** `ivy`'s own Mac checkout showed 1
   unpushed commit with `last_commit_email_ok: false` — the scout nudged
   same-morning per the playbook's outranking rule, before the commit ever
   reached `main` [cite:2026-08-30]. First observed case of the nudge
   working as designed rather than after the fact [[patterns]].
   **Below the bar, 2026-08-29:** `ai-capability-app` (local `sybil`) has
   `last_commit_email_ok: false` on its one commit from 2026-06-23, but the
   repo is dormant with nothing queued behind it — no same-day work at risk,
   so the "nudge immediately" bar correctly does not fire
   [cite:2026-08-29] [[repos/ai-capability-app]]. Stays uncountable until a
   history rewrite runs, same recipe as the `tomgreen.ai` recovery.
2. **More than one address is connected, and checking against one produced
   false alarms.** `tom@pulsarlabsai.com` is verified on the account — 72
   commits carry it and every one resolves `author.login` [cite:2026-09-01].
   The scanner compared `git var GIT_AUTHOR_IDENT` against `commit_email`
   alone, so repos correctly configured with that address reported
   `author_email_ok: false` and drew same-morning nudges on 2026-08-30 and
   08-31 with nothing to fix [cite:2026-08-30][cite:2026-08-31]. Fixed
   2026-09-01: `config.yml` gained `connected_emails` and the check became
   membership. The cost was not the wasted nudges but the noise — a real
   alarm and a false one looked identical.
3. **Committer is not author.** Only the *author* field decides whether a
   commit counts. Amending the committer of a bot-authored commit to the
   connected address does not make it count — `bc11dd6` was amended that way
   and still does not [cite:2026-08-26].

Bot identity `ivy-bot <bot@ivy.invalid>` (historical:
`bot@evergreen.invalid`) never lights the graph, by design.

## Scheduling

Crons are pinned in **UTC** (07:00 / 16:00 / 20:30) against local Berlin times
of 09:00 / 18:00 / 22:30. When Berlin flips CEST→CET in late October, local
fire times shift to 08:00 / 17:00 / 21:30 — a safe direction, since the
failsafe moves *earlier* and away from the midnight margin.

`local-wip.json` is written by the Mac's launchd scanner at 08:45 and 17:45
local. Past 36h old it means *unknown*, never "nothing pending" — a sleeping
Mac must not read as a clean tree.

## Dispatch runner: launchd env is not a login shell

Two same-day bugs on the Mac D2 runner, both from environment assumptions
that held in an interactive terminal and silently broke under launchd
[cite:2026-09-02]:

1. **Two working copies.** `launchd` ran the plist's script from
   `~/Build/ivy` (moves only when a human pulls), while the runner synced
   and executed from `~/.ivy-dispatch/ivy`. A fix landed in the synced copy
   but launchd kept running the stale one — new contracts, old gate — until
   `main()` was changed to exec the synced checkout after `ensure_clone`.
2. **No PATH.** `claude` lives in `~/.local/bin`, which only `~/.zshrc`
   puts on PATH; launchd starts from the bare system PATH and runs no shell
   profile, so the `bash -lc` wrapper resolved nothing. Fixed by dropping
   the shell wrapper and setting PATH explicitly in the plist over every
   binary the runner and its workers need.

Both cost claimed contracts before being caught: four `tomgreen.ai` build
contracts failed the attribution gate on stale code, two more claimed then
crashed with `FileNotFoundError` on `claude`. All were released back to
`queue/` under their existing ids rather than counted as waste, since no
worker had actually claimed or spent budget on the current code path
[[models]].

## Routine configuration

Routines created without explicit MCP connections inherit **all** of the
account's connectors by default; least privilege requires clearing them
explicitly [cite:ada1982].

## Changelog

- 2026-09-09 — recorded that the default cloud checkout is shallow, which
  makes `memory-lint.sh` misreport valid, pre-existing citations as broken;
  `git fetch --unshallow` is the fix, not a content edit.
- 2026-09-06 (retro) — recorded that cloud sessions can push commits to
  `main` but get a 403 pushing any tag ref; the retro's version-tag step
  needs a human to run.
- 2026-09-05 — recorded that `search_code` reaches cross-repo the same way
  as the other `search_*` tools but only indexes default branches, so it
  cannot confirm a path that exists only on an open PR's branch; PR-body
  text is the fallback for that case.
- 2026-09-04 — recorded that embedding `repo:owner/name` in a `search_*`
  tool's query string, rather than its `owner`/`repo` parameters, returns
  cross-repo results the dedicated parameters would have blocked; used it to
  verify two previously-unstamped `tomgreen.ai` dispatch contracts.
- 2026-09-02 — repaired three citations broken since the repo's bootstrap
  import (`ada1982`, 2026-08-29): `[cite:b85b8af]`, `[cite:d96eeef]` and
  `[cite:5f41f0a]` referenced no commit reachable in this checkout (likely
  orphaned by a pre-import history rewrite), which had made
  `memory-lint.sh` fail unconditionally for any memory commit since that
  import — an undetected blocker, not caught by any run that touched
  memory/ in between. No claim content changed: the two sandbox/API facts
  now cite the bootstrap import itself (`ada1982`), since they trace to
  `DESIGN.md` rather than a journal observation; the attribution-hostname
  claim now cites `2026-08-27`, where the matching journal entry actually
  exists.
- 2026-09-02 — recorded the two same-day launchd runner bugs (stale synced
  checkout, missing PATH) and how the four affected contracts were
  released rather than counted as waste.
- 2026-09-01 — recorded that `tom@pulsarlabsai.com` is also connected, that
  the single-address check produced false-alarm nudges (now fixed), and that
  a second invented hostname identity exists on `ai-capability-app`.
- 2026-08-30 (retro) — recorded the pre-push attribution catch on `ivy`
  itself and the below-the-bar `sybil` finding; both confirm the attribution
  rule's severity ordering is calibrated correctly, no change made.
- 2026-08-28 — attribution incident marked recovered: Mac identity fixed,
  tomgreen.ai history rewritten and verified clean org-wide.
- 2026-08-27 — page created, synthesized from `playbook.md` ops notes,
  `DESIGN.md` §6, and journals 2026-08-23→27.
