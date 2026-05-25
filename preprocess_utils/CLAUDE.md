# Preprocess Utils 模块文档

[← 返回根文档](../CLAUDE.md) > **preprocess_utils**

> 最后更新：2026-05-21 15:15:47

---

## 变更记录 (Changelog)

### 2026-05-21 (精简重构)
- 无内容变更，仅更新时间戳和导航

### 2026-05-10
- 初始化，深度扫描全部 5 个子模块

---

## 模块职责

零 LLM 成本的表格预处理工具包，在 Stage 0（Flatten）和 Stage 0.5（TableAnalyzer）中使用。

---

## 对外接口

### detect.py - 复合表头检测

```python
SEPARATOR_PRIORITY = ['/', '\\n', '\n', ' - ', '-', '|', ',']

def has_compound_headers(table: List[List]) -> bool
def find_compound_columns(table: List[List]) -> List[int]
def get_separator(header_cell: str) -> str
```

### flatten.py - 表格拆分

```python
def split_cell_value(value, primary_separator, expected_count) -> List[str]
    """三级降级策略：主分隔符 → 空格 → 兜底复制"""

def flatten_table(table) -> Tuple[List[List], Dict]
    """拆分复合表头表格，返回 (flattened_table, metadata)"""

def flatten_dataset(dataset) -> List[Dict]
    """批量处理，支持 'table_text'(TableQA) 和 'table'(TableFV) 键"""
```

### column_norm.py - 列值标准化

```python
def fuzzy_match_values(question_keyword, column_values, threshold=0.8) -> List[str]
    """基于 pylcs LCS 的模糊匹配"""

def normalize_column(question_keywords, table_text, column_idx) -> Optional[ColumnNormalization]
def extract_numeric_from_mixed(value) -> Optional[float]
def detect_mixed_format_column(values) -> bool
def normalize_column_format(values) -> Dict[str, Optional[float]]
```

### header_tree.py - 复合表头树

```python
class HeaderTree:
    @classmethod
    def build(cls, table_text: List[List]) -> 'HeaderTree'
    def parse_compound_cells(self, table_text) -> Dict[int, List[Dict]]
    def serialize_for_prompt(self, include_cells=True) -> str
```

### cache.py - JSONL 缓存

```python
def check_cache(cache_path) -> bool
def load_cache(cache_path) -> List[Dict]
def save_cache(samples, cache_path) -> None
```

---

## 依赖关系

```
preprocess_utils/__init__.py
  ├── detect.py      (被 flatten.py、header_tree.py 依赖)
  ├── flatten.py     (依赖 detect.py)
  ├── cache.py
  ├── header_tree.py (依赖 detect.py)
  └── column_norm.py (被 agents/table_analyzer.py 依赖)
```

---

## 测试

| 文件 | 测试数 |
|------|--------|
| `tests/test_flatten.py` | 15 |
| `tests/test_column_norm.py` | 14 |
| `tests/test_header_tree.py` | 6 |

```bash
pytest tests/test_flatten.py tests/test_column_norm.py tests/test_header_tree.py -v
```

---

## 相关文件

- `preprocess_utils/__init__.py`
- `preprocess_utils/detect.py`
- `preprocess_utils/flatten.py`
- `preprocess_utils/cache.py`
- `preprocess_utils/column_norm.py`
- `preprocess_utils/header_tree.py`
- `preprocess.py` - 命令行入口
