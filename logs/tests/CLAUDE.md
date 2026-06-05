# Tests 模块文档

[← 返回根文档](../CLAUDE.md) > **tests**

> 最后更新：2026-05-21 15:15:47

---

## 模块职责

单元测试模块，使用 **pytest** 框架，覆盖预处理工具包和 TableAnalyzer。

---

## 测试覆盖

| 测试文件 | 测试数 | 覆盖模块 |
|----------|--------|----------|
| `test_flatten.py` | 15 | flatten + detect + cache |
| `test_column_norm.py` | 14 | column_norm |
| `test_header_tree.py` | 6 | header_tree |
| `test_table_analyzer.py` | 8 | table_analyzer |
| **总计** | **43** | |

---

## 运行测试

```bash
pytest tests/ -v
```

> 注意：`requirements.txt` 缺少 pytest，需手动安装 `pip install pytest`

---

## 相关文件

- `tests/test_flatten.py`
- `tests/test_column_norm.py`
- `tests/test_header_tree.py`
- `tests/test_table_analyzer.py`
- `tests/test_verifier.py` (新增，未完善)
