# Issue tracker: dispatch contracts

Ivy's issues are dispatch contracts: one markdown file per unit of work under
`dispatch/queue/`, executed by the Mac runner and verified by the cloud
failsafe. Specs and decision tickets that are not yet executable work live
under `.scratch/<effort>/`, per the local-markdown convention.

## Conventions

- A contract is `dispatch/queue/<YYYY-MM-DD>-<repo-slug>-<kind>-<NN>.md`
  with the frontmatter and the three body sections in `dispatch/DESIGN.md`
  §2: `## Task`, `## Definition of done`, `## Verification (cloud-checkable)`.
- `created_by: tom` for anything published from an interactive session;
  `scout` is reserved for the routine.
- Routing: `review` → `workhorse`, `pool` pinned to the family that did not
  write the code (the playbook's Scout section is authoritative, including
  when to pin `frontier`); `build` → `frontier` (design-heavy) or `workhorse`
  (mechanical); `chore` → `workhorse`. `budget.wall_minutes` 20 to 45.
  `expires` 48 hours out unless the task says otherwise.
- Dependencies: `blocked_by: [id, id]`, an inline list. The runner skips a
  contract until every id is in `dispatch/done/`; the lint refuses ids that
  are not contracts.
- The daily cap (`config.yml` `dispatch.daily_cap`, counted by `created`
  date) applies to contracts published from a session too. Check
  `dispatch/queue/` and `dispatch/done/` for today's count first.
- `scripts/dispatch-lint.sh` must pass before committing. Commit
  bot-authored as `dispatch: open <id>`.
- A build contract's Task says which branch to start from and states that
  the worker opens a **draft** PR and never pushes to the default branch.
  Its Verification names a check the cloud can run with the GitHub MCP tools
  (a draft PR by `tompulsarlabs` referencing the contract id, a file present
  on `main` of ivy).

## When a skill says "publish to the issue tracker"

- Tickets from `/to-tickets`: one contract per ticket, in dependency order,
  each later one carrying `blocked_by` with the ids of the tickets that gate
  it. `ready-for-agent` means `state: open`. Keep the ticket's "What to
  build" as the `## Task`, its acceptance criteria as the `## Definition of
  done`, and add a `## Verification` the cloud can run.
- A spec from `/to-spec`: `.scratch/<feature-slug>/spec.md`. The contracts
  that implement it cite that path in `## Task`.
- Anything that is a question rather than work (a `/wayfinder` decision
  ticket): `.scratch/<effort>/issues/NN-<slug>.md`, never a contract, because
  nothing executes it.

## When a skill says "fetch the relevant ticket"

Read the contract file in `dispatch/queue/`, `dispatch/done/`, or
`dispatch/failed/`, and for a finished review, `dispatch/reports/<id>.md`.

## Wayfinding operations

Rooted at `.scratch/<effort>/`, exactly as the local-markdown convention:

- **Map**: `.scratch/<effort>/map.md` (Notes / Decisions-so-far / Fog).
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`, numbered from
  `01`, with `Type:` (`research`/`prototype`/`grilling`/`task`), `Status:`
  (`claimed`/`resolved`), and `Blocked by: NN, NN` lines near the top.
- **Frontier**: open, unblocked, unclaimed files; lowest number first.
- **Claim**: set `Status: claimed` and save before any work.
- **Resolve**: append the answer under `## Answer`, set `Status: resolved`,
  then add a pointer (gist + link) to the map's Decisions-so-far.

When the map clears, `/to-spec` collapses it into a spec and `/to-tickets`
publishes the contracts.

## PRs as a request surface

Off. The scout already surfaces every open PR org-wide as a candidate each
morning; `/triage` is not a flow here.
