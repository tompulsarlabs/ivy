# Report — 2026-09-07-tomgreenai-activitymatrix-review-01

Produced by the workhorse/anthropic lane, 10.5 wall-minutes.

# PR #41 — "Preview a 30-day activity matrix in the Lab header"

**Target reviewed:** PR head `29ea466` (`codex/lab-recent-activity`, merged as `c51e56c`). All line references are at `29ea466`; `src/app/globals.css` has since diverged on `main`, so cite the PR head for the CSS.

**Scope:** the three adversarial axes in the contract — (1) the rolling 30-day window against the Berlin date boundary and DST, (2) graceful degradation of the hourly refresh and the claimed link fallback, (3) whether the reduced-motion path actually disables the animation.

**Environment note:** network egress was blocked in this checkout (`gh`, `git fetch`, `curl`, `WebFetch` all denied). Everything below is derived from the committed tree, the vendored Next 16.3.2 docs in `node_modules/next/dist/docs/`, and git history. Items that could not be network-verified are listed at the end.

---

## Findings

### 1. HIGH — The window requires *today's* cell, so it collapses to "Activity unavailable" every night across the Berlin/UTC boundary

`src/lib/data/github.ts:68`
(with `src/components/recent-build-activity.tsx:15`, `src/lib/data/ivy.ts:22`)

`recentContributionDays` walks 30 UTC days ending at `today` and returns `null` if *any* day — including the final one — is absent:

```ts
// github.ts:65-70
for (let offset = 29; offset >= 0; offset--) {
  const date = new Date(end.getTime() - offset * 86_400_000).toISOString().slice(0, 10);
  const day = byDate.get(date);
  if (!day) return null;
  recent.push(day);
}
```

`today` comes from `ivyOperatingDate()` (`ivy.ts:22`), which is pinned to `Europe/Berlin` (`ivy.ts:19`) — UTC+1 in winter, UTC+2 in summer. The data comes from GitHub's anonymous contribution calendar (`github.ts:44`), whose newest `data-date` cell is keyed to GitHub's own day boundary (UTC for unauthenticated requests — see *Unverified* below).

**Failure scenario:** it is 00:20 on 8 June in Berlin (CEST). `ivyOperatingDate()` returns `2026-06-08`. UTC is still 22:20 on `2026-06-07`, so the calendar's newest cell is `2026-06-07`. `byDate.get("2026-06-08")` is `undefined` → `github.ts:68` returns `null` → `recent-build-activity.tsx:15` yields `null` → the entire matrix is dropped (`:20-22`) and the caption reads "Activity unavailable" (`:25`). This is not a partial degradation: 29 days of perfectly good data are discarded because the 30th is one clock-hour early.

The window then stays broken until an hourly regeneration lands *after* UTC midnight, so the blackout is roughly **00:00–02:00 Berlin in winter and 00:00–03:00 in summer, every single night**. The DST effect is on the *width* of that blackout (it jumps by an hour on the spring-forward Sunday and shrinks back in autumn), not on the arithmetic itself — see the confirmations section.

