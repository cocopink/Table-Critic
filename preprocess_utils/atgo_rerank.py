"""ATG 行/列单向重排预处理模块

提供 ATGO (仅行排) 和 ATGC (仅列排) 两种模式:
- ATGO: 仅基于行 ATG + QG-PPR 重排行顺序, 列顺序保持原样
- ATGC: 仅基于列 ATG + QG-PPR 重排列顺序, 行顺序保持原样

用法:
    from preprocess_utils.atgo_rerank import ATGOReranker, ATGCReranker

    # 仅行排
    row_reranker = ATGOReranker(cache_dir="./cache/atgo_rerank")
    dataset = row_reranker.rerank_batch(dataset)

    # 仅列排
    col_reranker = ATGCReranker(cache_dir="./cache/atgc_rerank")
    dataset = col_reranker.rerank_batch(dataset)
"""

import os
import pickle
from typing import Dict, List, Optional

from tqdm import tqdm

from table_structure import build_row_atg, build_col_atg, rank_rows, rank_columns, rerank_table


def _order_changed(order: List[int], n: int) -> bool:
    """判断排序是否与恒等序列不同。

    Args:
        order: 排序结果列表
        n: 原始元素数量

    Returns:
        True 表示顺序发生了改变
    """
    return order != list(range(n))


class ATGOReranker:
    """基于行 ATG + QG-PPR 的仅行重排器

    与 ATGReranker 的区别:
    - 仅构建行中心 ATG, 不构建列中心 ATG
    - 仅计算行排序, 列顺序保持原始顺序
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir

    def rerank_sample(self, sample: Dict, idx: int = 0) -> Dict:
        """对单个样本执行 ATGO 重排, 结果写入 sample["atgo_reranked_table"]。

        同时设置 sample["_atgo_order_changed"] 标记行顺序是否实际改变。

        Args:
            sample: 数据集样本, 需包含 table_text / table 和 question / statement。
            idx: 样本在数据集中的索引, 用于 sample_id 缺失时的缓存回退。

        Returns:
            同一 sample 对象（原地修改）。
        """
        table_text = sample.get("table", sample.get("table_text", []))
        question = sample.get("question", sample.get("statement", ""))
        sample_id = sample.get("id") or sample.get("table_id") or f"idx_{idx}"

        if not question or not table_text:
            sample["atgo_reranked_table"] = table_text
            sample["_atgo_order_changed"] = False
            return sample

        # 尝试从缓存加载
        if self.cache_dir:
            cache_path = os.path.join(self.cache_dir, f"{sample_id}.pkl")
            if os.path.exists(cache_path):
                reranked = pickle.load(open(cache_path, "rb"))
                sample["atgo_reranked_table"] = reranked
                return sample

        try:
            row_atg = build_row_atg(table_text)
            row_order = rank_rows(row_atg, question)
            num_rows = len(table_text) - 1
            col_order = list(range(len(table_text[0])))
            reranked = rerank_table(table_text, row_order, col_order)
            sample["atgo_reranked_table"] = reranked
            sample["_atgo_order_changed"] = _order_changed(row_order, num_rows)

            if self.cache_dir:
                os.makedirs(self.cache_dir, exist_ok=True)
                pickle.dump(reranked, open(cache_path, "wb"))
        except Exception as e:
            print(f"[ATGO] Rerank failed for sample {sample_id}: {e}")
            sample["atgo_reranked_table"] = table_text
            sample["_atgo_order_changed"] = False

        return sample

    def rerank_batch(self, dataset: List[Dict]) -> List[Dict]:
        for idx, sample in tqdm(enumerate(dataset), desc="ATGO Reranking"):
            self.rerank_sample(sample, idx=idx)
        return dataset


class ATGCReranker:
    """基于列 ATG + QG-PPR 的仅列重排器

    与 ATGReranker 的区别:
    - 仅构建列中心 ATG, 不构建行中心 ATG
    - 仅计算列排序, 行顺序保持原始顺序
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir

    def rerank_sample(self, sample: Dict, idx: int = 0) -> Dict:
        """对单个样本执行 ATGC 重排, 结果写入 sample["atgc_reranked_table"]。

        同时设置 sample["_atgc_order_changed"] 标记列顺序是否实际改变。

        Args:
            sample: 数据集样本, 需包含 table_text / table 和 question / statement。
            idx: 样本在数据集中的索引, 用于 sample_id 缺失时的缓存回退。

        Returns:
            同一 sample 对象（原地修改）。
        """
        table_text = sample.get("table", sample.get("table_text", []))
        question = sample.get("question", sample.get("statement", ""))
        sample_id = sample.get("id") or sample.get("table_id") or f"idx_{idx}"

        if not question or not table_text:
            sample["atgc_reranked_table"] = table_text
            sample["_atgc_order_changed"] = False
            return sample

        # 尝试从缓存加载
        if self.cache_dir:
            cache_path = os.path.join(self.cache_dir, f"{sample_id}.pkl")
            if os.path.exists(cache_path):
                reranked = pickle.load(open(cache_path, "rb"))
                sample["atgc_reranked_table"] = reranked
                return sample

        try:
            col_atg = build_col_atg(table_text)
            col_order = rank_columns(col_atg, question)
            num_cols = len(table_text[0])
            row_order = list(range(len(table_text) - 1))
            reranked = rerank_table(table_text, row_order, col_order)
            sample["atgc_reranked_table"] = reranked
            sample["_atgc_order_changed"] = _order_changed(col_order, num_cols)

            if self.cache_dir:
                os.makedirs(self.cache_dir, exist_ok=True)
                pickle.dump(reranked, open(cache_path, "wb"))
        except Exception as e:
            print(f"[ATGC] Rerank failed for sample {sample_id}: {e}")
            sample["atgc_reranked_table"] = table_text
            sample["_atgc_order_changed"] = False

        return sample

    def rerank_batch(self, dataset: List[Dict]) -> List[Dict]:
        for idx, sample in tqdm(enumerate(dataset), desc="ATGC Reranking"):
            self.rerank_sample(sample, idx=idx)
        return dataset
