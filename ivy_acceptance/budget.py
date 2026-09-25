"""In-memory reservation semantics; persistence and runtime supervision are build work."""
import math
from dataclasses import dataclass
from .planning import positive_int


class BudgetBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class Limits:
    max_attempts: int
    per_attempt_seconds: int
    total_seconds: int

    def __post_init__(self):
        for name in ("max_attempts", "per_attempt_seconds", "total_seconds"):
            positive_int(getattr(self, name), name)
        if self.per_attempt_seconds > self.total_seconds:
            raise ValueError("per-attempt limit exceeds total time")


class BudgetLedger:
    """A launch consumes an attempt even when it fails. Nothing silently refunds it.

    Callers supply supervisor monotonic time; this object neither measures token cost
    nor proves workload termination. Persist/restore atomically before live use.
    """
    def __init__(self, limits: Limits, started_at: float):
        self._check_time(started_at)
        self.limits = limits
        self.started_at = self.last_time = started_at
        self.used = set()
        self.active = None
        self.termination_unconfirmed = False

    @staticmethod
    def _check_time(value):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise BudgetBlocked("expected finite nonnegative monotonic time")

    def reserve(self, attempt_id: str, now: float):
        self._check_time(now)
        if not isinstance(attempt_id, str) or not attempt_id:
            raise BudgetBlocked("attempt id required")
        if now < self.last_time:
            raise BudgetBlocked("monotonic clock moved backwards")
        self.last_time = now
        if self.active is not None or self.termination_unconfirmed:
            raise BudgetBlocked("previous workload has not confirmed termination")
        if attempt_id in self.used:
            raise BudgetBlocked("attempt id was already consumed")
        if len(self.used) >= self.limits.max_attempts:
            raise BudgetBlocked("attempt budget exhausted")
        if now - self.started_at + self.limits.per_attempt_seconds > self.limits.total_seconds:
            raise BudgetBlocked("insufficient remaining execution time")
        self.used.add(attempt_id)
        self.active = attempt_id

    def finish(self, attempt_id: str, *, termination_confirmed: bool):
        if type(termination_confirmed) is not bool or attempt_id != self.active:
            raise BudgetBlocked("invalid termination confirmation")
        if not termination_confirmed:
            self.termination_unconfirmed = True
            return
        self.active = None
        self.termination_unconfirmed = False
