"""Tests for column_norm module."""

import pytest
from preprocess_utils.column_norm import (
    simple_stem,
    fuzzy_match_values,
    normalize_column,
    extract_numeric_from_mixed,
    detect_mixed_format_column,
    normalize_column_format,
    ColumnNormalization,
)


# --- simple_stem ---

def test_stem_removes_s():
    assert simple_stem("points") == "point"

def test_stem_removes_ed():
    assert simple_stem("played") == "play"

def test_stem_removes_ing():
    assert simple_stem("running") == "run"

def test_stem_removes_ly():
    assert simple_stem("quickly") == "quick"

def test_stem_short_word():
    assert simple_stem("the") == "the"

def test_stem_empty():
    assert simple_stem("") == ""


# --- fuzzy_match_values ---

def test_fuzzy_exact_match():
    result = fuzzy_match_values("points", ["points", "goals", "score"])
    assert "points" in result

def test_fuzzy_partial_match():
    result = fuzzy_match_values("point", ["points", "pts", "pointer"])
    assert len(result) >= 1

def test_fuzzy_no_match():
    result = fuzzy_match_values("xyz", ["points", "goals", "score"], threshold=0.8)
    assert result == []

def test_fuzzy_empty_keyword():
    assert fuzzy_match_values("", ["a", "b"]) == []


# --- normalize_column ---

def test_normalize_finds_match():
    table = [
        ["name", "pts"],
        ["Alice", "25"],
        ["Bob", "30"],
    ]
    result = normalize_column(["points"], table, 1)
    assert result is not None
    assert result.column_name == "pts"
    assert len(result.matched_values) > 0

def test_normalize_no_match():
    table = [
        ["name", "city"],
        ["Alice", "Berlin"],
        ["Bob", "Paris"],
    ]
    result = normalize_column(["points"], table, 1)
    assert result is None

def test_normalize_invalid_column():
    result = normalize_column(["test"], [["a"]], 5)
    assert result is None


# --- extract_numeric_from_mixed ---

def test_extract_parenthesized():
    assert extract_numeric_from_mixed("(5th)") == 5.0

def test_extract_round_of():
    assert extract_numeric_from_mixed("round of 16") == 16.0

def test_extract_heat():
    assert extract_numeric_from_mixed("heat 3") == 3.0

def test_extract_standalone_number():
    assert extract_numeric_from_mixed("42") == 42.0

def test_extract_excluded_dns():
    assert extract_numeric_from_mixed("DNS") is None

def test_extract_excluded_dash():
    assert extract_numeric_from_mixed("—") is None

def test_extract_n_a():
    assert extract_numeric_from_mixed("N/A") is None

def test_extract_empty():
    assert extract_numeric_from_mixed("") is None

def test_extract_decimal():
    assert extract_numeric_from_mixed("3.14") == 3.14


# --- detect_mixed_format_column ---

def test_detect_mixed():
    values = ["heat 1", "heat 2", "DNS", "3", "round of 16"]
    assert detect_mixed_format_column(values) == True

def test_detect_all_numeric():
    values = ["1", "2", "3", "4"]
    assert detect_mixed_format_column(values) == False

def test_detect_all_text():
    values = ["Alice", "Bob", "Charlie"]
    assert detect_mixed_format_column(values) == False


# --- normalize_column_format ---

def test_normalize_format():
    values = ["heat 1", "heat 2", "DNS", "3"]
    result = normalize_column_format(values)
    assert result["heat 1"] == 1.0
    assert result["heat 2"] == 2.0
    assert result["DNS"] is None
    assert result["3"] == 3.0
