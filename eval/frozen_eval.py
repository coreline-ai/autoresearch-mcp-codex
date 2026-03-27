"""
Frozen Evaluation Script for AutoResearch Agent System

This script evaluates search relevance using fixed fixtures.
It must NOT be modified during optimization iterations.

Product logic (normalize_query) lives in src/query_processor.py
and is imported here for evaluation. Agents improve src/, not eval/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.query_processor` is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.query_processor import normalize_query  # noqa: E402

ROOT = Path(__file__).resolve().parent
FIXTURES_PATH = ROOT / "fixtures.json"


def score_fixture(item: dict) -> float:
    """
    Score a single fixture by checking expected keyword matches.

    Args:
        item: Fixture dict with 'query' and 'expected_keywords'

    Returns:
        Float score between 0.0 and 1.0
    """
    tokens = set(normalize_query(item["query"]))
    expected = set(item["expected_keywords"])

    if not expected:
        return 0.0

    matched = len(tokens & expected)
    return matched / len(expected)


def main() -> int:
    """
    Run frozen evaluation on all fixtures and return score.

    Output format is JSON to enable programmatic consumption.
    """
    fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    scores = [score_fixture(item) for item in fixtures]
    final_score = sum(scores) / len(scores) if scores else 0.0

    result = {
        "score": round(final_score, 4),
        # NOTE: Values below are defaults for standalone execution.
        # In the orchestrator pipeline, eval/constraints.py overrides
        # constraints_ok, latency_ms, and latency_delta_pct with real
        # measurements (see orchestrator/agents.py::run_eval).
        "tests_pass": True,
        "constraints_ok": True,
        "latency_ms": 100,
        "latency_delta_pct": 0.0,
        "regressions": [],
        "notes": ["frozen eval completed"],
    }

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
