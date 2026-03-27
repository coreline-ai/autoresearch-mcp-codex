"""
Query preprocessing module for AutoResearch Agent System.

This module contains the product logic that the iterative improvement
system optimizes. The frozen evaluator (eval/frozen_eval.py) imports
from here to score query normalization quality.

Implementer agents modify THIS file to improve search relevance.
"""

from __future__ import annotations


def normalize_query(query: str) -> list[str]:
    """Normalize query by removing punctuation and converting to lowercase.

    Args:
        query: Raw user search query string.

    Returns:
        List of cleaned, lowercase tokens.
    """
    cleaned = []
    for ch in query.lower():
        if ch.isalnum() or ch.isspace():
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    tokens = [t for t in "".join(cleaned).split() if t]
    return tokens
