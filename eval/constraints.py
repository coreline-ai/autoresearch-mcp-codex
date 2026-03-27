"""
Constraints Checker for AutoResearch Agent System

Checks resource budgets and other constraints after changes.
Compares current eval metrics against baseline to detect violations.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path


BASELINE_PATH = Path("eval/baseline.json")
LATENCY_BUDGET_PCT = 5.0      # max allowed latency increase (%)
MAX_LATENCY_MS = 5000          # absolute latency ceiling (ms)
MAX_REGRESSIONS = 0            # max allowed regression count


def load_baseline_metrics() -> dict:
    """Load baseline metrics for comparison."""
    if BASELINE_PATH.exists():
        data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        return data
    return {}


def measure_latency(eval_script: str = "eval/frozen_eval.py") -> tuple[float, dict]:
    """Run eval and measure execution time as a latency proxy."""
    import subprocess

    start = time.time()
    r = subprocess.run(
        [sys.executable, eval_script],
        capture_output=True, text=True,
    )
    elapsed_ms = (time.time() - start) * 1000

    if r.returncode != 0:
        return elapsed_ms, {"error": r.stderr}

    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        data = {}

    return elapsed_ms, data


def check_constraints(
    eval_output: dict | None = None,
    baseline_latency_ms: float | None = None,
) -> dict:
    """Check resource constraints and return structured result.

    Args:
        eval_output: Pre-computed eval output dict. If None, runs eval fresh.
        baseline_latency_ms: Baseline latency for comparison. If None, uses 100ms default.
    """
    violations: list[str] = []
    notes: list[str] = []

    if eval_output is None:
        latency_ms, eval_output = measure_latency()
    else:
        latency_ms = eval_output.get("latency_ms", 100)

    if baseline_latency_ms is None:
        baseline = load_baseline_metrics()
        baseline_latency_ms = baseline.get("latency_ms", 100)

    # Check 1: Latency budget
    if baseline_latency_ms > 0:
        delta_pct = ((latency_ms - baseline_latency_ms) / baseline_latency_ms) * 100
    else:
        delta_pct = 0.0

    latency_ok = delta_pct <= LATENCY_BUDGET_PCT
    if not latency_ok:
        violations.append(
            f"Latency budget exceeded: {latency_ms:.0f}ms vs baseline {baseline_latency_ms:.0f}ms "
            f"(+{delta_pct:.1f}%, limit {LATENCY_BUDGET_PCT}%)"
        )

    # Check 2: Absolute latency ceiling
    if latency_ms > MAX_LATENCY_MS:
        violations.append(f"Absolute latency ceiling exceeded: {latency_ms:.0f}ms > {MAX_LATENCY_MS}ms")
        latency_ok = False

    # Check 3: Regressions from eval output
    regressions = eval_output.get("regressions", [])
    regressions_ok = len(regressions) <= MAX_REGRESSIONS
    if not regressions_ok:
        violations.append(f"Regressions detected: {regressions}")

    # Check 4: Score sanity (must be between 0 and 1)
    score = eval_output.get("score", 0.0)
    score_ok = 0.0 <= score <= 1.0
    if not score_ok:
        violations.append(f"Score out of range: {score}")

    constraints_ok = latency_ok and regressions_ok and score_ok
    if constraints_ok:
        notes.append("All constraints passed")

    return {
        "constraints_ok": constraints_ok,
        "latency_ms": round(latency_ms),
        "latency_delta_pct": round(delta_pct, 2),
        "violations": violations,
        "notes": notes,
    }


def main() -> int:
    """Run constraint checks and output JSON result."""
    result = check_constraints()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["constraints_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
