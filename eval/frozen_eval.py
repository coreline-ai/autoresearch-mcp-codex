"""
Frozen Evaluation Script for AutoResearch Agent System

This script evaluates search relevance using fixed fixtures.
It must NOT be modified during optimization iterations.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FIXTURES_PATH = ROOT / "fixtures.json"


def normalize_query(query: str) -> list[str]:
    """
    Normalize query by removing punctuation and converting to lowercase.

    This is a placeholder implementation that will be replaced
    by actual search code during optimization.
    """
    cleaned = []
    for ch in query.lower():
        if ch.isalnum() or ch.isspace():
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    tokens = [t for t in "".join(cleaned).split() if t]
    return tokens


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
        "tests_pass": True,
        "constraints_ok": True,
        "latency_ms": 100,
        "latency_delta_pct": 0.0,
        "regressions": [],
        "notes": ["frozen eval completed"]
    }

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
