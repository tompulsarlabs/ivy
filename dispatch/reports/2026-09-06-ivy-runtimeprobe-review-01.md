# Report — 2026-09-06-ivy-runtimeprobe-review-01

Produced by the frontier/openai lane, 4.7 wall-minutes.

# PR #20 review — bounded runtime probe

Reviewed current head `eaa9b3642a49a5bbe31406f51ebce014f79f235a` against PR #19’s design.

## Findings

### [P1] A failed or no-op probe is accepted as a successful CLI invocation

`ivy_acceptance/probe_cli.py:80` reports `"integrity": "verified"` without requiring a completed execution, complete capture, confirmed termination, or expected probe observations. `ivy_acceptance/probe_cli.py:135` subsequently returns normally for execution-error, canceled, and timed-out outcomes, so the top-level CLI exits zero.

The weakness is demonstrated directly at `tests/test_probe_receipt_controls.py:100`: a one-line synthetic event unrelated to the probe is accepted as verified by the test beginning at `tests/test_probe_receipt_controls.py:115`. Consequently, empty or semantically meaningless work can satisfy the verifier as long as its files are internally hash-consistent. An automation routine using command success or the `"verified"` field could mistake this for successful work without an external check.

Proposed fix: separate artifact-integrity verification from probe success. Parse and validate the captured JSONL; bind the fixed probe version/digest; require the expected fixture hashes, both denied-write observations, UID, credential absence, instruction inventory, zero exit status, complete capture, and confirmed termination. Return an explicit `probe_passed: false` and a nonzero CLI exit for failed, partial, or no-op executions. Add empty-stream, irrelevant-stream, nonzero-exit, and missing-observation tests.

### [P1] The probe is not hard-bounded across its complete lifecycle

`ivy_acceptance/probe_cli.py:116` performs plan compilation and materialization before any operation deadline exists. Input reads at `ivy_acceptance/materialization.py:35` and archive construction at `ivy_acceptance/docker_probe.py:215` have no size limit or interruptible deadline.

More importantly, `ivy_acceptance/docker_probe.py:221` applies a timeout only to the Docker client running a daemon-side build. If the client times out or is interrupted after submission, `ivy_acceptance/docker_probe.py:166` explicitly records the build as unconfirmed but has no builder identity with which to cancel or confirm it. The command may return and future attempts correctly remain blocked, but the daemon workload itself is not proven terminated. This does not meet PR #19’s termination requirement or support an unqualified “bounded runtime probe” claim.

Proposed fix: enforce input file/count/byte limits before materialization and include preparation in an outer wall-clock supervisor. Prefer preparing and verifying a pinned derived image before reserving a runtime attempt. If builds remain attempt-scoped, use a uniquely owned, inspectable build mechanism with explicit cancellation and shutdown confirmation, and add a live interrupted-build test. Until then, describe the implementation as reservation-bounded and container-run-bounded, not lifecycle-bounded.

### [P2] The implemented probe does not perform PR #19’s Milestone-A harness run

`ivy_acceptance/docker_probe.py:24` installs and executes a fixed Python filesystem probe rather than the selected real review-agent harness. It only lists instruction filenames and never consumes the neutral review task or instruction contents as an agent. The “known-bad output” at `ivy_acceptance/probe_cli.py:136` is manufactured by the supervisor rather than produced through the runtime under test.

PR #19 requires one neutral case through the actual harness, captured runtime metadata, and a known-bad agent output failing assessment. The implementation is useful infrastructure validation, but it cannot satisfy that requirement. The code honestly acknowledges this at `ivy_acceptance/probe_cli.py:144`, so this is a specification-completeness gap rather than a false benchmark-pass claim.

Proposed fix: retain this fixed script as an explicitly named isolation self-test or preflight, then implement the selected authenticated `HarnessAdapter` for Milestone A. Feed it the neutral task and instruction bundle, capture actual harness events and effective metadata, and run the bad-output control through the same assessment boundary.

## Sound sections

- Container-run cancellation is fail-closed: `ivy_acceptance/docker_probe.py:254` inspects ownership, kills when needed, reinspects state, and refuses to infer shutdown when Docker is unreachable. `ivy_acceptance/storage.py:258` blocks later reservations while termination remains unconfirmed.
- The container isolation request is consistent with PR #19’s boundary: `ivy_acceptance/docker_probe.py:235` uses no mounts, no network, a read-only root, non-root UID, dropped capabilities, and no-new-privileges, then checks the effective settings.
- No scheduled routine or dispatch verification path is directly modified. The added workflow has read-only repository permissions at `.github/workflows/acceptance-scaffold.yml:18` and runs only deterministic tests and the read-only planner at `.github/workflows/acceptance-scaffold.yml:31`. Model-quality fields remain fail-closed at `ivy_acceptance/grading.py:26`, and the probe reports Milestone A as not passed. The unsafe generic CLI success described in Finding 1 should nevertheless be fixed before any routine integration.
- The current GitHub checks pass on Python 3.11 and 3.14. They do not run Docker and therefore do not resolve the runtime findings above.

## Delivery note

The requested report was not written to `dispatch/reports/2026-09-06-ivy-runtimeprobe-review-01.md`, committed, or pushed because the contract’s final rule explicitly requires read-only operation and prohibits all three actions. The checkout remained unchanged.
