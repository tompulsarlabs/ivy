"""Execution boundary for Extra High to implement; no live or pretend executor."""
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol


class ExecutionState(str, Enum):
    COMPLETED = "completed"
    EXECUTION_ERROR = "execution_error"
    TIMED_OUT = "timed_out"
    CANCELED = "canceled"
    BUDGET_STOPPED = "budget_stopped"


class AttemptKind(str, Enum):
    PRIMARY = "primary"
    DIAGNOSTIC = "diagnostic"


class CriterionStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNVERIFIED = "unverified"


class BenchmarkStatus(str, Enum):
    MEETS = "meets_benchmark"
    DOES_NOT_MEET = "does_not_meet_benchmark"
    INCOMPLETE = "evidence_incomplete"


@dataclass(frozen=True)
class WorkerRequest:
    """Worker-visible material only. No grader inputs or expected result field."""
    attempt_id: str
    primary_slot_id: str
    comparison_sha256: str
    worker_snapshot_sha256: str
    agent_version_sha256: str
    deadline_seconds: int
    kind: AttemptKind = AttemptKind.PRIMARY
    diagnostic_of: str | None = None

    def __post_init__(self):
        if type(self.kind) is not AttemptKind:
            raise ValueError("explicit attempt kind required")
        if self.kind is AttemptKind.PRIMARY and self.diagnostic_of is not None:
            raise ValueError("primary attempts cannot replace earlier attempts")
        if self.kind is AttemptKind.DIAGNOSTIC and not self.diagnostic_of:
            raise ValueError("diagnostic attempt requires its original attempt id")
        if self.diagnostic_of == self.attempt_id:
            raise ValueError("an attempt cannot retry itself")


@dataclass(frozen=True)
class WorkloadHandle:
    attempt_id: str
    runtime_id: str


@dataclass(frozen=True)
class StopConfirmation:
    runtime_id: str
    terminated: bool
    evidence_reference: str | None


@dataclass(frozen=True)
class AttemptOutcome:
    execution_state: ExecutionState
    workload: WorkloadHandle
    capture_sha256: str | None
    observed_model: str | None
    observed_effort: str | None
    usage: dict | None
    # An outcome has no benchmark pass or release decision: those require grading.


class HarnessAdapter(Protocol):
    def describe(self) -> dict: ...
    def prepare(self, request: WorkerRequest) -> WorkloadHandle: ...
    def run(self, handle: WorkloadHandle, emit: Callable[[dict], None]) -> AttemptOutcome: ...
    def cancel(self, handle: WorkloadHandle) -> StopConfirmation: ...


class CapabilityUnavailable(RuntimeError):
    pass


class UnavailableAdapter:
    """Default until real isolation, capture and termination are implemented."""
    def describe(self):
        return {"available": False, "reason": "live_adapter_not_implemented"}

    def prepare(self, request):
        raise CapabilityUnavailable("live preparation is not implemented")

    def run(self, handle, emit):
        raise CapabilityUnavailable("live execution is not implemented")

    def cancel(self, handle):
        raise CapabilityUnavailable("runtime cancellation is not implemented")
