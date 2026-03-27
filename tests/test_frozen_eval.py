"""
Tests for frozen_eval.py
"""

import json
from pathlib import Path

import pytest

from src.query_processor import normalize_query
from eval.frozen_eval import score_fixture


def test_normalize_query_removes_punctuation() -> None:
    assert normalize_query("wireless-mouse!!") == ["wireless", "mouse"]


def test_normalize_query_lowercases() -> None:
    assert normalize_query("USB-C cable???") == ["usb", "c", "cable"]


def test_normalize_query_preserves_spaces() -> None:
    assert normalize_query("bluetooth speaker") == ["bluetooth", "speaker"]


def test_score_fixture_perfect_match() -> None:
    fixture = {
        "query": "wireless-mouse!!",
        "expected_keywords": ["wireless", "mouse"]
    }
    assert score_fixture(fixture) == 1.0


def test_score_fixture_partial_match() -> None:
    fixture = {
        "query": "wireless-device",
        "expected_keywords": ["wireless", "mouse"]
    }
    assert score_fixture(fixture) == 0.5


def test_score_fixture_no_match() -> None:
    fixture = {
        "query": "keyboard",
        "expected_keywords": ["wireless", "mouse"]
    }
    assert score_fixture(fixture) == 0.0


def test_frozen_eval_main_output_format() -> None:
    """Test that frozen_eval.py outputs valid JSON"""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "eval/frozen_eval.py"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "score" in output
    assert 0.0 <= output["score"] <= 1.0


def test_frozen_eval_score_correct_for_all_fixtures() -> None:
    """Verify frozen_eval calculates the correct score from actual fixtures."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "eval/frozen_eval.py"],
        capture_output=True, text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    # All 3 current fixtures match perfectly with normalize_query
    assert data["score"] == 1.0, f"Expected 1.0 but got {data['score']}"


def test_score_fixture_correctness_per_fixture() -> None:
    """Verify each fixture individually scores 1.0 (perfect match)."""
    fixtures = json.loads(
        (Path(__file__).parent.parent / "eval" / "fixtures.json").read_text(encoding="utf-8")
    )
    for f in fixtures:
        score = score_fixture(f)
        assert score == 1.0, f"Fixture {f['id']} expected 1.0, got {score}"
