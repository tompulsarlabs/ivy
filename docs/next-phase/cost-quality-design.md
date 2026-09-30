# Offline evidence and resource report

6 September 2026. This is the bounded system-development iteration Tom requested
after the runtime checkpoint at `eaa9b36`. It is internal engineering, with no
customer validation or evaluated model result. Terminal context was reconciled:
the continued acceptance work is the clean, pushed `codex/ivy-acceptance-scaffold`
branch and draft PR #20. Main and the separate Cockpit work are not build targets.

The current [runtime handoff](runtime-handoff.md) remains the evidence authority.
Its 9,900 allocated engineering seconds, eight consumed runtime attempts and
Milestone-A status are retained. This iteration adds separately recorded design
effort and at most **60 minutes for one implementation lane**, including verification
and closeout; it does not reset an earlier allowance. Recommend Astra High for this
bounded build as engineering judgment, not a measured cost optimum. No live
containers, models, judges, API calls or authentication work are part of this build.

## Deliverable and boundary

Implement a strict offline assessment of saved fixed-probe evidence, a small
versioned resource record, and a JSON plus Markdown report. Replay the three existing
completion, cancellation and deadline receipts from the private runtime store.
Write new derived artifacts to a separate selected directory; leave originals and
their ledger byte-for-byte unchanged. Synthetic controls are labeled separately.

Use the existing canonical encoding and hash helpers. Suggested seams are
`probe_assessment.py`, `resources.py`, `reporting.py` and small CLI additions. Do not
refactor the runtime lifecycle to complete this slice. The first line of every
report says **Infrastructure proof — no model evaluation**. It reports probe
assertions, shutdown controls, evidence gaps and resource visibility, never an agent
benchmark pass. The closed instruction-only planning schema stays unchanged.

## One assessment with separate facts

`probe-assessment` schema version 1 binds the receipt file hash, its bound capture
hash, recognized probe digest, assessment-policy digest and requested control
expectation. It contains these separate fields; no field substitutes for another:

| Field | Allowed states and interpretation |
|---|---|
| `artifact_integrity` | `verified`, `invalid`, `unverified`; hashes and record relationships only |
| `execution_state` | Recorded terminal state, or `unknown`; preserve cancellation/timeout |
| `program_identity` | `recognized`, `unknown`, `missing`; exact bytes, not a claimed version name |
| `assertions` | Criterion ID, `pass`/`fail`/`unverified`, bounded evidence references and reason code |
| `probe_assertions_status` | Known assertion failure wins; otherwise any missing requirement is unverified |
| `natural_completion_status` | Independent `pass`/`fail`/`unverified` for a complete successful fixed probe |
| `control_expectation` | Explicit `completion`, `cancellation` or `deadline`; supplied by the operator |
| `control_status` | `pass`/`fail`/`unverified` against that expectation |
| `benchmark_status` | Always `unavailable`; `model_evaluation` is always false |

Invalid artifact bindings prohibit a pass and make affected observations unverified;
do not interpret tampered bytes as trustworthy failure evidence. With valid bindings,
a known failed required assertion produces `fail` even if another requirement is
missing. Otherwise missing, malformed or unsupported required evidence produces
`unverified`. Preserve each reason and coverage count. An overall pass requires all
requirements of the declared control; a worker-written score is never an input.

Completion requires recognized program and matching inputs, all fixed-probe
assertions passing, `execution_state: completed`, complete capture, one final
`stream_closed` with exit zero, independently recorded container exit zero and
confirmed stopped state. Cancellation/deadline controls require the corresponding
supervisor `stop_requested` reason, matching terminal receipt state, observed probe
readiness, all required fixed-probe assertions passing, and confirmed stopped
container. A partial capture is expected for those controls. Their passing control
status never changes `execution_state` or fills primary coverage. When an interruption
is established, `natural_completion_status` is `fail` with reason `interrupted`,
even if the expected interruption control passes; absent termination evidence makes
it `unverified`. A known contradictory exit/control event fails the relevant
criterion; absent shutdown evidence is unverified rather than inferred from client exit.

## Recognize the actual fixed probe and its evidence

