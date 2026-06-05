"""Tests for TableAnalyzer module."""

import pytest
from agents.table_analyzer import TableAnalyzer, format_analysis_for_prompt


def _make_sample(table, question="What is the score?"):
    return {"table": table, "question": question}


def test_analyze_simple_table():
    sample = _make_sample([
        ["name", "score"],
        ["Alice", "90"],
        ["Bob", "85"],
    ])
    analysis = TableAnalyzer().analyze(sample)
    assert "answer_format_hint" in analysis
    assert "EXACT values" in analysis["answer_format_hint"]
    assert "column_normalizations" in analysis
    assert "format_normalizations" in analysis
    assert "header_tree_text" in analysis


def test_analyze_compound_headers():
    sample = _make_sample([
        ["name", "city/country"],
        ["Alice", "Berlin/Germany"],
        ["Bob", "Paris/France"],
    ])
    analysis = TableAnalyzer().analyze(sample)
    assert "city/country" in analysis["header_tree_text"]
    assert "compound" in analysis["header_tree_text"]


def test_analyze_mixed_format():
    sample = _make_sample([
        ["round", "winner"],
        ["heat 1", "Alice"],
        ["heat 2", "Bob"],
        ["DNS", ""],
    ])
    analysis = TableAnalyzer().analyze(sample)
    # round column should trigger format normalization (heat 1 → 1, heat 2 → 2, DNS → None)
    assert len(analysis["format_normalizations"]) > 0


def test_analyze_column_normalization():
    sample = _make_sample([
        ["name", "pts"],
        ["Alice", "25"],
        ["Bob", "30"],
    ], question="How many points did Alice score?")
    analysis = TableAnalyzer().analyze(sample)
    # "points" should fuzzy-match against "pts" column values
    norm_found = any(n["column_name"] == "pts" for n in analysis["column_normalizations"])
    assert norm_found


def test_format_analysis_for_prompt_empty():
    analysis = {"header_tree_text": "", "column_normalizations": [], "format_normalizations": {}}
    assert format_analysis_for_prompt(analysis) == ""


def test_format_analysis_for_prompt_with_data():
    analysis = {
        "header_tree_text": "Column Hierarchy:\n  date/time (compound)",
        "column_normalizations": [{"hint": 'Column "pts" has similar values: 25, 30'}],
        "format_normalizations": {},
    }
    text = format_analysis_for_prompt(analysis)
    assert "date/time" in text
    assert "pts" in text


def test_analyze_empty_table():
    sample = _make_sample([], "test question")
    analysis = TableAnalyzer().analyze(sample)
    assert analysis["header_tree_text"] == ""
    assert analysis["column_normalizations"] == []
    assert analysis["format_normalizations"] == {}


def test_analyze_with_statement_key():
    sample = {"table": [["a", "b"], ["1", "2"]], "statement": "test"}
    analysis = TableAnalyzer().analyze(sample)
    assert "answer_format_hint" in analysis
