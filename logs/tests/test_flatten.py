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


# ===== Cache Tests (Task 4) =====

import os
import tempfile
from preprocess_utils.cache import check_cache, load_cache, save_cache


def test_check_cache_when_file_exists():
    """Should return True when cache file exists"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        cache_path = f.name
        f.write('{"test": "data"}')

    try:
        assert check_cache(cache_path) == True
    finally:
        os.unlink(cache_path)


def test_check_cache_when_file_missing():
    """Should return False when cache file doesn't exist"""
    assert check_cache("/nonexistent/path.jsonl") == False


def test_save_and_load_cache():
    """Should save and load samples correctly"""
    import tempfile
    import os

    samples = [
        {"id": "1", "table": [["a", "b"], ["c", "d"]]},
        {"id": "2", "table": [["e", "f"], ["g", "h"]]}
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        cache_path = f.name

    try:
        # Save
        save_cache(samples, cache_path)

        # Check cache exists
        assert check_cache(cache_path) == True

        # Load
        loaded_samples = load_cache(cache_path)

        assert len(loaded_samples) == 2
        assert loaded_samples[0]["id"] == "1"
        assert loaded_samples[1]["id"] == "2"
    finally:
        if os.path.exists(cache_path):
            os.unlink(cache_path)


def test_load_cache_raises_file_not_found():
    """Should raise FileNotFoundError when cache doesn't exist"""
    import pytest

    with pytest.raises(FileNotFoundError):
        load_cache("/nonexistent/path.jsonl")


def test_save_cache_creates_directory():
    """Should create directory if it doesn't exist"""
    import tempfile
    import shutil

    temp_dir = tempfile.mkdtemp()
    cache_path = os.path.join(temp_dir, "subdir", "cache.jsonl")

    try:
        samples = [{"id": "1", "data": "test"}]
        save_cache(samples, cache_path)

        assert os.path.exists(cache_path)
        assert check_cache(cache_path) == True
    finally:
        shutil.rmtree(temp_dir)
