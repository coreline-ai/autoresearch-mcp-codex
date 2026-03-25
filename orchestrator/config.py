import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

@dataclass
class OrchestratorConfig:
    max_iterations: int = 10; target_score: float | None = None; mode: str = "single-agent"
    allow_dirty: bool = False; baseline_path: Path = field(default=lambda: Path("eval/baseline.json"))
    frozen_eval_path: Path = field(default=lambda: Path("eval/frozen_eval.py"))
    tests_path: Path = field(default=lambda: Path("tests"))
    results_path: Path = field(default=lambda: Path("agent/RESULTS.tsv"))
    decisions_path: Path = field(default=lambda: Path("agent/DECISIONS.md"))
    memory_path: Path = field(default=lambda: Path("agent/MEMORY.md"))
    tmp_path: Path = field(default=lambda: Path("tmp"))
    reports_path: Path = field(default=lambda: Path("reports"))
    use_git: bool = True; max_no_improvement_streak: int = 3

def load_baseline(config):
    if not config.baseline_path.exists():
        raise FileNotFoundError(f"Baseline not found: {config.baseline_path}")
    return json.loads(config.baseline_path.read_text(encoding="utf-8"))

def save_baseline(config, score, iteration):
    config.baseline_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"score": score, "measured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "iteration": iteration}
    config.baseline_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