The current program in `docker_probe.py` has SHA-256
`ff5d328717984c218110e0815d2bda951321983a853140da119b8c5e352fdd4e`.
Register those exact bytes as `fixed-filesystem-probe-v1` with a fixed assessment
policy. A test checks that the recognized bytes and digest agree. A new program
digest requires an explicit new recognition entry and policy; no automatic fallback
to the newest program is allowed. Future receipt writers may add an explicit
program descriptor, but that producer change is optional for this offline slice.

The three historical receipts already bind `preparation.json`, whose `visible_files`
contains `probe.py`, the fixture path/hash map and instruction path/hash map. Support
this exact legacy shape through a pure normalization function: derive expectations
from the recorded map, not today's fixtures or command configuration. Bind the
normalization version in the assessment. An explicit program descriptor, when
present, must agree with that recorded hash. Missing required fields remain
unverified; an unknown receipt/program/policy version cannot pass. Never rewrite a
legacy receipt to manufacture provenance.

Check the existing preparation, image-input, image-build, prepared-container and
stop-container relationships before using observations. Require matching runtime ID,
derived image, ownership labels and binding digest; the fixed entrypoint and command
must select the recognized probe and the expected `complete`/`wait` mode. The local
trusted supervisor recorded these facts; hashes are not signatures against its owner.

The fixed-probe assertions are deliberately narrow:

| Assertion | Evidence and pass rule |
|---|---|
| Selected fixture bytes | Exactly one `fixture_read`; exact path/hash equality with recorded `fixture/` entries |
| Fixture write did not succeed | Exactly one event for `/worker/fixture/prohibited-write`, result `OSError`, plus supervisor-observed read-only root |
| Evidence-path write did not succeed | Exactly one event for `/ivy-evidence/prohibited-write`, result `FileNotFoundError`, plus zero host mounts |
| Non-root execution | `probe_ready.uid` is integer 65534 and recorded container user is `65534:65534` |
| Checked credential variables absent | `credential_environment_present` is false; this program checks only `OPENAI_API_KEY` and `CODEX_API_KEY` |
| Visible instruction inventory | Exact top-level names derived from recorded `instructions/` paths match `probe_ready`; this does not show an agent read their contents |
| Effective container isolation | Saved inspection has read-only root, no mounts, network `none`, no privilege, dropped `ALL` capabilities and `no-new-privileges=true` |

`write_succeeded` is a known failure. A different exception class is unverified,
with its observed class retained; it is not silently treated as permission denial.
Even the recognized classes prove only that the prescribed write did not succeed.
Do not claim monitored syscall coverage, complete credential absence, instruction
following, semantic review quality or daemon-build shutdown from these checks.

Require exactly one readiness record and the expected set of observation events.
Contradictory or duplicate events cannot pass. Unknown worker events or missing
observations leave the affected evidence unverified. Fixed-program observations
combined with supervisor metadata are assessed values, not worker self-scores.

## Bounded stream decoding

Inspect regular local files only and reject symlinks or escaping artifact paths.
Apply bounds while reading, before allocating the whole stream: 4 MiB encoded
capture, 16,384 supervisor records, 128 KiB per supervisor line, and 1 MiB combined
decoded stdout/stderr. Bound individual decoded worker JSON lines at 128 KiB and
JSON nesting at 16. These are parser limits, not new runtime execution limits.
Apply a 4 MiB limit to each metadata/resource JSON file as well. A report manifest
selects at most 32 receipts and 256 exclusive resource records; reject excess input
before traversing the bundle. These small explicit bounds keep offline parsing
predictable without introducing a scheduler or a streaming service.

Validate strict UTF-8 JSON, duplicate keys, finite numeric values, exact supported
record shapes, consecutive sequence numbers beginning at 1 and nondecreasing finite
nonnegative supervisor elapsed time. Decode base64 strictly. Reassemble each channel
in sequence order before decoding UTF-8 and splitting worker JSONL: chunks can split
a multibyte character or one JSON object and can contain several complete lines.
Never merge stderr into stdout. Bound and report stderr; it cannot supply probe
observations. Reject invalid base64, unsupported shapes, trailing partial worker
JSON and limit overruns as incomplete evidence with explicit reasons. No repair,
replacement characters, speculative JSON completion or success from an empty stream.

