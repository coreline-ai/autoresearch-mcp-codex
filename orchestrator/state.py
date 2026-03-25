import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

class Phase(Enum):
    IMPLEMENT = "implement"; RUN_TESTS = "run_tests"; RUN_EVAL = "run_eval"
    DECIDE = "decide"; ACCEPT = "accept"; REJECT = "reject"; ARCHIVE = "archive"; DONE = "done"

@dataclass
class IterationState:
    iteration: int; mode: str; phase: Phase | str; selected_hypothesis: str
    baseline_score: float; last_updated: str

    def to_dict(self):
        return {"iteration": self.iteration, "mode": self.mode,
                "phase": self.phase if isinstance(self.phase, str) else self.phase.value,
                "selected_hypothesis": self.selected_hypothesis, "baseline_score": self.baseline_score,
                "last_updated": self.last_updated}

    @classmethod
    def from_dict(cls, data):
        phase = data["phase"]
        try: phase = Phase(phase)
        except ValueError: pass
        return cls(data["iteration"], data["mode"], phase, data["selected_hypothesis"],
                    data["baseline_score"], data["last_updated"])

STATE_PATH = Path("agent/ITERATION_STATE.json")

def load_state():
    if not STATE_PATH.exists(): return None
    return IterationState.from_dict(json.loads(STATE_PATH.read_text(encoding="utf-8")))

def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

def update_phase(phase):
    current = load_state()
    if current is None: raise RuntimeError("No active iteration state")
    current.phase = phase
    current.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    save_state(current)
    return current
