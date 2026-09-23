# Setting Ivy up from scratch

Two halves: four cloud routines (scheduled Claude Code runs) and one local
launchd job (the WIP scanner). Everything else is state in this repo.

## 1. Prerequisites

Starting from a blank Mac, or handing this to someone non-technical? Work
through [`AGENTIC-STACK.md`](AGENTIC-STACK.md) first — it installs the
languages, Claude Code, Codex, and gstack, then arrives here.

- A GitHub account whose noreply address is `commit_email` in `config.yml`,
  with every other verified address listed under `connected_emails` (the
  connected-address rule in `playbook.md` is what makes contributions
  count; the scanner and the runner's attribution gate test membership in
  that list).
- Claude Code with cloud routines (claude.ai/code → routines).
- A Mac (or any always-on-ish machine) for the local scanner. Python 3 and
  git on PATH; nothing else.

## 2. Cloud routines

Create one scheduled routine per file in [`routines/`](../routines/) —
scout, check, failsafe, retro. Each file records the schedule (UTC cron +
local intent), the model, the connectors, the live trigger ID, and the
prompt to paste. The prompts are deliberately thin pointers into
`playbook.md`, which is the single source of operating truth; the retro
tunes behavior by editing the playbook, so the cloud configuration rarely
needs touching. When a routine file's prompt changes, paste it into the
trigger again.

The routine sandbox is repo-scoped (`memory/ops.md`): no `gh`, no GraphQL,
only this repo's git remote plus the built-in GitHub MCP tools. The
playbook's *Deciding green* rule exists because of this.

## 3. Local WIP scanner

The scanner publishes each local repo's name, branch, and dirty/unpushed
counts (no hostname, no paths) to `local-wip.json` so the morning scout
sees work that only exists on the laptop.

```bash
cp setup/ai.tomgreen.ivy-wip.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/ai.tomgreen.ivy-wip.plist
```

The plist runs `scripts/local-wip.sh` (a thin wrapper around
`scripts/local-wip.py`) at 08:45 and 17:45 local — just before the scout
and check routines fire. Adjust `local_wip.roots` in `config.yml` to
choose which directories are scanned. Run `./scripts/local-wip.sh` once by
hand to verify.

## 4. Nudges

Grey-day nudges use Claude Code's push notifications (verified reaching a
phone from cloud runs); Google Calendar events are the documented
fallback. Nothing to configure beyond being signed into the Claude app on
the phone.

## 5. Sanity checks

- `scripts/check.sh` locally: exits 0 on a green day, 1 on grey (needs
  `gh` authed; in the cloud sandbox it exits 2 — expected, the routines
  use the MCP verification path instead).
- After the first failsafe commit, confirm the contribution square lit;
  if not, walk the misconfig checklist in `playbook.md`.

## 6. Dispatch runner (D2)

The runner executes queued dispatch contracts (`dispatch/queue/`) on the
Mac — the only place with provider CLI auth (`claude`, `codex`). It keeps
its own clone under `~/.ivy-dispatch/` so your working checkout is never
touched, claims and finishes contracts as bot-authored commits, and leaves
`verified:` stamping to the cloud failsafe.

```
./setup/install-dispatch-runner.sh install     # launchd, every 30 min
python3 scripts/dispatch-runner.py --once --dry-run   # plan only
python3 scripts/dispatch-runner.py --once      # single real pass
./setup/install-dispatch-runner.sh status|uninstall
```

Prereqs: `claude` and `codex` CLIs authenticated on the Mac; git push auth
for github.com over https (e.g. `gh auth setup-git`); the global git
identity set to one of `config.yml` `connected_emails`, or every `build`
contract fails at the attribution gate. Models are pinned per lane in
`config.yml`.

**PATH is declared in the plist, not inherited.** launchd starts with
`/usr/bin:/bin:/usr/sbin:/sbin`, and no shell profile is read (the login shell
is zsh; launchd does not run it), so anything in `~/.local/bin` — `claude`
among them — is invisible unless named. The plist sets PATH explicitly; if a
CLI moves, update `setup/ai.tomgreen.ivy-dispatch.plist` and re-run
`install`. The runner resolves the harness binary to an absolute path before
claiming a contract, and leaves the contract `open` if it cannot, so a bad
PATH costs a log line rather than a contract.

**Updating the runner.** `main` is what executes. The launchd job's entry
point is `~/Build/ivy/scripts/dispatch-runner.py`, but after syncing its own
clone the runner execs the copy in `~/.ivy-dispatch/ivy` — so a merged change
takes effect on the next tick with no `git pull` needed.

Until 2026-09-02 it did not: the entry point only moved when a human pulled,
so a gate fix pushed at 18:37 sat unexecuted while the pre-fix code refused
four contracts at 19:06. The runner had been faithfully syncing a checkout
whose code it never ran. Treat `main` as the gate accordingly — a syntax error
there stops every tick, which is why `dispatch-runner-test.py` runs before push.

To test *local* edits you must opt out of the exec, or you will be testing
`origin/main` instead of your change:

```
IVY_RUNNER_REEXEC=1 python3 scripts/dispatch-runner.py --once --dry-run
python3 scripts/dispatch-runner-test.py    # pure parts; run before every push
```

**Skills for workers.** The worker prompt names `code-review` / `tdd` when
they are installed in the harness: `claude plugins install
mattpocock-skills` for Claude Code, `npx skills@latest add mattpocock/skills
-g` for Codex (see `AGENTIC-STACK.md`). Without them the worker still runs.