## Resource record and aggregation

Use a separate `resource-measurement` schema version 1, not new fields in the frozen
comparison configuration. The small record has `id`, `scope_id`, nullable
`parent_scope_id`, `stage`, `accounting: exclusive`, `source_ref`, `source_sha256`,
nullable attempt/receipt bindings, and a closed `metrics` object. Stages are `setup`,
`coordinator`, `worker`, `grader`, `engineering`; infrastructure probes use `setup`.
Parent links describe relationships, not permission to sum parent-inclusive bills.

Each metric is `{value, unit, basis, reason}`. Basis is `reported`, `estimated` or
`unknown`; unknown has null value and a reason, while numeric zero requires an
identified source. Reject booleans as numbers, negatives, NaN/infinity, unknown
units, duplicate IDs, missing bindings and mixed currencies in one money total.
Allowed metrics are request count, input/output/cached-input tokens, billed amount,
run-capture elapsed seconds, whole-command elapsed seconds, reserved seconds and
engineering elapsed seconds. Counts are integers. Currency belongs to the billed
amount metric. No price table, currency conversion or token-to-dollar estimator is
implemented in this slice. Record unavailable usage as unknown, not zero or free.

One `scope_id` identifies one exclusive spend component. Reject multiple records for
the same scope rather than guessing whether they replace or supplement each other;
combine its metric observations before record creation. Reject inclusive parent
totals as unsupported input. Sum exclusive components once, including unsuccessful
and diagnostic attempts. Keep reported and estimated subtotals separate, and show
unknown component coverage. The report manifest explicitly lists the expected
resource scope IDs; absent records count as unknown scopes. A reported metric total
requires one reported value for every declared scope, with matching units/currency.
Otherwise emit only its reported/estimated subtotals and missing coverage, with the
complete total null. A total describes only that declared scope; it cannot claim
unobserved coordinator or provider-wide spend. The default infrastructure report
declares one setup scope per selected receipt, even when all resource values are
unknown. Engineering scopes, if supplied, remain a separate group.
Do not add cached-input tokens to input tokens as though they are disjoint. Do not
add elapsed, reserved and engineering seconds into one duration. Summed component
time is not an end-to-end wall-clock measurement, especially with parallel work.

For this replay, derive run-capture elapsed time from the final valid supervisor
event and label its interval explicitly: it excludes preparation and later cleanup.
Import reserved seconds only from a separately hash-bound ledger row matching the
attempt. Engineering debit remains a separately sourced observation. Whole-command
duration may be imported from the existing allowlisted validation report only when
its attempt and receipt-file hash match; label it reported by that measurement
source, not derived from the runtime receipt. Otherwise it stays unknown. Billed
dollars and tokens remain unknown. The report must work with unknown resources.

Future cost per accepted primary task is defined as all exclusive execution spend
in a frozen comparison, including coordinator/worker/grader/setup and diagnostics,
divided by independently accepted primary task slots. Engineering cost is reported
separately. That metric requires independent assessments and complete scope/usage;
zero accepted slots has no finite value. **Do not implement a benchmark-cost producer
or compute this ratio from infrastructure probes.** This build emits an unavailable
metric with reason `no_model_primary_assessments` and makes no savings claim.

## Commands and report

- Keep `verify-probe` explicitly integrity-only. Exit 0 means its declared integrity
  check succeeded even for a partial run; expose `verification_scope: artifact_integrity_only`
  and never call that probe success. Invalid bindings exit 2.
- Add `assess-probe DIRECTORY --expect completion|cancellation|deadline`, returning
  the assessment JSON to stdout without writing originals. Exit 0 only for the
  expected control passing, 1 for known control failure, 2 for unverified/invalid.
- Wire the existing `probe` result through that same assessment and exit decision.
  Its predeclared expectation follows its options: normal mode expects completion;
  wait mode with cancellation before the deadline expects cancellation; wait mode
  otherwise expects deadline. Reject ambiguous option combinations before launch.
  Do not infer the expected outcome from the result after execution. This closes
  the existing generic-CLI-success gap; deterministic tests cover this wiring without
  granting or making another runtime launch. Preflight-only remains a setup check.
