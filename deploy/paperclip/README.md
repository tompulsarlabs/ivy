# Private Paperclip board — release candidate

22 September 2026. **Built and rehearsed locally; not hosted yet.** Tom approved
planning and building the always-on board/Mac execution direction after the
$30 alert/$40 hosting-cap proposal. Railway account sign-in is pending. Real
image checks passed for owner bootstrap, access refusal, task persistence and
backup restoration. Connecting autonomous Ivy workers is a separate rollout.

## Proposed deployment

- Railway, one Paperclip service and one PostgreSQL 17 service in the same EU
  region, private database networking, one app replica and persistent volumes.
- Use this directory as the build context and `railway.json` as its config.
  Do not connect automatic deployments from the experimental acceptance branch.
  The Dockerfile wraps the official prebuilt image without copying Ivy code,
  credentials or the host home directory into it.
- Image: `ghcr.io/paperclipai/paperclip:2026.916.1`, pinned by OCI index digest
  `sha256:a02ac35ac41df911af477422ea0e781cf41d2b2c600c66f0a5ac9d8c63f52c2c`.
  Public registry metadata includes Linux amd64 and arm64 images.
- Upstream release source: `d554c4789ed3930f8a53ac9fdf6503b3187097da`.
  Source inspection verified the entrypoint, auth configuration and health route.
  Local execution evidence is recorded in the release rehearsal linked below.
- Preserve the upstream entrypoint: it uses tini, repairs volume ownership and
  runs the server as the unprivileged node user. The wrapper command runs the
  startup guard, then execs the pinned upstream Node command. Do not replace
  either with a provider-generated start command.
- Mount an app volume at `/paperclip`; retain the separately provisioned database
  volume. Disable sleeping and automatic image updates. No high-availability claim.

The existing Ivy fixture bridge is pinned to **2026.831.1** and loopback access.
Its five prior controls do not validate this newer hosted image or authenticated
remote integration. Do not relax that version/auth boundary merely to get a pass.

## Approved hosting scope, before tax

Expected small-instance usage: **$20–40/month**, an engineering estimate, not a
provider quote or measured bill. Railway charges $10/GB-month RAM, $20/vCPU-month
CPU usage, $0.15/GB-month volume storage and $0.05/GB egress. Its $5 Hobby or $20
Pro minimum counts toward usage; it is not an extra fee on top of all usage.
Backups and additional retained data must fit the proposed allowance too.

Use a dedicated workspace with a $30 compute alert and $40 compute hard
limit. Verify plan eligibility, checkout total and tax before provisioning; stop
if the selected offering exceeds that scope. These provider settings are not
yet configured and must precede ongoing workloads.
Railway shuts down workloads at the compute limit; availability is sacrificed
when the limit is reached. Its limit is workspace-wide, so do not apply it to a
workspace containing Tom's other services. Provider billing enforcement is not
an application-level guarantee about final tax or adjustments.

No Railway Agent, model API or paid sandbox service is required for the board.
Do not enable those as part of hosting. A Mac connection configuration renderer
is built; the connection and authentication are unverified. Until connected,
the hosted board does not execute Ivy's local jobs.
Even after connection, Mac execution depends on the Mac being awake and connected.

Cheaper alternative: budget approximately €10–15/month before VAT for a small
Hetzner VM, backups and IP allowance, subject to capacity and selected SKU.
CX23 is €5.49 and CX33 €8.49 before extras; VM administration, patching, TLS and
backup operations become our responsibility. Railway is proposed to reduce that
operational work. No new domain purchase is needed if using a provider hostname.

