"""Tests for HeaderTree module."""

import pytest
from preprocess_utils.header_tree import HeaderTree, HeaderNode, CellParsingRule


def test_build_simple_headers():
    tree = HeaderTree.build([
        ["name", "age", "score"],
        ["Alice", "25", "90"],
        ["Bob", "30", "85"],
    ])
    assert tree.compound_count == 0
    assert tree.flat_columns == ["name", "age", "score"]
    assert tree.max_depth == 1
    assert tree.serialize_for_prompt() == ""


def test_build_compound_headers():
    tree = HeaderTree.build([
        ["name", "city/country", "score"],
        ["Alice", "Berlin/Germany", "90"],
        ["Bob", "Paris/France", "85"],
    ])
    assert tree.compound_count == 1
    assert "city" in tree.flat_columns
    assert "country" in tree.flat_columns
    assert tree.max_depth == 2
    text = tree.serialize_for_prompt()
    assert "city/country" in text
    assert "compound" in text


def test_build_empty_table():
    tree = HeaderTree.build([])
    assert tree.compound_count == 0
    assert tree.flat_columns == []
    assert tree.serialize_for_prompt() == ""


def test_serialize_for_prompt_with_cells():
    tree = HeaderTree.build([
        ["date/time"],
        ["11 may 1917 @ 1950 hours"],
        ["12 jun 1918 @ 2000 hours"],
    ])
    text = tree.serialize_for_prompt()
    assert "date/time" in text
    assert "@" in text


def test_parse_compound_cells():
    tree = HeaderTree.build([
        ["event/date"],
        ["finals @ 2015"],
        ["semifinal @ 2016"],
        ["finals @ 2017"],
    ])
    parsed = tree.parse_compound_cells([
        ["event/date"],
        ["finals @ 2015"],
        ["semifinal @ 2016"],
        ["finals @ 2017"],
    ])
    assert 0 in parsed
    assert len(parsed[0]) == 3


def test_set_table_text():
    tree = HeaderTree.build([
        ["date/time"],
        ["1944-03-08 10:30"],
    ])
    tree.set_table_text([["date/time"], ["1944-03-08 10:30"]])
    assert hasattr(tree, '_table_text')