- Add an offline report command that takes an explicit manifest listing selected
  receipt directories and expectations, optional resource records, and an explicit
  output directory. Render one `report.json` and `report.md` from the same computed
  assessment set. Successful rendering exits 0 irrespective of assessment status;
  include `command_status: rendered` and status counts. Bad invocation/input that
  prevents rendering exits 2. Documentation distinguishes command success from quality.

Hash the report's canonical result with a detached digest; include policy and
source hashes so offline re-rendering needs no execution. Omit changing timestamps
from hashed result content, or require a supplied stable timestamp. Refuse output
inside any selected source attempt/store and refuse overwriting an existing report.
Render only allowlisted observation summaries and relative artifact references;
never copy raw Docker inspection, environment values, host paths or worker streams
into a public export. Private originals remain the inspectable evidence source.

## Explicit verification cases

These are deterministic software cases, not operational-agent quality evals. Add
their named inventory to the project's shared evaluation inventory and report the
actual commands/results. Synthetic receipt mutations use copies with clearly
labeled origins; never alter originals or count synthetic output as a model run.

| ID | Case and required result |
|---|---|
| EQ01 | Complete recognized probe: valid bindings and every prescribed observation produce completion/control pass; benchmark unavailable |
| EQ02 | Cancellation and deadline: each matched control passes with stopped evidence; natural completion never passes and capture stays partial |
| EQ03 | Empty, irrelevant or missing observation stream: no control pass; explicit missing-coverage reasons |
| EQ04 | Known violation plus another missing observation: failure remains visible and outranks unverified |
| EQ05 | Bad artifact hash, runtime/image mismatch or ownership mismatch: no trusted pass; originals still verify |
| EQ06 | Legacy recognized program normalizes; missing/unknown program or unknown policy version stays unverified; explicit descriptor disagreement cannot pass |
| EQ07 | Chunk boundaries split JSON/UTF-8 and interleave stderr: equivalent valid stdout yields identical assertions; stderr cannot spoof observations |
| EQ08 | Invalid base64/JSON, duplicate keys/events, sequence gaps, trailing fragments or configured bound exceeded: bounded incomplete result, no crash or pass |
| EQ09 | Nonzero exit, false stopped flag, wrong control reason and different write exception: fail/unverified according to the declared rules, never completion pass |
| EQ10 | Resource zero versus unknown, reported versus estimated, invalid numbers/units/currency, duplicate scope and inclusive parent: exact subtotals or explicit rejection; no double counting |
| EQ11 | CLI/report semantics: integrity-only partial verification can exit 0; assess exits 0/1/2 correctly; Markdown and JSON share results; no model-cost ratio |
| EQ12 | Replay the three existing real receipts with matching reported durations: originals and ledger unchanged, separate report inspectable and deterministically reproducible |

Run the existing deterministic suite plus these focused cases, then the actual
offline replay. Report passing counts only from commands run. Missing private
evidence is a replay gap, not grounds to substitute synthetic evidence or launch
Docker. Stop at 60 minutes with the achieved slice and remaining issue; do not
restart this allowance or extend the implementation into runtime/auth repairs.

## Deferred decisions

The new remote PR reviews correctly identify that receipt integrity is not probe
success and that a complete lifecycle ceiling is unproved. This increment addresses
the former; it preserves the latter limitation. It does not close Milestone A.
The requested semantic rubric, independent reviewer and adjudication deadline still
belong to the future actual model comparison; they are not implemented by fixed
filesystem assertions. A cloud-verifiable authenticated evidence path belongs to
later operational integration, outside this explicitly trusted local supervisor.

Do not change production routing or infer efficiency from lane names. A later
routing experiment needs its own versioned schema binding the policy revision,
decision inputs, selected lane and requested versus observed execution identity.
The current instruction-only schema intentionally cannot vary model/tools between
variants. No routing service, scheduler, Cockpit integration, release control,
subscription credential broker or customer data ingestion is added here.

Decision record: [ADR 0002](../adr/0002-evidence-and-resource-report.md).
