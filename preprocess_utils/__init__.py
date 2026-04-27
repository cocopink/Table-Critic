"""Preprocessing utilities for Table-Critic flatten module."""

from .detect import has_compound_headers, find_compound_columns
from .flatten import flatten_table, flatten_dataset
from .cache import check_cache, load_cache, save_cache

__all__ = [
    'has_compound_headers',
    'find_compound_columns',
    'flatten_table',
    'flatten_dataset',
    'check_cache',
    'load_cache',
    'save_cache',
]
