#!/usr/bin/env python3
"""Preprocessing entry point for Table-Critic table flatten module.

This script provides a CLI to preprocess datasets by flattening tables
with compound headers before running the main Table-Critic pipeline.

Usage:
    python preprocess.py --dataset_path data.jsonl --output_path output.jsonl --task_type TableQA
"""

import fire
import json
import os
import sys
from typing import List, Dict, Any

from preprocess_utils import flatten_dataset, check_cache, load_cache, save_cache


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load data from JSONL file.

    Args:
        file_path: Path to JSONL file

    Returns:
        List of dictionaries containing the data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line {line_num}: {e}")
                continue

    if not data:
        raise ValueError(f"No valid data found in {file_path}")

    return data


def save_jsonl(data: List[Dict[str, Any]], file_path: str) -> None:
    """Save data to JSONL file.

    Args:
        data: List of dictionaries to save
        file_path: Output file path
    """
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def generate_stats(original_data: List[Dict], flattened_data: List[Dict],
                   task_type: str) -> Dict[str, Any]:
    """Generate statistics about the flattening process.

    Args:
        original_data: Original dataset before flattening
        flattened_data: Dataset after flattening
        task_type: Type of task ('TableQA' or 'TableFV')

    Returns:
        Dictionary containing statistics
    """
    total_samples = len(flattened_data)
    flattened_count = sum(
        1 for item in flattened_data
        if 'flatten_metadata' in item and item['flatten_metadata'].get('flattened', False)
    )

    stats = {
        'task_type': task_type,
        'total_samples': total_samples,
        'tables_flattened': flattened_count,
        'tables_skipped': total_samples - flattened_count,
        'flatten_rate': flattened_count / total_samples if total_samples > 0 else 0,
    }

    # Add shape statistics for flattened tables
    if flattened_count > 0:
        original_shapes = []
        new_shapes = []

        for item in flattened_data:
            if 'flatten_metadata' in item and item['flatten_metadata'].get('flattened', False):
                meta = item['flatten_metadata']
                if 'original_shape' in meta:
                    original_shapes.append(meta['original_shape'])
                if 'new_shape' in meta:
                    new_shapes.append(meta['new_shape'])

        if original_shapes and new_shapes:
            avg_original_cols = sum(s[1] for s in original_shapes) / len(original_shapes)
            avg_new_cols = sum(s[1] for s in new_shapes) / len(new_shapes)
            stats['avg_original_columns'] = round(avg_original_cols, 2)
            stats['avg_new_columns'] = round(avg_new_cols, 2)
            stats['avg_columns_added'] = round(avg_new_cols - avg_original_cols, 2)

    return stats


def main(
    dataset_path: str = "thought/TableQA/data/wikitq/test_lower.jsonl",
    output_path: str = "thought/TableQA/data/wikitq/test_flatten.jsonl",
    task_type: str = "TableQA",
    force_refresh: bool = False,
    stats_path: str = None,
    analysis_only: bool = False,
) -> None:
    """Main preprocessing function.

    Args:
        dataset_path: Path to input JSONL dataset file
        output_path: Path to output flattened JSONL file
        task_type: Type of task (TableQA or TableFV)
        force_refresh: Force reprocessing even if cached results exist
        stats_path: Optional path to save processing statistics as JSON
    """
    # Validate task_type
    if task_type not in ['TableQA', 'TableFV']:
        print(f"Error: task_type must be 'TableQA' or 'TableFV', got '{task_type}'", file=sys.stderr)
        sys.exit(1)

    # Validate input file exists
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset file not found: {dataset_path}", file=sys.stderr)
        sys.exit(1)

    # --- analysis_only mode (Stage 0.5) ---
    if analysis_only:
        print(f"Table-Critic Analysis Pipeline (--analysis_only)")
        print(f"=" * 50)
        print(f"Task Type: {task_type}")
        print(f"Input:  {dataset_path}")
        print(f"Output: {output_path}")
        print()

        from agents.table_analyzer import TableAnalyzer

        analyzer = TableAnalyzer()
        dataset = load_jsonl(dataset_path)
        analyzed_count = 0
        for item in dataset:
            item["table_analysis"] = analyzer.analyze(item)
            analyzed_count += 1

        save_jsonl(dataset, output_path)
        print(f"Analyzed {analyzed_count} samples → {output_path}")
        return

    print(f"Table-Critic Preprocessing Pipeline")
    print(f"=" * 50)
    print(f"Task Type: {task_type}")
    print(f"Input: {dataset_path}")
    print(f"Output: {output_path}")
    print(f"Force Refresh: {force_refresh}")
    print()

    # Load dataset
    print("Loading dataset...")
    try:
        dataset = load_jsonl(dataset_path)
        print(f"Loaded {len(dataset)} samples")
    except Exception as e:
        print(f"Error loading dataset: {e}", file=sys.stderr)
        sys.exit(1)

    # Check cache
    cache_path = output_path + '.cache'
    if not force_refresh:
        print("Checking cache...")
        if check_cache(cache_path):
            print("Cache hit! Loading cached results...")
            cached_data = load_cache(cache_path)
            save_jsonl(cached_data, output_path)

            stats = generate_stats(dataset, cached_data, task_type)
            print(f"Preprocessing complete (from cache)")
            print(f"  Total samples: {stats['total_samples']}")
            print(f"  Tables flattened: {stats['tables_flattened']}")
            print(f"  Tables skipped: {stats['tables_skipped']}")

            if stats_path:
                save_jsonl([stats], stats_path)
                print(f"Statistics saved to: {stats_path}")

            sys.exit(0)

    # Process dataset
    print("Flattening tables...")
    try:
        flattened_dataset = flatten_dataset(dataset)
    except Exception as e:
        print(f"Error during flattening: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Save results
    print("Saving results...")
    try:
        save_jsonl(flattened_dataset, output_path)
        print(f"Flattened data saved to: {output_path}")
    except Exception as e:
        print(f"Error saving results: {e}", file=sys.stderr)
        sys.exit(1)

    # Save cache
    print("Saving cache...")
    try:
        save_cache(flattened_dataset, cache_path)
        print(f"Cache saved to: {cache_path}")
    except Exception as e:
        print(f"Warning: Failed to save cache: {e}")

    # Generate and save statistics
    stats = generate_stats(dataset, flattened_dataset, task_type)
    print()
    print(f"Preprocessing Statistics:")
    print(f"  Total samples: {stats['total_samples']}")
    print(f"  Tables flattened: {stats['tables_flattened']}")
    print(f"  Tables skipped: {stats['tables_skipped']}")
    print(f"  Flatten rate: {stats['flatten_rate']:.2%}")

    if 'avg_original_columns' in stats:
        print(f"  Avg original columns: {stats['avg_original_columns']}")
        print(f"  Avg new columns: {stats['avg_new_columns']}")
        print(f"  Avg columns added: {stats['avg_columns_added']}")

    if stats_path:
        save_jsonl([stats], stats_path)
        print(f"Statistics saved to: {stats_path}")

    print()
    print("Preprocessing complete!")


if __name__ == '__main__':
    fire.Fire(main)