Sources checked 2026-09-22:
[Railway pricing](https://docs.railway.com/pricing),
[cost controls](https://docs.railway.com/pricing/cost-control),
[Hetzner current prices](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/),
[Hetzner backup charges](https://docs.hetzner.com/cloud/billing/faq/).

## Runtime configuration

The Dockerfile sets authenticated/public exposure (internet address, login
required), port 3100, app home and disabled scheduled heartbeats. Configure the
following through the provider's secret/variable UI, never in Git or chat:

| Variable | Value or source |
| --- | --- |
| `DATABASE_URL` | Private-network reference to the PostgreSQL service |
| `BETTER_AUTH_SECRET` | Fresh cryptographically random app secret |
| `PAPERCLIP_SECRETS_MASTER_KEY` | Fresh 32-byte encryption key encoded as base64 |
| `PAPERCLIP_AUTH_PUBLIC_BASE_URL` | Exact HTTPS URL assigned to this app |
| `PAPERCLIP_ALLOWED_HOSTNAMES` | That hostname; optionally add `healthcheck.railway.app`, no wildcard |
| `PAPERCLIP_AUTH_DISABLE_SIGN_UP` | Enable after Tom's owner account is bootstrapped |

App secrets identify/encrypt this deployment. They are not model API keys.
Retain encryption and authentication material in protected recovery storage.
The guard refuses missing volumes, unsafe modes, conflicting origins and known
model credential variables. It creates a mode-0600 config for upstream CLI use
inside the app volume, including this deployment's database connection string.
It preserves existing config and refuses a changed database URL until the
operator reconciles that config. It mirrors the canonical auth URL into
`PAPERCLIP_PUBLIC_URL` so the CSRF guard uses the same origin behind a proxy.
These checks do not disable all model execution paths: keep the board empty of
active agents and credentials.

Run the first-owner bootstrap command privately in the service container:

```sh
node --import ./server/node_modules/tsx/dist/loader.mjs cli/src/index.ts auth bootstrap-ceo --base-url https://YOUR-APP-HOSTNAME
```

Use its claim URL to establish Tom's account; never publish a claim
URL in a PR, log excerpt or task reply. Verify signup and ownership rules before
placing any private work in the board. Disable further signup after bootstrap;
check that an unrelated browser session cannot join or see company data.

Keep automatic heartbeats off, create no model-backed agents and enable no
provider connectors in this first release. Disabling the timer alone does not
disable demand wakeups or every recovery path. Do not import active agents or
production dispatch records. Create an empty Ivy company and a manual test task.

## Release checks to execute on the provisioned service

1. Confirm the deployed digest, effective authenticated/public mode, intended
   hostname and persistent volume mounts. Health returns HTTP 200; a successful
   health request alone does not prove access control.
2. Tom signs in as owner. An anonymous browser cannot read company/task data;
   a second unauthorised account cannot join. Confirm signup is disabled after
   owner bootstrap, with access checks repeated after a restart.
3. Create/edit a manual test task, restart the service, and verify the same task,
   owner identity and attachment remain. Confirm no agent runs were created.
4. Configure daily database and app-data backups. Restore a matching database,
   attachments and encryption material into a separate private environment;
   verify task readability there. Retain the recovery procedure and timestamps.
5. Check actual resource use and billing limits. Record the HTTPS URL, image
   digest, release time and results in the existing runtime handoff.

No public production URL can be supplied until these checks have run. If a check
fails, stop promotion and retain logs/evidence. For first-install failure keep
the persisted data and debug the release. For later upgrade failure, restore a
tested matching pre-upgrade database/data backup with the prior image; do not
assume rolling back an image reverses database migrations.

## Subsequent Ivy integration

Replay one completed contract in an isolated company using independent source
and CI evidence, then one fresh task with explicit acceptance checks. Prove
duplicate delivery and cancel-plus-pause behavior on this exact version before
cutover. For any task class moved to Paperclip, stop the old scheduler for that
class first: there must be one dispatch authority. Preserve Git contracts and
artifact references; do not retroactively award acceptance to historical claims.

Upstream references:
[release](https://github.com/paperclipai/paperclip/releases/tag/v2026.916.1),
[pinned Dockerfile](https://github.com/paperclipai/paperclip/blob/d554c4789ed3930f8a53ac9fdf6503b3187097da/Dockerfile),
[deployment modes](https://docs.paperclip.ing/reference/deploy/deployment-modes/),
[Railway config](https://docs.railway.com/config-as-code/reference).

## Recorded local rehearsal

[Portable evidence](../../docs/next-phase/evidence/paperclip-board-build-20260922.json)
retains all failures and the final successful run. The final image passed
internal HTTP checks for owner bootstrap, anonymous/unrelated-user refusal,
signup lock, manual task persistence after restart, and restoration of database
and app data into new isolated volumes with the owner session and task intact.
No agent runs were created. All nine release/restore containers are stopped.

The Mac loopback forward timed out, so requests ran inside the isolated Docker
network. Public HTTPS, interactive browser login, uploaded attachments and
scheduled provider backups remain unverified. One post-start sample showed
743.1 MiB app RAM and 62.78 MiB database RAM; it does not establish steady-state
usage or monthly cost.

[The hybrid worker plan](../../docs/next-phase/hybrid-worker-plan.md) describes
the native SSH connection, disconnect behavior and gates before real execution.
