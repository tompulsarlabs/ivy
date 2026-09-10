# Setting up an agentic coding stack

This is the setup I use: **Claude Code** and **Codex** as the agents, two skill layers shared across both — **gstack** (a virtual engineering team) and **Matt Pocock's skills** (a way of working) — and optionally **Ivy**, a set of scheduled agents that keep projects moving on their own.

It's written for a Mac, and for someone who has never used the Terminal. If a step looks obvious, do it and move on; nothing here assumes prior knowledge.

Ivy is the last and most optional part — Parts A to C are a general-purpose agentic setup that stands on its own, whether or not you ever run Ivy.

**About an hour**, most of it waiting for downloads.

---

## Before you start

| What | Notes |
|---|---|
| **A Mac** | macOS 13 (Ventura) or newer. Apple menu → *About This Mac*. |
| **A paid Claude plan** | Pro or higher. The free Claude plan does **not** include Claude Code. |
| **A paid ChatGPT plan** | Plus, Pro, Business, Edu, or Enterprise — needed to sign in to Codex. |
| **A GitHub account** | Free. [github.com](https://github.com). |
| **Your Mac password** | You'll type it once or twice. |

Both paid plans are genuine gates: the agents won't run without them. If you only want one, Claude Code alone is a complete setup — skip the Codex step.

---

## A word about the Terminal

The Terminal is a window where you type instructions instead of clicking buttons. It looks intimidating; it isn't.

**To open it:** press `⌘ + Space`, type `Terminal`, press Enter. You'll see some text and a blinking cursor — that's the *prompt*, waiting for you.

**To run a command:** copy the line, paste it in (`⌘ + V`), press **Enter**. That's the whole skill.

**Five things that otherwise trip people up:**

1. **Walls of text are normal.** Commands narrate what they're doing. That's not errors.
2. **When it asks for your password, nothing appears as you type.** No dots, no stars. Type it anyway and press Enter.
3. **"Finished" means the prompt comes back.** A fresh line with a blinking cursor means done. Otherwise, wait.
4. **One command at a time.** Don't paste the next until the prompt returns.
5. **After installing a command-line tool, quit the Terminal fully (`⌘ + Q`) and reopen it.** New commands often don't exist until you do. This single step resolves most "command not found" confusion.

---

# Part A — Foundations

## 1. Homebrew

Homebrew installs other software. Everything below depends on it.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Press Enter when prompted, and enter your Mac password when asked.

**⚠️ Don't skip this.** When it finishes it prints a short *"Next steps:"* section with **two lines** starting with `echo` and `eval`. Copy those two lines, paste them in, press Enter. Homebrew does not work until you do. (They differ between Apple Silicon and Intel Macs, which is why you copy the ones it prints rather than any written here.)

Check:

```bash
brew --version
```

## 2. Languages and tools

One command installs the lot:

```bash
brew install git node python go bun gh
```

This takes several minutes.

```bash
git --version && node --version && python3 --version && go version && bun --version && gh --version
```

Six version numbers means you're good.

<details>
<summary>What each one is</summary>

- **git** — tracks project history; how you download and update code
- **node** — runs JavaScript/TypeScript projects and much agent tooling
- **python** — needed by a great many scripts and tools
- **go** — compiles Go projects; some agent tooling ships as Go binaries
- **bun** — a fast JavaScript runtime; gstack requires it
- **gh** — GitHub's official tool, used for signing in and managing repos
</details>

## 3. Sign in to GitHub

```bash
gh auth login
```

Answer with arrow keys and Enter: **GitHub.com** → **HTTPS** → **Yes** (authenticate Git) → **Login with a web browser**. Copy the code it shows, press Enter, paste the code in the browser, approve.

This also configures Git itself, so pushing and pulling just works afterwards.

---

# Part B — The agents

## 4. Claude

**The desktop app** (normal Claude, as a Mac app): download from **[claude.ai/download](https://claude.ai/download)**, drag it to Applications, sign in.

**Claude Code** (Claude in your Terminal, able to read files, write code, and run programs):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Quit the Terminal (`⌘ + Q`), reopen, then:

```bash
claude --version
```

Log in by running `claude` — your browser opens for sign-in. Type `/exit` to leave a session. `claude doctor` diagnoses a broken install.

> Prefer Homebrew? `brew install --cask claude-code` works too, but it won't auto-update — you'd run `brew upgrade claude-code` yourself. The curl installer updates in the background.

## 5. Codex

OpenAI's terminal agent — useful in its own right, and gstack uses it for second opinions and adversarial review.

```bash
brew install --cask codex
```

Then quit and reopen the Terminal, and run:

```bash
codex
```

Choose **Sign in with ChatGPT** and complete it in the browser.

> npm alternative: `npm install -g @openai/codex`.

## 6. Cursor (optional)

Cursor is an AI code editor — a full app rather than a Terminal tool. If you want it, download it from **[cursor.com](https://cursor.com)** and install it normally.

Install it *before* the next step if you want it included automatically.

---

# Part C — The shared layer

This is the part worth understanding. There are three separate things you might want shared across tools, and each has a different answer.

## 7. Skills — one command, every agent

**[gstack](https://github.com/garrytan/gstack)** (free, MIT, from Garry Tan) turns your agents into a virtual engineering team: a CEO who rethinks the product, an eng manager, a designer who catches AI slop, a reviewer that finds real bugs, a QA lead that drives a browser, a security officer, a release engineer. All as slash commands.

The important flag is `--host auto`: it detects **every** agent tool you have installed and configures gstack for all of them in one pass — Claude Code, Codex, Cursor, and also Kiro, Factory, and OpenCode if you use those.

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/gstack && ./setup --host auto
```

**Order matters:** `auto` only configures tools that already exist, so run this *after* installing Claude Code, Codex, and Cursor. Add a new tool later? Just run `./setup --host auto` again.

Try it: run `claude`, then type `/review` or `/office-hours`. Useful ones to know: `/office-hours`, `/plan-ceo-review`, `/review`, `/qa`, `/ship`, `/investigate`, `/browse`, `/design-review`, `/learn`.

### Matt Pocock's skills — the engineering discipline

gstack gives you a team; **[Matt Pocock's skills](https://github.com/mattpocock/skills)** give you a way of working: interview before building (`/grill-with-docs`), break work into tracer-bullet tickets (`/to-tickets`), build test-first (`/tdd`), review on two axes (`/code-review`), and keep a `CONTEXT.md` glossary so the agent stops using twenty words where one will do. Ivy uses them in its routines and its workers.

Two routes, one per tool. For Claude Code the plugin is in the official marketplace and updates itself:

```bash
claude plugins install mattpocock-skills
```

For Codex (and any other agent), the installer copies the skill files in. Run it once, globally, and pick the skills you want — make sure `setup-matt-pocock-skills` is one of them:

```bash
npx skills@latest add mattpocock/skills -g
```

Don't do both for the same tool: you'd get every skill twice.

Then, in each repo you work on, run `/setup-matt-pocock-skills` once inside a session. It asks where issues live and where docs go, and writes three small files under `docs/agents/`. From then on, start each feature with `/grill-with-docs`; the glossary and decision records build themselves.

### Which one for what

gstack and Matt's skills overlap in three places, and gstack fights Ivy in two. Checked against gstack `0d1bd56` (2026-09-01, 55 skills) and mattpocock/skills v1.2.3. No skill *names* clash; some *trigger phrases* do, so name the skill you mean.

| Situation | Use | Not |
|---|---|---|
| Sharpening an idea | `/grill-with-docs` first (your vocabulary lands in `CONTEXT.md`), then gstack `/autoplan` for the CEO/eng/design critique | `/autoplan` alone: it decides for you and writes no glossary |
| Reviewing a PR at the keyboard | gstack `/review` (production bugs), then `/code-review` (does it match the spec), then `/codex` for a second model | saying "review this" and letting Claude pick |
| Reviewing a PR while you're away | an Ivy review contract (cross-family, verified by the failsafe) | gstack `/codex` (needs you present) |
| Debugging | `/diagnosing-bugs` when there is no repro yet (it refuses to theorise until one goes red); gstack `/investigate` when there is one and you want scoped edits | both at once |
| Turning a plan into work Ivy runs | `/to-tickets` → `dispatch/queue/` (attribution gate, draft PRs only, daily cap, external verification) | gstack `/spec --execute`, a second executor with none of those guardrails |
| Design and QA on a site | gstack `/design-review` (the AI-slop catcher), `/qa`, `/browse` | nothing on Matt's side covers this |
| Headless workers (`claude -p`, `codex exec`) | Matt's only: plain text, no preamble | gstack: its preamble script, onboarding gates, and `AskUserQuestion` stall a worker |
| Weekly look back | Ivy's Sunday retro for what shipped and what to tune; gstack `/retro global` for how you worked across Claude, Codex, and Gemini sessions | gstack `/retro` inside the ivy repo: it writes `.context/retros/*.json` there |
| Shipping in the ivy repo | commit and PR by hand or `/implement` | gstack `/ship`: it bumps a `VERSION` file and rewrites `CHANGELOG.md`, which Ivy's retro owns |
| Memory | Ivy's `memory/` wiki for Ivy; gstack `/learn` and gbrain for other repos if you want session-level history | gbrain or `/learn` pointed at ivy: a memory the agent writes and then obeys is exactly what Ivy's immutable rule forbids |

**Where the gstack section goes.** gstack asks for a `## gstack` block (35 skill names plus "use `/browse` for all browsing") in each project's `CLAUDE.md`. Put it in `~/.claude/CLAUDE.md` instead, once. It then applies to every repo on the Mac and never loads into Ivy's cloud routines, which cannot run gstack anyway. To move an existing one:

```bash
# append gstack's own snippet to your global file, then delete the block from any repo CLAUDE.md
sed -n '/^## gstack$/,/^$/p' ~/.claude/skills/gstack/README.md >> ~/.claude/CLAUDE.md
```

**Duplicates.** If Matt's plugin is installed on the Mac, sessions inside `ivy` also see the vendored copy under `.claude/skills/`. Claude Code should resolve same-name skills with project precedence; check with gstack's `gstack-context-bill` (it measures the always-on cost of an installed skill tree). If it shows each twice, drop the plugin and use `npx skills@latest add mattpocock/skills -g` instead, which puts the same files where gstack lives.

## 8. Instructions — one file every tool reads

**[AGENTS.md](https://agents.md)** is the open standard (stewarded by the Linux Foundation's Agentic AI Foundation) for telling coding agents about a project: how to build it, how to test it, house conventions. It's read by Codex, Cursor, Factory, OpenCode, Zed, Warp, VS Code, GitHub Copilot, Gemini CLI, Windsurf, Jules, Aider, Goose, Devin, Junie, Amp and more.

Claude Code reads `CLAUDE.md` instead. So write your instructions **once** in `AGENTS.md`, and make `CLAUDE.md` a one-line pointer to it:

```bash
echo '@AGENTS.md' > CLAUDE.md
```

That `@` is a Claude Code import — it pulls the other file in. One source of truth, every tool reads it.

The exception is a repo only Claude Code ever opens. Ivy is one: its routines run as Claude Code in the cloud and its Codex workers operate in *other* repos, so `CLAUDE.md` there carries the content itself (navigation pointers plus the agent-skills block) and there is no `AGENTS.md` to point at.

The same trick works for your personal, global preferences, which apply to every project:

- Claude Code: `~/.claude/CLAUDE.md`
- Codex: `~/.codex/AGENTS.md`

## 9. MCP servers — added per tool, honestly

MCP servers give agents new abilities (databases, browsers, third-party services). **There is no shared config file** — each product keeps its own. But the commands mirror each other, so adding a server twice is quick:

```bash
# Claude Code
claude mcp add --transport http <name> <url>
claude mcp add <name> -e API_KEY=xxx -- npx some-mcp-server

# Codex
codex mcp add <name> --url <url>
codex mcp add <name> --env API_KEY=xxx -- npx some-mcp-server
```

`claude mcp list` and `codex mcp list` show what's configured. Cursor manages its own in its settings UI (`~/.cursor/mcp.json`).

---

# Part D — Ivy (optional, advanced)

**Ivy is the repo you're reading this in.** It's an agentic DevOps loop: scheduled agents that read their own memory, find work worth doing across your repos, nudge you when a day is slipping, and write down what they learn. Three routines run daily — a morning scout, an evening check, a late failsafe — plus a Sunday retro, a local scanner that reports work-in-progress that only exists on your laptop, and a dispatch runner that executes queued work on the Mac and reports its own heartbeat back into the repo.

**Two things to know before you start.** It's **experimental**. And it needs **Claude Code cloud routines** (claude.ai/code → routines), which come with a paid Claude plan.

**Permission required.** Ivy's original materials are proprietary; commercial
reuse requires prior written permission. See [LICENSE](../LICENSE). The setup
steps below are for authorised deployments.

A fork gives you the frame — the routines, the playbook, the structure — and none of anyone else's access. This repo carries its author's commit email, a watchlist of their repositories, and their journal and memory; cloned verbatim, you'd get a bot diligently tracking someone else's projects. With the required permission, create your deployment:

```bash
gh repo fork tompulsarlabs/ivy --clone --fork-name ivy
cd ivy
```

Then swap the identity before running anything:

1. **`config.yml`** — set `commit_email` to *your* GitHub noreply address (this is what makes contributions register) and list every address verified on your GitHub account under `connected_emails`; the local scanner and the runner's attribution gate both test membership in that list, and the global `git config user.email` on the Mac must be one of them. Replace the repo watchlist with your own and point `local_wip.roots` at your own project folders.
2. **`setup/*.plist`** — rename the launchd job labels and the files themselves from `ai.tomgreen.ivy-*` to your own reverse-domain label, and update every path inside: the script path, `HOME`, and the `PATH` line, which must include wherever `claude` lives (`~/.local/bin` by default). launchd inherits no shell profile, so a PATH that is right in your Terminal is not right here.
3. **`journal/`, `memory/`, `state.json`** — these are the previous owner's history. Read them to understand how the system thinks, then clear them out for your own run.

With that done, follow **[`SETUP.md`](SETUP.md)** for the mechanics: creating the four cloud routines, installing the local scanner as a launchd job, and the optional dispatch runner (which executes queued work on your Mac and needs both `claude` and `codex` authenticated — which, by this point, they are).

Start by reading [`OVERVIEW.md`](../OVERVIEW.md) and [`playbook.md`](../playbook.md). The playbook is the operating truth; the routines are thin pointers into it.

---

## Keeping it current

```bash
brew update && brew upgrade                       # languages and tools
cd ~/.claude/skills/gstack && git pull && ./setup --host auto   # gstack, all hosts
npx skills@latest update -g                       # Matt Pocock's skills for Codex (the Claude plugin updates itself)
cd ~/Build/ivy && git pull                        # Ivy: the local scanner runs from this checkout
```

Claude Code updates itself in the background. Codex installed via Homebrew needs `brew upgrade --cask codex`. Ivy's dispatch runner needs no pull: it execs the synced copy of itself on every tick. A changed `setup/*.plist` needs `./setup/install-dispatch-runner.sh install` (or the scanner's `launchctl` reload) before launchd sees it.

## If something goes wrong

| What you see | Fix |
|---|---|
| `command not found: brew` | The two `echo`/`eval` lines from step 1 weren't run. Scroll up, find them, paste them. |
| `command not found: claude` / `codex` | Quit the Terminal fully (`⌘ + Q`) and reopen. |
| gstack didn't set up one of your tools | That tool wasn't installed yet. Install it, then re-run `./setup --host auto`. |
| Claude Code won't log in | Confirm your Claude plan is Pro or higher — the free tier excludes Claude Code. Then `claude doctor`. |
| Ivy contracts sit `open` all day; `dispatch/runner-status.json` shows `harness.claude: false` | launchd can't see `claude`. Fix the `PATH` line in `setup/ai.tomgreen.ivy-dispatch.plist`, then `./setup/install-dispatch-runner.sh install`. |
| No `dispatch/runner-status.json` commit at all inside 09:15–21:00 | The job isn't ticking: `./setup/install-dispatch-runner.sh status` (loaded?), and check the Mac wasn't asleep. |
| A `build` contract fails with `exit: attribution` | The Mac's `git config --global user.email` isn't in `config.yml` `connected_emails`. Set it to one that is. |
| Anything else | Paste the error into Claude Code and ask what it means. This works more often than it has any right to. |

## Glossary

- **Terminal** — the typing window
- **Command** — one instruction you run
- **Repository (repo)** — a project folder with its full history
- **Clone / fork** — download a copy / make your own copy you control
- **CLI** — a tool you use by typing rather than clicking
- **MCP** — the standard that lets agents plug into external tools and data
- **Agent** — an AI that doesn't just answer, but reads, writes, and runs things
