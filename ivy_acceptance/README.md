# Ivy acceptance planning and runtime evidence

Python 3.11+, standard library only. Current status and remaining work live in
[the runtime handoff](../docs/next-phase/runtime-handoff.md); architectural contracts
live in [system-design.md](../docs/next-phase/system-design.md).

The offline evidence/resource build adds explicit fixed-probe assessment and a
JSON + Markdown report. The [portable recorded report](../docs/next-phase/evidence/offline-report-20260906/report.md)
reassesses historical completion, cancellation and deadline receipts. The three
expected controls pass; only completion passes natural completion. All 82 local
deterministic tests pass, including the [twelve named eval cases](../evals/evidence-quality.json).
These are infrastructure checks. No evaluated model or judge call occurred, and
real-agent acceptance remains incomplete.

## Existing commands

```sh
python3 -B -m ivy_acceptance plan examples/acceptance/preview.json
python3 -B -m unittest discover -s tests -v
python3 -B -m ivy_acceptance --help
```

`plan` reads explicit input trees and prints a detached content-bound preview. It
performs no subprocess, network call or file write; `-B` suppresses Python bytecode
writes. Every preview has `execution_ready: false`. Editing that flag cannot
provide owner approval or enable an agent run.

`probe` executes a fixed Python infrastructure test in a dedicated Docker context;
it does not execute an AI model. `--preflight-only` checks setup without reserving
an attempt. `recover-probe` confirms shutdown of an attempt-owned container after
failure. `verify-probe` verifies artifact integrity only. `assess-probe` evaluates the
recognized fixed program against a declared expectation. `probe` now returns that
assessment and uses its exit status: 0 pass, 1 observed failure, 2 unverified/invalid.
Ambiguous cancellation options are rejected before creating a store or adapter.

Runtime launch and grant commands consume the recorded, explicitly authorized
session allowance. They do not obtain approval or reset history. Follow the current
handoff for that allowance; an offline evidence read needs no fresh runtime grant.

## Offline assessment and report

```sh
python3 -B -m ivy_acceptance assess-probe /path/to/attempt --expect completion
python3 -B -m ivy_acceptance assess-probe /path/to/attempt --expect cancellation
python3 -B -m ivy_acceptance report /path/to/manifest.json --output /path/to/new-report
```

The report manifest is versioned and rejects undeclared fields. Relative input
paths resolve against the manifest directory. A minimal manifest is:

```json
{
  "schema_version": 1,
  "receipts": [{"id": "completion", "directory": "store/attempt", "expect": "completion"}],
  "resources": [],
  "sources": {},
  "expected_resource_scopes": null
}
```

Use `deadline` for a recorded deadline control. The report command returns 0 for a
successful render even if a contained assessment fails; inspect `status_counts` or
use `assess-probe` for a gate. It writes `report.json`, `report.md`, and a detached
SHA-256 of the **canonical JSON object** in `report.sha256`. It refuses an existing
output directory or overlap with selected evidence stores. Rendering needs no
Docker, model, network access or new runtime grant.

Optional resource records follow [the versioned contract](../docs/next-phase/cost-quality-design.md#resource-record-and-aggregation).
Every metric is explicit; unknown values are null, with a reason. `sources` maps
safe identifiers to JSON observation files, and each resource record binds one by
its raw file hash. Reported capture, command, reservation and engineering durations
also require matching underlying observations; file integrity alone is insufficient.
Declare extra expected scopes as `{"id": "worker", "stage": "worker"}` entries
alongside each selected receipt's setup scope. Missing scopes stay unknown. One
exclusive record per scope replaces its default record; inclusive totals are rejected.
Reported and estimated subtotals remain separate. This version makes no billing
savings claim and cannot calculate cost per accepted agent task.

The portable example contains allowlisted assessments and hashes, not private raw
Docker records or host paths. Its engineering observation is the historical design
checkpoint (11,700 allocated seconds); the current cumulative build debit lives in
[resource-ledger.json](../docs/next-phase/resource-ledger.json).

## Components

| Module | Existing responsibility |
|---|---|
| `canonical.py` | Strict JSON, canonical digests and explicit file snapshots |
| `planning.py` | Instruction-only preview, separated inputs and paired primary slots |
| `budget.py`, `storage.py` | Reservation limits, atomic persistence, locking and retained history |
| `materialization.py` | Recompile plans and verify bytes before packing selected visible inputs |
| `docker_probe.py` | Fixed-probe image preparation, preflight, capture and container termination |
| `probe_cli.py` | Probe commands, recovery and artifact integrity checks |
| `evidence_io.py`, `probe_assessment.py` | Bounded strict evidence readers and explicit fixed-probe outcomes |
| `resources.py`, `reporting.py` | Exclusive resource coverage and reproducible allowlisted reports |
| `grading.py` | Citation existence/range controls; semantic assessment stays unverified |
| `ports.py` | Execution contracts; real model adapter remains unavailable |

The example contains two synthetic draft cases, two illustrative instruction versions
and two repetitions. Four further cases, benchmark-owner approval, a real harness,
independent semantic assessment and a model comparison report remain unfinished.

## Evidence boundaries

Worker-visible files and hidden grading labels are separated. The actual probe uses
no host mounts, network or credentials, a non-root user and a read-only root. Captures
and lifecycle inspection remain supervisor-owned. A separate worktree alone is not
an isolation boundary.

Hash verification assumes a trusted local supervisor. It detects changed artifacts;
it does not establish signed authority, semantic correctness or a tamper-proof host.
Missing model/effort/usage observations remain unavailable. Infrastructure probes
cannot fill primary model-evaluation slots or establish cost per accepted agent task.

The current command deadlines and shutdown grace do not establish a hard end-to-end
limit on filesystem work or daemon-side image builds. Unknown shutdown blocks later
launches. Offline reporting does not repair or erase that limit.

Production dispatch and Cockpit are separate from this package. Their future
integration must consume an authoritative assessed result rather than infer success
from a worker claim, CLI exit or artifact hash.
