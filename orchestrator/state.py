"""State management for AutoResearch Agent System."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class Phase(str, Enum):
    """Iteration phase state machine (16 states per doc spec)."""
    INIT = "init"
    READ_CONTEXT = "read_context"
    EXPLORE = "explore"
    PLAN = "plan"
    IMPLEMENT = "implement"
    RUN_TESTS = "run_tests"
    RUN_EVAL = "run_eval"
    CRITIQUE = "critique"
    DECIDE = "decide"
    ACCEPT = "accept"
    REJECT = "reject"
    ROLLBACK = "rollback"
    ARCHIVE = "archive"
    FINALIZE = "finalize"
    ERROR = "error"
    DONE = "done"


class DecisionCode(str, Enum):
    """Reject reason classification codes (doc 08-decision-engine)."""
    ACCEPT = "ACCEPT"
    TEST_FAIL = "TEST_FAIL"
    CONSTRAINT_FAIL = "CONSTRAINT_FAIL"
    NO_IMPROVEMENT = "NO_IMPROVEMENT"
    SCORE_REGRESSION = "SCORE_REGRESSION"
    CRITIC_BLOCK = "CRITIC_BLOCK"
    SCOPE_VIOLATION = "SCOPE_VIOLATION"
    FORBIDDEN_FILE = "FORBIDDEN_FILE"
    EVAL_CRASH = "EVAL_CRASH"
    IMPLEMENT_ERROR = "IMPLEMENT_ERROR"
    NO_CODE_CHANGE = "NO_CODE_CHANGE"


class Decision(str, Enum):
    """Decision outcomes."""
    ACCEPT = "accept"
    REJECT = "reject"
    HOLD = "hold"


@dataclass
class IterationState:
    """Tracks current iteration state (doc 11 spec)."""
    iteration: int
    mode: str
    phase: Phase | str
    selected_hypothesis: str | None = None
    baseline_score: float = 0.0
    candidate_score: float | None = None
    tests_pass: bool | None = None
    constraints_ok: bool | None = None
    decision: str | None = None
    last_updated: str = ""

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "mode": self.mode,
            "phase": self.phase if isinstance(self.phase, str) else self.phase.value,
            "selected_hypothesis": self.selected_hypothesis,
            "baseline_score": self.baseline_score,
            "candidate_score": self.candidate_score,
            "tests_pass": self.tests_pass,
            "constraints_ok": self.constraints_ok,
            "decision": self.decision,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> IterationState:
        phase = data.get("phase", "done")
        try:
            phase = Phase(phase)
        except ValueError:
            pass
        return cls(
            iteration=data.get("iteration", 0),
            mode=data.get("mode", "single-agent"),
            phase=phase,
            selected_hypothesis=data.get("selected_hypothesis"),
            baseline_score=data.get("baseline_score", 0.0),
            candidate_score=data.get("candidate_score"),
            tests_pass=data.get("tests_pass"),
            constraints_ok=data.get("constraints_ok"),
            decision=data.get("decision"),
            last_updated=data.get("last_updated", ""),
        )


# Default path (used when no config is provided)
DEFAULT_STATE_PATH = Path("agent/ITERATION_STATE.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_state(state_path: Path = DEFAULT_STATE_PATH) -> IterationState | None:
    if not state_path.exists():
        return None
    return IterationState.from_dict(json.loads(state_path.read_text(encoding="utf-8")))


def save_state(state: IterationState, state_path: Path = DEFAULT_STATE_PATH) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def init_state(
    iteration: int,
    mode: str,
    hypothesis: str | None = None,
    baseline: float = 0.0,
    state_path: Path = DEFAULT_STATE_PATH,
) -> IterationState:
    """Create and persist a fresh iteration state."""
    state = IterationState(
        iteration=iteration,
        mode=mode,
        phase=Phase.INIT,
        selected_hypothesis=hypothesis,
        baseline_score=baseline,
        last_updated=_now_iso(),
    )
    save_state(state, state_path)
    return state


def update_phase(phase: Phase, state_path: Path = DEFAULT_STATE_PATH) -> IterationState:
    current = load_state(state_path)
    if current is None:
        raise RuntimeError("No active iteration state")
    current.phase = phase
    current.last_updated = _now_iso()
    save_state(current, state_path)
    return current


def update_state_fields(state_path: Path = DEFAULT_STATE_PATH, **kwargs) -> IterationState:
    """Update arbitrary fields on the current iteration state."""
    current = load_state(state_path)
    if current is None:
        raise RuntimeError("No active iteration state")
    for key, value in kwargs.items():
        if hasattr(current, key):
            setattr(current, key, value)
    current.last_updated = _now_iso()
    save_state(current, state_path)
    return current
