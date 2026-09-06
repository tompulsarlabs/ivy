# Ivy acceptance planning and runtime evidence

Python 3.11+, standard library only. Current status and remaining work live in
[the runtime handoff](../docs/next-phase/runtime-handoff.md); architectural contracts
live in [system-design.md](../docs/next-phase/system-design.md).

The terminal build at `eaa9b36` recorded 59 passing deterministic tests and verified
real credential-free worker completion, cancellation and deadline shutdown. Both
Python 3.11/3.14 CI jobs passed. No evaluated model or judge call occurred, and the
real-agent milestone remains incomplete. The evidence-and-resource iteration is
specified in [cost-quality-design.md](../docs/next-phase/cost-quality-design.md);
its proposed commands are not implemented merely because the design exists.

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
failure. `verify-probe` currently verifies artifact integrity and reports execution
state; a zero exit or integrity result alone does not establish probe success.
The new design addresses that distinction explicitly.

Runtime launch and grant commands consume the recorded, explicitly authorized
session allowance. They do not obtain approval or reset history. Follow the current
handoff for that allowance; an offline evidence read needs no fresh runtime grant.

## Components

| Module | Existing responsibility |
|---|---|
| `canonical.py` | Strict JSON, canonical digests and explicit file snapshots |
| `planning.py` | Instruction-only preview, separated inputs and paired primary slots |
| `budget.py`, `storage.py` | Reservation limits, atomic persistence, locking and retained history |
| `materialization.py` | Recompile plans and verify bytes before packing selected visible inputs |
| `docker_probe.py` | Fixed-probe image preparation, preflight, capture and container termination |
| `probe_cli.py` | Probe commands, recovery and artifact integrity checks |
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
launches. The next offline reporting iteration does not repair or erase that limit.

Production dispatch and Cockpit are separate from this package. Their future
integration must consume an authoritative assessed result rather than infer success
from a worker claim, CLI exit or artifact hash.
