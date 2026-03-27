"""
Tests for src/query_processor.py — the product logic that agents improve.
"""

from __future__ import annotations

from src.query_processor import normalize_query


class TestNormalizeQueryEdgeCases:
    def test_empty_string(self):
        assert normalize_query("") == []

    def test_only_punctuation(self):
        assert normalize_query("!!!???...") == []

    def test_only_spaces(self):
        assert normalize_query("   ") == []

    def test_numbers_preserved(self):
        assert normalize_query("usb 3.0 cable") == ["usb", "3", "0", "cable"]

    def test_mixed_case(self):
        assert normalize_query("WiFi Router") == ["wifi", "router"]

    def test_hyphens_become_spaces(self):
        assert normalize_query("noise-cancelling-headphones") == ["noise", "cancelling", "headphones"]

    def test_unicode_letters(self):
        result = normalize_query("café latte")
        assert "caf" in result or "café" in result  # depends on isalnum behavior
        assert "latte" in result

    def test_multiple_spaces_collapsed(self):
        assert normalize_query("wireless   mouse") == ["wireless", "mouse"]

    def test_tabs_and_newlines(self):
        assert normalize_query("wireless\tmouse\nkeyboard") == ["wireless", "mouse", "keyboard"]

    def test_single_character(self):
        assert normalize_query("a") == ["a"]

    def test_existing_fixture_q001(self):
        assert normalize_query("wireless-mouse!!") == ["wireless", "mouse"]

    def test_existing_fixture_q002(self):
        assert normalize_query("USB-C cable???") == ["usb", "c", "cable"]

    def test_existing_fixture_q003(self):
        assert normalize_query("bluetooth speaker") == ["bluetooth", "speaker"]