Note that even under the most favourable premise (GitHub's calendar in Berlin time), the contract "the 30th day must be today" is still fragile: any refresh landing between Berlin midnight and GitHub publishing the new cell produces the same collapse. The bug is the strictness of the terminal-day requirement, not only the timezone.

The existing tests bless the behaviour rather than catch it — `src/lib/data/github.test.ts:67` asserts `recentContributionDays(days, "2026-03-01")` is `null` for data ending 45 days earlier, which is correct for genuinely stale data but is the same code path that fires for a one-hour lag.

**Proposed fix** — anchor the window's end to the newest available day within a small tolerance, keeping the "missing data is not zero" guarantee for interior gaps and genuinely stale feeds:

```ts
export function recentContributionDays(
  days: ContributionDay[],
  today: string,
  toleranceDays = 1,
): ContributionDay[] | null {
  const endOfToday = new Date(`${today}T00:00:00Z`);
  if (!Number.isFinite(endOfToday.getTime()) ||
      endOfToday.toISOString().slice(0, 10) !== today) return null;
  const byDate = new Map(days.map((day) => [day.date, day]));
  const iso = (ms: number) => new Date(ms).toISOString().slice(0, 10);

  // The upstream calendar rolls over on its own clock; accept a window that
  // ends up to toleranceDays behind Berlin's today rather than dropping 29
  // good days for one missing one.
  let end = endOfToday.getTime();
  for (let back = 0; ; back++) {
    if (back > toleranceDays) return null;
    if (byDate.has(iso(endOfToday.getTime() - back * 86_400_000))) {
      end = endOfToday.getTime() - back * 86_400_000;
      break;
    }
  }

  const recent: ContributionDay[] = [];
  for (let offset = 29; offset >= 0; offset--) {
    const day = byDate.get(iso(end - offset * 86_400_000));
    if (!day) return null; // an interior gap is still bad data
    recent.push(day);
  }
  return recent;
}
```

The visible caption at `recent-build-activity.tsx:25` already prints the real first and last dates, and the aria-label at `:21` already names them, so a window ending yesterday remains truthful without any copy change. Add a test asserting a window that ends one day behind `today` still returns 30 days, and that two days behind returns `null`.

---

### 2. MEDIUM-HIGH — The whole block, including the fallback link, sits inside a `Suspense` boundary; the committed content baseline shows the resolved output was never captured

`src/app/building/page.tsx:110-118`, `e2e/content-baseline.json:370-424`

The link fallback does exist and is rendered on both branches (`recent-build-activity.tsx:27`, outside the `days ? … : null` conditional at `:20-22`), so on the success *and* the failure path the user gets "Activity unavailable — View on GitHub ↗". That part of the claim holds. But it is inside the boundary, and the committed baseline says that output never reached a JS-disabled render.

The component always emits exactly one of two caption strings at `recent-build-activity.tsx:25`: a date range (`"17 dec – 15 jan"`) or `"activity unavailable"`. `e2e/content-guard.mjs` captures `header`/`main`/`footer` `innerText` with `javaScriptEnabled: false` (`content-guard.mjs:33`, `:39-43`). The `/building` baseline array spans `content-baseline.json:370-424` and contains **neither** string. The only line this PR added is `"last 30 days"` (`:396`) — which is emitted by *both* the real component (`recent-build-activity.tsx:18`) and the Suspense fallback (`building/page.tsx:113`), so it cannot distinguish them. (`"view on github ↗"` at `:418` predates this PR: the whole-file diff is one insertion and one deletion, and the `/building` page already carried a GitHub link on its "This site — design, code and change history" card.)

I confirmed via `git log 32b0e2c..29ea466 -- e2e/content-baseline.json` that the baseline was last touched at the PR head commit itself, where `recent-build-activity.tsx` is exactly as shipped — i.e. the caption row existed when the baseline was written. So one of two things is true, and both are defects:

- the baseline was regenerated with `--update` and the JS-disabled render genuinely showed only the fallback (`building/page.tsx:112-114`), meaning a no-JS visitor sees a loading state and the "View on GitHub" escape hatch is **not reachable without JavaScript**; or
- the baseline was hand-edited rather than regenerated, in which case it does not describe the shipped page at all.

Either way the regression guard is worthless here: `content-guard.mjs:66-73` only fails on *lost* baseline lines, so the single protected string `"last 30 days"` survives even if the matrix, the date range and the link all stop rendering. There is no other coverage — grepping the nine e2e specs at `29ea466` for `contribution`, `30 days` or `activity` returns nothing.

**Proposed fix** (robust under either hypothesis):
1. Move the `Last 30 days` label and the GitHub link out of the async component into the static shell in `building/page.tsx`, leaving only the matrix and its date range inside `RecentBuildActivity`. The escape hatch is then part of the page regardless of streaming or data state.
2. Drop the `Suspense` wrapper. `next.config.ts` at `29ea466` sets no `cacheComponents`, and `/building` uses no request-time APIs, so the route is statically prerendered and the fallback is dead code that only creates the divergence above.
3. Regenerate the baseline with `node e2e/content-guard.mjs --update` and add a Playwright assertion on `/building` that the block renders either a `\d+ \w{3} – \d+ \w{3}` range or the literal `Activity unavailable`, plus a visible link to `github.com/tompulsarlabs`.

---

### 3. MEDIUM — A single transient GitHub failure degrades the block for up to a full hour, with no last-good fallback

`src/lib/data/github.ts:42-55`

`getContributions` correctly swallows every failure and returns `null` (`:47`, `:50`), and `AbortSignal.timeout(5000)` (`:46`) bounds a hang — the page can never break or stall on GitHub, which is the right shape. But because the caller has no memory of the previous good window, one 5-second timeout during an hourly regeneration bakes "Activity unavailable" into the statically regenerated page and pins it there until the next revalidation (`:45`, `revalidate: 3600`). Compounded with finding #1, the block is unavailable more often than the underlying data justifies.

**Failure scenario:** GitHub returns a 503 for 20 seconds at 14:00; the 14:00 regeneration hits it; visitors from 14:00 to 15:00 see "Activity unavailable" even though a complete, correct 30-day window was rendered a minute earlier.

**Proposed fix:** persist the last successfully parsed window (Next `unstable_cache` with a long TTL, or a `revalidate: false` second cache entry written on success) and fall back to it when `getContributions()` returns `null`, labelling the caption with the real end date so nothing stale is presented as current — the same honesty rule `isStale` already applies in `ivy.ts:139-145`. If that is more machinery than the feature warrants, at minimum shorten `revalidate` on the failure path so a transient error is retried in minutes rather than an hour.

---

### 4. LOW — `signal` opts this fetch out of Next's per-render memoization

`src/lib/data/github.ts:46`

`node_modules/next/dist/docs/01-app/03-api-reference/04-functions/fetch.md:90` states that passing an `AbortController` signal is the documented way to *opt out* of request memoization. There is one caller today (`recent-build-activity.tsx:14`; `ProofStrip` at `proof-strip.tsx:104` takes `contributions` as a prop and is not itself mounted anywhere at `29ea466`), so there is no live impact — but a second server component calling `getContributions()` in the same render pass will now issue a second real request to GitHub instead of sharing one. Worth a one-line comment at `:46` recording that trade-off, or wrapping the call in `React.cache()` to restore de-duplication independently of the signal.

### 5. LOW — The fallback URL duplicates the username constant

`src/components/recent-build-activity.tsx:5` vs `src/lib/data/github.ts:11`

`PROFILE = "https://github.com/tompulsarlabs"` and `USER = "tompulsarlabs"` are independent literals. If the account is ever renamed, the data source and the "reachable link fallback" drift apart silently — and the drift is invisible precisely in the failure state, where the link is the only thing left. Export `USER` (or a `PROFILE_URL` derived from it) from `github.ts` and build the href from it.

### 6. LOW — `aria-label` on a role-less `<div>` is not exposed

`src/components/recent-build-activity.tsx:17`, `src/app/building/page.tsx:112`

ARIA prohibits naming elements with the generic role, so neither "Recent build activity" nor "Loading recent build activity" is announced by most screen readers. The label on the fallback is also not in a live region, so nothing announces the transition. Use `<section aria-label="Recent build activity">` for the wrapper (the inner `role="img"` at `contribution-graph.tsx:40` already carries the real description), and either drop the fallback label or give the boundary `aria-live="polite"`.

### 7. LOW — `min-height` under-reserves the block's real height

`src/app/globals.css:1745`

`.lab-build-activity { min-height: 13rem }` reserves 208px, but the resolved block is ~300px (label + `mt-6` 24px + a 7×27px grid with 6×7px gaps = 231px + `gap-3` 12px + caption). If the fallback is ever shown (see finding #2), the content below shifts by ~90px when it resolves. Set the reservation from the grid's actual height, or remove it once the `Suspense` boundary goes.

---

## Confirmed sound

These were probed specifically and I found no defect.

- **Window arithmetic is DST-immune.** `github.ts:61-69` anchors on `new Date(\`${today}T00:00:00Z\`)` and steps by exact `86_400_000` ms increments, reading dates back out via `toISOString().slice(0, 10)`. UTC has no DST, so every step lands precisely on a UTC midnight; the 29 March and 25 October Berlin transitions cannot produce a duplicated, skipped or shifted day. Contrast this with local-time `setDate()` arithmetic, which would have been wrong — the implementation chose correctly. The result is always exactly 30 distinct consecutive calendar dates.
- **Date validation ordering is correct.** `github.ts:62` checks `Number.isFinite(end.getTime())` *before* calling `end.toISOString()`. For an invalid input such as `"2026-13-01"` the finite check short-circuits, so `toISOString()` never throws a `RangeError`. The round-trip comparison also correctly rejects rolled-over dates like `"2026-02-30"`, which `github.test.ts:71-73` covers.
- **Weekday rows are computed on the calendar date, not a local instant.** `contribution-graph.tsx:30` uses `getUTCDay()` on a `T00:00:00Z` date, so a cell's row never drifts by one across a DST boundary or on a server in a non-UTC zone. The mid-week leading pad at `:31-34` puts the first partial week in its true weekday rows.
- **Displayed dates match the data.** `recent-build-activity.tsx:8-10` formats with `timeZone: "UTC"` against a `T00:00:00Z` instant, so the caption cannot render an off-by-one date on a server in a negative-offset zone.
- **The reduced-motion path fully disables the animation — it does not merely slow it.** `globals.css:1792-1795` applies `animation: none` to both `.contribution-cell[data-active="true"]::before` (the detached motes, `:1761-1769`) and `::after` (the staggered edge slivers, `:1770-1779`). The `animation` shorthand also resets `animation-delay`, so the `var(--spark-delay)` stagger declared at `:1759`, `:1768` and `:1778` is neutralised rather than left dangling. Those two pseudo-elements are the only animated things the PR introduces — there is no `transition` or second `animation` on `.contribution-cell`, `.contribution-week`, `.contribution-month` or `.contribution-energy` — and the media block is the last rule in the file at PR head with equal specificity to the base rules, so cascade order resolves in its favour. What remains is a static sliver at `opacity: 0.55` and static motes at `opacity: 0.65`; that is decoration, not motion, and is the correct resting treatment. The site also has no competing JS-driven motion toggle — every reduced-motion decision in `globals.css` is a media query — so this is consistent with the rest of the codebase.
- **The failure path cannot break or hang the page.** `getContributions` (`github.ts:42-55`) has a total `try`/`catch`, a non-OK guard, a 5s abort, and `parseContributions` returns `null` on markup drift rather than throwing. Every `days[0]`/`days[29]` access at `recent-build-activity.tsx:21` and `:25` is inside a `days ?` guard, and `recentContributionDays` guarantees exactly 30 entries when non-null, so there is no index-out-of-range risk.
- **The link fallback exists on the failure path.** `recent-build-activity.tsx:27` sits outside the `days ?` conditional, so "View on GitHub ↗" renders whether or not the matrix does, with `min-h-11` giving it a 44px touch target. Its URL is internally consistent: the `tompulsarlabs` slug matches `USER` (`github.ts:11`) and the repository's own origin remote (`github.com/tompulsarlabs/tomgreen.ai`), so the account demonstrably exists. See findings #2 and #5 for the reachability caveats that *are* real.

---

## Unverified

- **HTTP reachability of `https://github.com/tompulsarlabs`** — network egress was blocked in this checkout. Verified only by static consistency with `USER` and the git remote.
- **That GitHub's anonymous `/users/<user>/contributions` calendar uses UTC day boundaries** — this is the premise that sets the *width* of the nightly blackout in finding #1. I could not fetch the endpoint to confirm the newest `data-date`. Finding #1 does not depend on it: any reckoning other than `Europe/Berlin`, or any lag between Berlin midnight and GitHub publishing the new cell, produces the same collapse, because the code requires the terminal day to be present.
- **Whether `e2e/content-baseline.json` was regenerated or hand-edited at `29ea466`** — git cannot distinguish the two. Finding #2 states both branches; the proposed fix covers both.
