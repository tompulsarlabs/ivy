# Report — 2026-09-25-ivy-playbookretune-review-02

Produced by the workhorse/openai lane, 9.3 wall-minutes.

# PR #21 follow-up review — `e2d21c3`

**Verdict: block.** The Immutable claim holds, and one prior scope claim is correctly narrowed, but the green fallback and eval rigor findings are not fully closed.

| 09-24 finding | Status |
|---|---|
| P1: green fallback false-grey | **Not closed** |
| P2: memory transformation grading | **Partially closed** |
| P2: blind / exact-head comparison | **Not closed** |
| P2: PR #18 equivalent-case claim | **Closed by narrowing the claim** |

## Findings

### P1 — the fallback can still falsely grey a real-work day

`a6b020a` corrects the timeout fixture’s generic PR search to return #67 at `evals/routines/cases/failsafe-timeout-promote/evidence.md:21-23`; `d40e6da` correctly says a worker-opened draft PR counts at `playbook.md:157-160`.

But the actual lookup ladder at `playbook.md:150-165` is unchanged from `5937264`: it has neither bounded contract-PR discovery nor a branch for a successful-but-incomplete/conflicting zero result. It also explicitly classifies a review-only day as grey at `playbook.md:160-163`, despite Immutable `playbook.md:25-26` saying PR reviews count.

The new regression begins already green (`failsafe-timeout-promote/case.json:56-75`; its journal says GREEN at `files/journal/2026-09-23.md:142-151`) and only asserts no Tom journal and `failsafe_fired != true` (`case.json:34-53`). It does not require `day_state: green`, `method: real-work`, or #67 as the green source.

**Proposed fix:** Before deciding grey, query any current-day/active build contract’s known PR URL, branch, or contract ID. A verified connected-actor PR makes the day green; a conflicting/incomplete result is unknown and alerts; a clean zero with no PR lead remains grey. Add a regression that starts grey with a generic zero plus exact contract lookup #67, and asserts green/source/no Tom journal.

### P2 — the memory graders retain diffs but do not validate the claimed structure

`7121c3b` does retain unified diffs, and `da3cc49` adds the collapsed-page case. However, `scripts/eval-routines.py:203-216` still grades regex counts; `diffs` are only attached after measurement at `:405-412`, not used by `grade()`.

The cases at `failsafe-ongoing-condition/case.json:8-83` and `retro-collapse-sediment/case.json:8-76` do not require the ongoing-condition count or what it blocks, although the playbook requires both at `playbook.md:341-346`. They can pass after deleting the real condition and inserting unrelated `dark`, date, and citation text. The retro case also permits up to two restatements rather than one current-state account.

**Proposed fix:** Grade a structurally identified condition paragraph, requiring one surviving account with began date, current count, last-confirmed date, citation, and blocked consequence. Add adversarial fixture mutations for deletion, unrelated citations, and a second restatement, then rerun the affected cases.

### P2 — the claimed blind, current-head comparison is not established

Random leaf sandbox names are an improvement, but `scripts/eval-routines.py:317-321` places them under a shared parent. The label-bearing work directories and transcripts remain reachable as siblings (`:335`, `:367-368`, `:440-447`), while the Claude invocation at `:346-360` omits `--restricted`, the CLI mode that confines file tools to the working directory. `Read`, `Glob`, and `Grep` can therefore inspect `../../<label>/transcripts/`, exposing case and variant labels.

Separately, the advertised 47/48 preserve and 3/4 change result is for `6b59878`, not the final playbook (`evals/routines/results/2026-09-24.md:79-84`). Final `f5eefba` receives only the nine failsafe cases (`:21-26`, `:129-157`), despite post-`6b59878` playbook changes.

**Proposed fix:** Run with `--restricted`, place every run outside any readable label-bearing parent, add an integration test for parent traversal, and rerun the full 27-case comparison against `e2d21c3`.

## Closed finding

The PR body now explicitly limits the PR #18 assertion to 3 of 10 Ivy cases having full runnable equivalents. That satisfies the prior review’s alternative of narrowing the claim; it does not claim complete coverage.

## Declined-proposal assessment

The review-only trade-off is operationally asymmetric: a false grey produces one permitted, genuine journal fallback, while a false green can skip the only day-securing commit. It does not, however, make a known-but-undatable review accurately “grey”; it remains an ambiguous positive and conflicts with the Immutable counting rule.

Treating every successful zero-result search as unknown would indeed alert quiet evenings. But that does not justify treating a zero that conflicts with a known contract PR as clean; the current playbook lacks that distinction.

## Confirmed

All cited fix commits are ancestors of `e2d21c3`. `routines/` is byte-identical between `5937264` and the current head. The seven Immutable sections remain byte-identical: 110 LF-terminated lines, 5,946 bytes, SHA-256 `292c1e83511eb72b3f9dbae511f7581fbe94e6327871a49a0333612bbe4856e3`.

Read-only constraint honored: no report file, commit, push, or workspace modification was made.
