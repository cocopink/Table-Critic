"""Detect compound headers in tables."""

from typing import List, Tuple, Dict

# Separator priority order (most common first)
SEPARATOR_PRIORITY = ['/', '\n', ' - ', '-', '|', ',']

def has_compound_headers(table: List[List]) -> bool:
    """Check if table has compound column headers."""
    raise NotImplementedError("To be implemented in Task 2")

def find_compound_columns(table: List[List]) -> List[int]:
    """Find indices of compound columns."""
    raise NotImplementedError("To be implemented in Task 2")

def get_separator(header_cell: str) -> str:
    """Get the separator used in a header cell."""
    raise NotImplementedError("To be implemented in Task 2")
