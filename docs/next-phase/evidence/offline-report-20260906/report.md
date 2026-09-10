Infrastructure proof — no model evaluation

Recorded offline assessment. No model benchmark or savings claim.

| Evidence | Expected control | Control | Natural completion | Integrity |
| --- | --- | --- | --- | --- |
| complete | completion | pass | pass | verified |
| cancel | cancellation | pass | fail | verified |
| deadline | deadline | pass | fail | verified |

**complete**

Receipt: `d6efd9c8b6047ff844a7398ba11736620ae7b083542f77df2039d73dd09a132e`

| Check | Status | Reason |
| --- | --- | --- |
| capture_structure | pass | parsed |
| worker_event_shapes | pass | supported |
| no_duplicate_observations | pass | matched |
| fixture_bytes | pass | matched |
| nonroot | pass | matched |
| checked_credentials_absent | pass | matched |
| instruction_inventory | pass | matched |
| fixture_write | pass | write_did_not_succeed |
| evidence_write | pass | write_did_not_succeed |
| isolation_0 | pass | matched |
| isolation_1 | pass | matched |
| termination | pass | confirmed_stopped |
| start_identity | pass | matched |
| expected_completion | pass | natural_completion_requirements |

**cancel**

Receipt: `6ab850b039ffb82ccf26047235cf1575a759f9a29b727424d041c322d02d8ddc`

| Check | Status | Reason |
| --- | --- | --- |
| capture_structure | pass | parsed |
| worker_event_shapes | pass | supported |
| no_duplicate_observations | pass | matched |
| fixture_bytes | pass | matched |
| nonroot | pass | matched |
| checked_credentials_absent | pass | matched |
| instruction_inventory | pass | matched |
| fixture_write | pass | write_did_not_succeed |
| evidence_write | pass | write_did_not_succeed |
| isolation_0 | pass | matched |
| isolation_1 | pass | matched |
| termination | pass | confirmed_stopped |
| start_identity | pass | matched |
| expected_stop_request | pass | matched |
| expected_terminal_state | pass | matched |

**deadline**

Receipt: `fb5d3317c704b0c6c84bbbae4b677834d349ca5b462bfe76ce85f2ecb61d5b66`

| Check | Status | Reason |
| --- | --- | --- |
| capture_structure | pass | parsed |
| worker_event_shapes | pass | supported |
| no_duplicate_observations | pass | matched |
| fixture_bytes | pass | matched |
| nonroot | pass | matched |
| checked_credentials_absent | pass | matched |
| instruction_inventory | pass | matched |
| fixture_write | pass | write_did_not_succeed |
| evidence_write | pass | write_did_not_succeed |
| isolation_0 | pass | matched |
| isolation_1 | pass | matched |
| termination | pass | confirmed_stopped |
| start_identity | pass | matched |
| expected_stop_request | pass | matched |
| expected_terminal_state | pass | matched |

**Resource visibility**

| Group / metric | Reported subtotal | Estimated subtotal | Unknown scopes | Complete reported total |
| --- | ---: | ---: | ---: | ---: |
| execution / request_count (count) | Unavailable | Unavailable | 3 | Unavailable |
| execution / input_tokens (tokens) | Unavailable | Unavailable | 3 | Unavailable |
| execution / output_tokens (tokens) | Unavailable | Unavailable | 3 | Unavailable |
| execution / cached_input_tokens (tokens) | Unavailable | Unavailable | 3 | Unavailable |
| execution / billed_amount (currency unknown) | Unavailable | Unavailable | 3 | Unavailable |
| execution / run_capture_elapsed_seconds (seconds) | 11.9423986 | Unavailable | 0 | 11.9423986 |
| execution / whole_command_elapsed_seconds (seconds) | 13.121506 | Unavailable | 0 | 13.121506 |
| execution / reserved_seconds (seconds) | 190 | Unavailable | 0 | 190 |
| execution / engineering_elapsed_seconds (seconds) | Unavailable | Unavailable | 3 | Unavailable |
| engineering / request_count (count) | Unavailable | Unavailable | 1 | Unavailable |
| engineering / input_tokens (tokens) | Unavailable | Unavailable | 1 | Unavailable |
| engineering / output_tokens (tokens) | Unavailable | Unavailable | 1 | Unavailable |
| engineering / cached_input_tokens (tokens) | Unavailable | Unavailable | 1 | Unavailable |
| engineering / billed_amount (currency unknown) | Unavailable | Unavailable | 1 | Unavailable |
| engineering / run_capture_elapsed_seconds (seconds) | Unavailable | Unavailable | 1 | Unavailable |
| engineering / whole_command_elapsed_seconds (seconds) | Unavailable | Unavailable | 1 | Unavailable |
| engineering / reserved_seconds (seconds) | Unavailable | Unavailable | 1 | Unavailable |
| engineering / engineering_elapsed_seconds (seconds) | 11700 | Unavailable | 0 | 11700 |

Cost per accepted primary task: **Unavailable — no model primary assessments.**

**Limits of this evidence**

- Trusted local supervisor; hashes are not signatures.
- Fixed-probe observations are not agent quality or instruction-following evidence.
- Observed capture time excludes preparation and cleanup; no hard lifecycle guarantee.
- Resource totals cover declared exclusive scopes only; unavailable billing is not zero.
