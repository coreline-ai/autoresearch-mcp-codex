"""Configuration for AutoResearch Orchestrator."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class OrchestratorConfig:
    max_iterations: int = 10
    target_score: float | None = None
    mode: str = "single-agent"
    allow_dirty: bool = False
    baseline_path: Path = field(default_factory=lambda: Path("eval/baseline.json"))
    frozen_eval_path: Path = field(default_factory=lambda: Path("eval/frozen_eval.py"))
    tests_path: Path = field(default_factory=lambda: Path("tests"))
    results_path: Path = field(default_factory=lambda: Path("agent/RESULTS.tsv"))
    decisions_path: Path = field(default_factory=lambda: Path("agent/DECISIONS.md"))
    memory_path: Path = field(default_factory=lambda: Path("agent/MEMORY.md"))
    state_path: Path = field(default_factory=lambda: Path("agent/ITERATION_STATE.json"))
    tmp_path: Path = field(default_factory=lambda: Path("tmp"))
    reports_path: Path = field(default_factory=lambda: Path("reports"))
    use_git: bool = True
    max_no_improvement_streak: int = 3
    # LLM provider: "claude" (Claude Code CLI) or "codex" (OpenAI Codex CLI)
    llm_provider: str = "claude"
    llm_timeout: int = 300
    llm_max_turns: int = 3


def load_baseline(config: OrchestratorConfig) -> dict:
    if not config.baseline_path.exists():
        raise FileNotFoundError(f"Baseline not found: {config.baseline_path}")
    return json.loads(config.baseline_path.read_text(encoding="utf-8"))


def save_baseline(config: OrchestratorConfig, score: float, iteration: int) -> None:
    """Atomically save baseline (write to temp, then rename)."""
    config.baseline_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "score": score,
        "measured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "iteration": iteration,
    }
    content = json.dumps(data, ensure_ascii=False, indent=2)

    # Atomic write: tempfile in same directory, then os.replace
    fd = None
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(config.baseline_path.parent),
            suffix=".tmp",
        )
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        fd = None
        os.replace(tmp_path, str(config.baseline_path))
    except Exception:
        if fd is not None:
            os.close(fd)
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
