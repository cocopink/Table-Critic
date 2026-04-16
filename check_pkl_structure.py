#!/usr/bin/env python3
"""
检查 pkl 文件结构
"""

import pickle
import json
from pathlib import Path


def check_pkl_structure(pkl_path: str):
    """检查 pkl 文件结构"""
    print(f"\n检查文件: {pkl_path}")
    print("=" * 60)

    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)

    print(f"数据类型: {type(data)}")
    print(f"数据长度: {len(data)}")

    if isinstance(data, list) and len(data) > 0:
        print(f"\n第一个元素类型: {type(data[0])}")

        if isinstance(data[0], dict):
            print(f"\n第一个元素的键: {list(data[0].keys())}")
            print(f"\n第一个元素的内容:")
            for key, value in data[0].items():
                if isinstance(value, (str, int, float, bool)):
                    print(f"  {key}: {value}")
                elif isinstance(value, list) and len(value) > 0:
                    print(f"  {key}: [list with {len(value)} items]")
                elif isinstance(value, dict):
                    print(f"  {key}: {{dict with {len(value)} keys}}")
                else:
                    print(f"  {key}: {type(value)}")

        # 检查前5个元素
        print(f"\n前5个元素的键:")
        for i, item in enumerate(data[:5]):
            if isinstance(item, dict):
                print(f"  [{i}] {list(item.keys())}")
            else:
                print(f"  [{i}] {type(item)}")

    # 统计信息
    if isinstance(data, list):
        print(f"\n数据统计:")
        print(f"  总记录数: {len(data)}")

        # 检查是否有 None 值
        none_count = sum(1 for item in data if item is None)
        if none_count > 0:
            print(f"  None 值数量: {none_count}")

        # 检查有效的字典记录
        valid_dicts = [item for item in data if isinstance(item, dict)]
        print(f"  有效字典记录: {len(valid_dicts)}")

        if valid_dicts:
            # 统计键的出现频率
            from collections import Counter
            key_counter = Counter()
            for item in valid_dicts:
                key_counter.update(item.keys())

            print(f"\n键的出现频率:")
            for key, count in key_counter.most_common():
                percentage = (count / len(valid_dicts)) * 100
                print(f"  {key}: {count} ({percentage:.1f}%)")


def main():
    """主函数"""
    # 检查两个 pkl 文件
    current_pkl = "results/refine/wikitq/sota/gpt-5.4/final_result.pkl"
    reference_pkl = "/home/ubuntu/mnt/lx/Table-Critic/results/refine/wikitq/gpt-5.4/final_result.pkl"

    check_pkl_structure(current_pkl)
    check_pkl_structure(reference_pkl)


if __name__ == "__main__":
    main()
