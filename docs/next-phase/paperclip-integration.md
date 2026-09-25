# Paperclip integration slice

10 September 2026. Tom approved the proposed isolated fixture integration with
“I'm aligned, let's go.” This implements that slice on the existing acceptance
branch and draft PR #20. It does not migrate production dispatch or Cockpit.

## What runs

The pilot uses the published `paperclipai@2026.831.1` process adapter and HTTP
API. A fixed Python worker emits a transport fixture. Ivy reads the output
captured by Paperclip, binds it to the company, issue, executor and run, seals
the observation, and assesses it with the existing citation checker plus an
exact fixture-output check. The supervisor relays the executor's completion
claim under the executor's local Paperclip identity. Paperclip routes it into
its configured review stage. Ivy publishes its assessment as a different
reviewer identity; only a fixture pass requests `done`.

This is a supervisor-driven integration, not an autonomous agent demonstration.
The reviewer has a no-op process run to establish its Paperclip run context;
the Python supervisor performs the assessment. Local Paperclip agent keys are
minted for the campaign, kept in memory and revoked during cleanup. They are
not model-provider API keys. No model provider or host subscription login is
configured or required.

`paperclip_bridge.py` contains the loopback-only client, exclusive attempt
reservation, immutable observation storage, assessment and reviewer delivery.
`paperclip_pilot.py` is the explicit runnable campaign. It creates only its own
test company, agents and issues on the supplied local instance. Scheduled
heartbeats are disabled; demand wakeups are enabled only around explicit
dispatches. Workers and reviewers are paused after each case.

## Controls and observed results

| Case | Required outcome | Observed |
| --- | --- | --- |
| Valid fixture | Completion claim enters review; separate reviewer approves | Done after review |
| False completion | An empty finding list cannot pass merely because the process succeeded | Failed assessment; stays in review |
| Tampered delivery | Recomputed hashes cannot replace the previously sealed observation | Rejected; stays in review; original retained |
| Duplicate delivery | Reopening the attempt store does not dispatch another process | One worker process; repeated review reconciled |
| Interrupted execution | Stop the worker; refuse a later completion claim | Worker PID absent, claim refused with HTTP 409, no acceptance |

The portable observations and development history are in
[`evidence/paperclip-integration-20260910/report.json`](evidence/paperclip-integration-20260910/report.json).
The 20 new deterministic tests cover malformed output, ownership, stale runs,
concurrent reservations, restart, tampering, self-review, review-stage changes
and recovery after a lost write response. The full suite has 102 tests.

### Cancellation finding

The release can create an automatic retry record after cancellation, even with
scheduled heartbeats disabled and demand wakeups subsequently disabled. The
pilot's stop operation therefore cancels the run **and pauses that worker**.
The successful cancellation control retained two run records but observed only
one worker process. The retry record was cancelled without a process PID.

Run termination and issue status are separate. The cancelled issue was still
`in_progress` at the recorded observation; later cleanup can mark it blocked.
Neither is a completion pass. Earlier development checks incorrectly required
`blocked` immediately, and then incorrectly equated run-record count with
process count. Those failed campaigns are retained, not reclassified as passes.
This is an adoption constraint to test further, not a hard lifecycle guarantee.

## Reproduce

Use a separate temporary install and Paperclip data directory. Pin the package:

```sh
npm install --prefix /tmp/ivy-paperclip-install --ignore-scripts --no-audit --no-fund paperclipai@2026.831.1
```

On this Mac, disabling install scripts left embedded PostgreSQL's library
symlinks absent. The package's `@embedded-postgres/darwin-arm64/scripts/hydrate-symlinks.js`
was read, its manifest paths were checked to stay inside that package, and only
that package-local script was run. The first failed startup log remains in the
private evidence directory. Other platforms need their own dependency check.

Start Paperclip from the empty pilot directory with an allowlisted environment:
`PATH`, an explicit `PAPERCLIP_HOME`, `PORT=3197`, `HOST=127.0.0.1`,
`HEARTBEAT_SCHEDULER_ENABLED=false` and `DO_NOT_TRACK=1`. Invoke the installed CLI
with `onboard --yes --no-install-service`. Quickstart needs no LLM configuration.
Disable telemetry and update checks in this instance's config. Do not use
`test-drive`, Codex adapters or adapter login probes for this fixture campaign.

From the Ivy acceptance worktree:

```sh
python3 -B -m ivy_acceptance.paperclip_pilot \
  --url http://127.0.0.1:3197 --state /absolute/new/campaign-directory
python3 -B -m unittest discover -s tests -v
```

The state directory must not exist. This is an explicit new development
campaign, not a retry against an overwritten store. Every attempted campaign
must remain in the development history. An uncertain dispatch reservation
cannot be reused. The historical Docker store is never opened by this code.

## Limits and next decision

- Fixed-fixture transport success establishes no model quality, independent
  semantic assessment, accepted benchmark, buyer value or Milestone A pass.
- The Paperclip instance is separate; the processes are not OS-isolated from
  the operator. Local supervisor and database integrity are trusted. Digests
  detect changes against that trusted record and are not signed attestations.
- The code uses the released process API, not the newer Runner native bundle
  format reviewed at upstream commit `2a05b5e`. No native compatibility claim.
- Sequential duplicate review delivery and lost-response reconciliation are
  covered. Concurrent reviewer writes, server restart during delivery and a
  general distributed exactly-once guarantee remain unverified.
- Cancellation plus pause stopped the one observed fixture process. Descendant
  process trees, interrupted builds and hard whole-lifecycle limits remain
  unverified. No Docker command or renewal of old runtime grants occurred.
- Provider authentication, request/cost enforcement, subscription quota routing
  and real-agent execution remain deferred. No paid integration is authorized.

The next adoption decision should use one representative Ivy contract and its
existing independent check, with explicit stop/retry policy. Keep one dispatcher
responsible for that contract. This slice supports continuing the Paperclip
evaluation; it does not justify a production migration yet.
