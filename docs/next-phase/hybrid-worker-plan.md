# Always-on Paperclip, Mac execution first

22 September 2026. Tom approved planning and building this direction after the
$40/month Railway compute proposal. Hosting scope: one private board and its
database, with a $30 alert and $40 compute shutdown limit before tax. This does
not authorize model APIs, cloud execution, an extra paid network service, or
production queue migration. Provision within the existing proposal once Tom
connects the hosting account; do not ask him to reapprove individual build tests.

## Architecture

```mermaid
flowchart TD
    Tom[Tom: desk or travelling] --> Board[Paperclip: one hosted board and database]
    Board --> Mac[Dedicated Mac worker over a private connection]
    Mac --> Git[Git branches, PRs and source evidence]
    Git --> Review[Ivy acceptance checks and human decisions]
    Review --> Board
    Board -. Later, separately funded .-> Cloud[Optional cloud worker]
```

Paperclip owns task state and, after a controlled cutover, dispatch for the
selected task class. A Mac worker executes jobs; it is not a second Paperclip
server or a second business queue. Existing production Ivy dispatch continues
unchanged until that cutover. Never assign the same task to both dispatchers.

Use Paperclip's native **SSH environment driver** for the first connection.
The pinned 2026.916.1 release already supports remote workspaces, host-key
verification and a stored private-key secret reference. These controls are
experimental. Reuse them and prove the actual Mac behavior before adding custom
transport or automatic fallback.

## Implementation stages

| Stage | Deliverable | Evidence needed to advance |
| --- | --- | --- |
| 1. Private board | Guarded pinned image, persistent app/database storage, one owner, signup locked, backups | Local real-image auth/restart/restore checks, then provider HTTPS and billing checks |
| 2. Mac connection | Dedicated OS account, private network route, scoped SSH identity, isolated workspaces | Exact host identity, workspace ownership, harmless remote process and reconnect/stop tests |
| 3. One real task class | Explicitly assigned Mac agent, versioned contract, independent acceptance | Complete one representative task; retain failure/disconnect evidence; stop old dispatcher for that class |
| Later, optional | Cloud worker for periods without a reachable Mac | Separate cost/auth approval, compatible harness, no duplicate execution during handoff |

Stage 1 now has executable startup checks and a real local rehearsal. Stage 2
has a tested configuration renderer; the Mac is **not connected**. No new SSH
service, Mac account, network tunnel or persistent worker has been installed.

## Mac connection contract

- A dedicated Mac account owns its own workspaces. Never give the hosted board
  Tom's normal SSH key or access to `/Users/tom/Build/ivy`, his home or existing
  provider authentication. A workspace path is not itself an OS sandbox.
- Reach that account through a private route, for example a Tailscale network.
  Railway-to-Mac connectivity and any network service plan must be verified;
  there is no assumption that the prepared Railway container can already reach
  a tailnet address. Do not expose the Mac's SSH port on the public internet.
- Generate a new SSH identity for this connection. Keep its private key in
  Paperclip's encrypted secret store, use a pinned secret version, and verify
  the Mac's ed25519 host-key fingerprint through an independent local channel.
- The account's authorized key must disable forwarding and agent forwarding;
  account permissions limit its filesystem access. Enforce connection limits
  through private-network policy. This access setup precedes connection testing.
- Model authentication is established separately for the dedicated worker.
  Do not copy Tom's existing subscription login. The first connection test runs
  a harmless fixed command with no model/provider credentials.

The renderer uses the exact released environment fields and reads only the
explicit public host-key file supplied by the operator:

```sh
python3 -B -m ivy_acceptance.paperclip_mac \
  --host WORKER.TAILNET.ts.net \
  --username ivyworker \
  --workspace /Users/ivyworker/workspaces \
  --secret-id UUID_FROM_PAPERCLIP_SECRET_STORE \
  --secret-version 1 \
  --known-hosts-file /absolute/path/to/verified-worker-known-hosts \
  --output /absolute/new/mac-environment.json
```

Replace the uppercase placeholders; use a lowercase actual host. Output creation
is exclusive. It is a prepared environment payload, not an API call or proof of
reachability. The renderer rejects public/loopback destinations, Tom/root accounts,
workspace paths outside the dedicated account, wildcard or malformed host pins,
raw private keys, and unpinned secret versions. It cannot verify account ownership
or resolve a hostname without the later live connection check.

## Disconnect and travel behavior

- Mac reachable: explicitly assigned new jobs can run on it after validation.
- Mac unavailable before dispatch: leave work queued or blocked and show the
  reason. Do not silently run it on the board container or buy cloud capacity.
- Connection lost during work: treat execution as uncertain. Do not equate an
  SSH client exit or an expired heartbeat with remote process termination.
- Before retry: reconnect, inspect the recorded process/workspace and resulting
  artifacts, establish whether it completed or stopped, then permit a new run.
  Stop uncertain agents to prevent recovery loops while that is unresolved.
- Travelling with a Mac left awake: the same worker can remain available after
  the private route is verified. With the Mac asleep, the board remains usable
  for planning and review while execution waits.

These are rollout requirements, not a claim that automatic availability routing
or remote shutdown is already implemented. Native behavior must be tested with
an explicit interrupted-run case before unattended use. Cloud fallback remains
off in this first implementation.

## Cost and operations

Hosting the board has a continuous baseline regardless of where the worker runs.
Local execution avoids adding cloud build/worker load to that baseline. Record
actual RAM/CPU/storage measurements after deployment and compare projected
monthly usage against the $30 alert. A brief idle-container sample is not a
monthly bill forecast. The $40 hard limit sacrifices availability at exhaustion.

Current status and all failures live in [the existing handoff](runtime-handoff.md).
Source references: [Paperclip environments](https://docs.paperclip.ing/experimental/environments/),
[pinned SSH transport](https://github.com/paperclipai/paperclip/blob/d554c4789ed3930f8a53ac9fdf6503b3187097da/packages/adapter-utils/src/ssh.ts),
[pinned config schema](https://github.com/paperclipai/paperclip/blob/d554c4789ed3930f8a53ac9fdf6503b3187097da/server/src/services/environment-config.ts).
