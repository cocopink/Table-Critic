"""Test suite for table flatten functionality."""

import pytest
from preprocess_utils.detect import has_compound_headers, find_compound_columns


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
