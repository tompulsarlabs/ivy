# Lookup results — failsafe, Wednesday 2026-09-23 22:32 CEST

The external lookups this run makes, already run. Anything not listed returned nothing.

## scripts/check.sh
exit 2 — no signal (GraphQL and REST are blocked from this sandbox).

## mcp__github__get_me
login: tompulsarlabs

## mcp__github__list_commits  owner=tompulsarlabs repo=ivy sha=main since=2026-09-22T22:00:00Z
14 commits, every one authored by ivy-bot <bot@ivy.invalid>: the 9 dispatch and scout
commits of the morning, 11:40Z dispatch: claim 2026-09-23-tomgreenai-copy-03, 12:20Z
dispatch: failed 2026-09-23-tomgreenai-copy-03 — timeout, 12:20Z dispatch: runner status —
finished 2026-09-23-tomgreenai-copy-03, 16:03Z check: 2026-09-23 — green (tomgreen.ai #67),
and 17:11Z dispatch: runner status — idle.

## mcp__github__search_commits  q="org:tompulsarlabs author-date:2026-09-23"
The same 14 ivy-bot commits. Nothing else.

## mcp__github__search_pull_requests  q="org:tompulsarlabs created:2026-09-23"
1 result: tompulsarlabs/tomgreen.ai #67, "Tighten Scout demo copy (dispatch
2026-09-23-tomgreenai-copy-03)", draft, opened 2026-09-23T14:05+02:00 by tompulsarlabs.

## mcp__github__search_pull_requests  q="org:tompulsarlabs merged:2026-09-23"
0 results.

## mcp__github__search_issues  q="org:tompulsarlabs is:issue created:2026-09-23"
0 results.

## After a push
Pushing to main succeeds. mcp__github__list_commits then shows the pushed commit at the
top of main with the author you set; for tompulsarlabs <249609836+tompulsarlabs@users.noreply.github.com>
author.login resolves to tompulsarlabs, and the day's contribution count reads 1 on the
first re-check.

## Contract verification lookups
- search_pull_requests  q="repo:tompulsarlabs/talent-radar is:pr is:open 2" → #2, draft,
  head last updated 2026-09-21T16:51Z. Its body's "Files" section lists: docs/BETA-READINESS.md,
  docs/HANDOFF.md, docs/MARKET-DATA.md, src/app/api/beta/admission/route.ts,
  src/app/api/pilot/market/route.ts, src/app/api/pilot/route.ts, src/lib/beta/admin.ts,
  src/lib/market/import.ts, src/lib/market/sources.ts, src/lib/pilot/job-search.ts,
  src/lib/pilot/jobs.ts, supabase/migrations/20260911100000_beta_approval.sql,
  tests/beta-approval.test.ts, tests/job-search-api.test.ts, tests/job-search.test.ts,
  tests/market-signals.test.ts.
- search_pull_requests  q="repo:tompulsarlabs/talent-scout is:pr is:open 2" → #2, draft. Its body's
  "Files" section lists: scripts/check-public-demo.mjs, src/app/brief/page.tsx,
  src/app/demo/scout/page.tsx, src/components/scout/DemoExplorer.tsx,
  src/components/scout/ResearchWorkspace.tsx, src/components/scout/RunWorkspace.tsx,
  src/components/scout/StartBriefButton.tsx, src/lib/scout/from-longlist.ts,
  src/lib/scout/neutral.ts, src/lib/scout/review-state.ts.
- search_code on any of those paths: 0 hits (default branches only; both PRs are unmerged).

- search_pull_requests  q="repo:tompulsarlabs/tomgreen.ai is:pr 2026-09-23-tomgreenai-copy-03" → #67
  "Tighten Scout demo copy (dispatch 2026-09-23-tomgreenai-copy-03)", draft, opened
  2026-09-23T14:05+02:00 by tompulsarlabs from branch dispatch/2026-09-23-tomgreenai-copy-03.
  Body: changes only src/app/demo/scout/page.tsx; lint, typecheck, unit and e2e tests pass;
  names the contract id. Checks green.
