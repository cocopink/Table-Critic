"""Test suite for table flatten functionality."""

import pytest
from preprocess_utils.detect import has_compound_headers, find_compound_columns
from preprocess_utils.flatten import flatten_table, split_cell_value


def test_detect_compound_headers_with_slash():
    """Should detect slash-separated compound headers"""
    table = [
        ["no.", "date/time", "location"],
        ["1", "1944-03-08 10:30", "Germany"]
    ]
    assert has_compound_headers(table) == True


def test_detect_simple_headers():
    """Should return False for simple headers"""
    table = [
        ["no.", "date", "location"],
        ["1", "1944-03-08", "Germany"]
    ]
    assert has_compound_headers(table) == False


def test_find_compound_columns_indices():
    """Should return indices of compound columns"""
    table = [
        ["no.", "date/time", "city/country", "location"],
        ["1", "1944-03-08", "Berlin/Germany", "Europe"]
    ]
    indices = find_compound_columns(table)
    assert indices == [1, 2]  # date/time and city/country


def test_detect_empty_table():
    """Should handle empty table gracefully"""
    assert has_compound_headers([]) == False
    assert find_compound_columns([]) == []


def test_detect_newline_separator():
    """Should detect newline-separated compound headers"""
    table = [
        ["no.", "date\ntime", "location"],
        ["1", "1944-03-08", "Germany"]
    ]
    assert has_compound_headers(table) == True


def test_find_multiple_separators():
    """Should find columns with different separators"""
    table = [
        ["no.", "date/time", "city - country", "rank|position"],
        ["1", "1944-03-08", "Berlin - Germany", "1|2"]
    ]
    indices = find_compound_columns(table)
    assert indices == [1, 2, 3]  # all three compound columns


# ===== Flatten Tests (Task 3) =====

def test_flatten_slash_column():
    """Should split column with slash separator"""
    table = [
        ["no.", "date/time", "location"],
        ["1", "1944-03-08 10:30", "Germany"],
        ["2", "1944-03-09 14:20", "France"]
    ]
    flattened, metadata = flatten_table(table)

    assert flattened[0] == ["no.", "date", "time", "location"]
    assert len(flattened) == 3
    assert metadata['flattened'] == True
    assert metadata['split_columns'] == 1


def test_flatten_with_space_separator_in_value():
    """Should split cell value using space when header uses slash"""
    table = [
        ["date/time"],
        ["1944-03-08 10:30"]
    ]
    flattened, _ = flatten_table(table)

    assert flattened[0] == ["date", "time"]
    assert flattened[1] == ["1944-03-08", "10:30"]


def test_flatten_fallback_copy():
    """Should copy value when splitting fails"""
    table = [
        ["a/b"],
        ["unknown"]
    ]
    flattened, _ = flatten_table(table)

    assert flattened[0] == ["a", "b"]
    assert flattened[1] == ["unknown", "unknown"]


def test_flatten_no_compound_headers():
    """Should return original table if no compound headers"""
    table = [
        ["a", "b", "c"],
        ["1", "2", "3"]
    ]
    flattened, metadata = flatten_table(table)

    assert flattened == table
    assert metadata['flattened'] == False


def test_split_cell_value_priority():
    """Should try separators in priority order"""
    # Test 1: Slash works
    result = split_cell_value("2023/01/15", "/", 3)
    assert result == ["2023", "01", "15"]

    # Test 2: Fallback to space
    result = split_cell_value("1944-03-08 10:30", "/", 2)
    assert result == ["1944-03-08", "10:30"]

    # Test 3: Fallback to copy
    result = split_cell_value("unknown", "/", 2)
    assert result == ["unknown", "unknown"]
