---
subject: tompulsarlabs/pixel-perfect-showcase-8458
type: repo
updated: 2026-09-08
---

# pixel-perfect-showcase-8458

**Private.** Local alias `ivy-cockpit` — a Codex-authored cockpit UI for
operating Ivy's own dispatch queue. First seen in the 2026-09-08 watchlist
sync, created 2026-09-07 [cite:2026-09-08]. Two stacked draft PRs opened
09-07, both still open.

## PR #1 and #2

**PR #1** ("Connect cockpit actions to the Ivy queue") replaces an earlier
adapter that pointed at an undefined endpoint with a real, unconditional
write path to `tompulsarlabs/ivy` `main` (`queue-github.server.ts`,
`PATCH /git/refs/heads/main`), gated on three env vars. Reviewed 2026-09-08
by `2026-09-08-ivycockpit-queueconnect-review-01`: server-side operator
and repo allowlists, bounded queue policy, atomic writes and idempotent
retries all confirmed sound; several UI-copy findings (dialog claims
immediate runner release / repository state changes that the server does
not actually perform) and one unauthenticated endpoint running a
privileged full-repo read (`getCommandCapability`, no auth middleware).
**verified: true** (PR-body corroboration; repo outside this session's
direct access [[ops]]) [cite:2026-09-08].

**PR #2** ("Harden shared-credential access and document Ivy privacy
findings"), stacked on #1: adds JWT middleware and an exact operator
allowlist before Notion/GitHub credentialed calls, stops raw Notion error
bodies from reaching a client or log sink, rejects redirects, patches four
vulnerable transitive dependencies. Reviewed 2026-09-08 by
`2026-09-08-ivycockpit-credentialharden-review-01`. **verified: true**
(same corroboration standard) [cite:2026-09-08].

## Finding: the "write credential remains disabled" claim does not hold in code

Both PR bodies call the shared GitHub write credential a release blocker
that "must remain disabled" — because it can also modify the repository
the Mac's runner executes unattended. The 2026-09-08 review found this is
a *documentation* stance, not a code property: there is one token
(`IVY_GITHUB_TOKEN`) serving both reads and writes, no kill switch or
separate write token anywhere in `src/`, and the shipped setup page
(`src/routes/system.tsx:106-108`) still instructs the owner to grant
**Contents read/write**. A successful *read* also arms the write UI
(`getCommandCapability` returns `available: true` with all actions
enabled off a read-only `snapshot()`). The moment an owner follows the
product's own setup instructions, the write path is live for every
allowlisted operator [cite:2026-09-08].

**Why this matters for Ivy specifically:** this repo's own product writes
to Ivy's dispatch queue and could write to Ivy `main`. An unconfirmed
"disabled" claim here is a standing risk to the system reviewing it, not
an ordinary product bug — worth weighting above the usual review-finding
bar until a default-deny gate or split read/write token actually lands.

## Changelog

- 2026-09-08 — page created from journals 2026-09-07→08, the two review
  contracts, and the F1 credential finding.
