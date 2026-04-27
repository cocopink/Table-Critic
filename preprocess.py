#!/usr/bin/env python3
"""Preprocessing entry point for Table-Critic table flatten module.

This script provides a CLI to preprocess datasets by flattening tables
with compound headers before running the main Table-Critic pipeline.

Usage:
    python preprocess.py --dataset_path data.jsonl --output_path output.jsonl --task_type TableQA
"""

import argparse
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


def main():
    """Main entry point for preprocessing CLI."""
    parser = argparse.ArgumentParser(
        description='Preprocess Table-Critic datasets by flattening compound table headers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python preprocess.py \\
      --dataset_path thought/TableQA/data/wikitq/test_lower.jsonl \\
      --output_path /tmp/test_flatten.jsonl \\
      --task_type TableQA

  # Force refresh (skip cache)
  python preprocess.py \\
      --dataset_path data.jsonl \\
      --output_path output.jsonl \\
      --task_type TableQA \\
      --force_refresh

  # Generate statistics
  python preprocess.py \\
      --dataset_path data.jsonl \\
      --output_path output.jsonl \\
      --task_type TableQA \\
      --stats_path stats.json
        """
    )

    parser.add_argument(
        '--dataset_path',
        type=str,
        required=True,
        help='Path to input JSONL dataset file'
    )

    parser.add_argument(
        '--output_path',
        type=str,
        required=True,
        help='Path to output flattened JSONL file'
    )

    parser.add_argument(
        '--task_type',
        type=str,
        required=True,
        choices=['TableQA', 'TableFV'],
        help='Type of task (TableQA or TableFV)'
    )

    parser.add_argument(
        '--force_refresh',
        action='store_true',
        help='Force reprocessing even if cached results exist'
    )

    parser.add_argument(
        '--stats_path',
        type=str,
        default=None,
        help='Optional path to save processing statistics as JSON'
    )

    args = parser.parse_args()

    # Validate input file exists
    if not os.path.exists(args.dataset_path):
        print(f"Error: Dataset file not found: {args.dataset_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Table-Critic Preprocessing Pipeline")
    print(f"=" * 50)
    print(f"Task Type: {args.task_type}")
    print(f"Input: {args.dataset_path}")
    print(f"Output: {args.output_path}")
    print(f"Force Refresh: {args.force_refresh}")
    print()

    # Load dataset
    print("Loading dataset...")
    try:
        dataset = load_jsonl(args.dataset_path)
        print(f"Loaded {len(dataset)} samples")
    except Exception as e:
        print(f"Error loading dataset: {e}", file=sys.stderr)
        sys.exit(1)

    # Check cache
    cache_path = args.output_path + '.cache'
    if not args.force_refresh:
        print("Checking cache...")
        if check_cache(cache_path):
            print("Cache hit! Loading cached results...")
            cached_data = load_cache(cache_path)
            save_jsonl(cached_data, args.output_path)

            stats = generate_stats(dataset, cached_data, args.task_type)
            print(f"Preprocessing complete (from cache)")
            print(f"  Total samples: {stats['total_samples']}")
            print(f"  Tables flattened: {stats['tables_flattened']}")
            print(f"  Tables skipped: {stats['tables_skipped']}")

            if args.stats_path:
                save_jsonl([stats], args.stats_path)
                print(f"Statistics saved to: {args.stats_path}")

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
        save_jsonl(flattened_dataset, args.output_path)
        print(f"Flattened data saved to: {args.output_path}")
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
    stats = generate_stats(dataset, flattened_dataset, args.task_type)
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

    if args.stats_path:
        save_jsonl([stats], args.stats_path)
        print(f"Statistics saved to: {args.stats_path}")

    print()
    print("Preprocessing complete!")


if __name__ == '__main__':
    main()
