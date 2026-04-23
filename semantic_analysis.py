#!/usr/bin/env python3
"""
语义化Bad Case分析脚本
使用官方评估函数，按语义错误类型分类
"""

import pickle
import os
import re
import unicodedata
from typing import Dict, List
from collections import defaultdict

# ===== 复制官方评估函数 =====

def normalize(x):
    if not isinstance(x, str):
        x = str(x)
    x = ''.join(c for c in unicodedata.normalize('NFKD', x)
                if unicodedata.category(c) != 'Mn')
    x = re.sub(r"[''`]", "'", x)
    x = re.sub(r'[\""]', '"', x)
    x = re.sub(r"[‑–—−]", "-", x)
    while True:
        old_x = x
        x = re.sub(r"((?<!^)\[[^\]]*\]|\[\d+\]|[•♦†‡*#+])*$", "", x.strip())
        x = re.sub(r"(?<!^)( \([^)]*\))*$", "", x.strip())
        x = re.sub(r'^"([^"]*)"$', r'\1', x.strip())
        if x == old_x:
            break
    if x and x[-1] == '.':
        x = x[:-1]
    x = re.sub(r'\s+', ' ', x, flags=re.U).lower().strip()
    return x

class Value:
    _normalized = None
    @property
    def normalized(self):
        return self._normalized

class StringValue(Value):
    def __init__(self, content):
        self._normalized = normalize(content)
    def match(self, other):
        return self.normalized == other.normalized

class NumberValue(Value):
    def __init__(self, amount, original_string=None):
        if abs(amount - round(amount)) < 1e-6:
            self._amount = int(amount)
        else:
            self._amount = float(amount)
        self._normalized = str(self._amount) if not original_string else normalize(original_string)
    @property
    def amount(self):
        return self._amount
    def match(self, other):
        if self.normalized == other.normalized:
            return True
        if isinstance(other, NumberValue):
            return abs(self.amount - other.amount) < 1e-6
        return False
    @staticmethod
    def parse(text):
        try:
            return int(text)
        except:
            try:
                return float(text)
            except:
                return None

def to_value(original_string, corenlp_value=None):
    if isinstance(original_string, Value):
        return original_string
    if not corenlp_value:
        corenlp_value = original_string
    amount = NumberValue.parse(corenlp_value)
    if amount is not None:
        return NumberValue(amount, original_string)
    return StringValue(original_string)

def to_value_list(original_strings, corenlp_values=None):
    if corenlp_values is not None:
        return list(set(to_value(x, y) for (x, y) in zip(original_strings, corenlp_values)))
    else:
        return list(set(to_value(x) for x in original_strings))

def check_denotation(target_values, predicted_values):
    if len(target_values) != len(predicted_values):
        return False
    for target in target_values:
        if not any(target.match(pred) for pred in predicted_values):
            return False
    return True

def tsv_unescape(x):
    return x.replace(r'\n', '\n').replace(r'\p', '|').replace('\\\\', '\\')

def tsv_unescape_list(x):
    return [tsv_unescape(y) for y in x.split('|')]

def wikitq_match_func(sample, target_values, strategy="top"):
    """官方WikiTQ评估函数"""
    results = sample["chain"][-1]["parameter_and_conf"]
    if strategy == "top":
        res = results[0][0]
    else:
        raise NotImplementedError
    pred_answer = [res.lower()] if '|' not in res else [r for r in res.lower().split('|')]
    pred_answer = to_value_list(pred_answer)
    return check_denotation(target_values, pred_answer)

def tabfact_match_func(sample, strategy="top"):
    """官方TabFact评估函数"""
    results = sample["chain"][-1]["parameter_and_conf"]
    if strategy == "top":
        res = results[0][0]
    else:
        raise NotImplementedError
    res = res.lower()
    if res == "true":
        res = "yes"
    if res == "false":
        res = "no"
    if res == "yes" and sample["label"] == 1:
        return True
    elif res == "no" and sample["label"] == 0:
        return True
    else:
        return False

# ===== 语义化错误分类 =====

def classify_error_semantic(question: str, gold: str, pred: str) -> str:
    """
    语义化错误分类
    关注错误背后的语义原因，而不是表面形式
    """
    question = question.lower()
    gold = str(gold).strip().lower()
    pred = str(pred).strip().lower()

    # 1. 数值计算与理解错误
    if any(kw in question for kw in ['how many', 'count', 'number of', 'total', 'sum', 'average']):
        if gold.isdigit() and pred.isdigit():
            return '数值计算错误'
        if gold.replace('.', '').isdigit() and pred.replace('.', '').isdigit():
            return '数值计算错误'

    # 2. 排序与比较错误
    if any(kw in question for kw in ['most', 'least', 'highest', 'lowest', 'best', 'worst', 'top', 'bottom', 'first', 'last', 'max', 'min']):
        return '排序比较错误'

    # 3. 实体识别与匹配错误
    if any(kw in question for kw in ['who', 'which', 'what', 'name', 'where', 'when']):
        return '实体识别错误'

    # 4. 时间理解错误
    if any(kw in question for kw in ['when', 'year', 'date', 'time', 'how long', 'duration']):
        return '时间理解错误'

    # 5. 逻辑推理错误
    if any(kw in question for kw in ['why', 'because', 'reason', 'cause']):
        return '逻辑推理错误'

    # 6. 验证判断错误（TabFact）
    if gold in ['true', 'false', 'yes', 'no'] and pred in ['true', 'false', 'yes', 'no']:
        return '事实验证错误'

    # 7. 格式转换错误（答案形式正确但格式不对）
    if '|' in pred:
        # 检查是否只是格式问题
        gold_parts = set(gold.split('|'))
        pred_parts = set(pred.split('|'))
        if gold_parts == pred_parts:
            return '答案格式错误'

    # 8. 多答案处理不当
    if '|' in pred:
        return '多答案处理错误'

    # 9. 其他理解错误
    return '理解错误'

# ===== 辅助函数 =====

def load_target_values_map(tagged_data_path='thought/TableQA/data/wikitq/tagged_data'):
    """加载目标值映射"""
    target_values_map = {}
    if not os.path.exists(tagged_data_path):
        return target_values_map
    for basename in os.listdir(tagged_data_path):
        if basename[0] == '.':
            continue
        filepath = os.path.join(tagged_data_path, basename)
        with open(filepath, 'r', encoding='utf8') as fin:
            header = fin.readline().rstrip('\n').split('\t')
            for line in fin:
                stuff = dict(zip(header, line.rstrip('\n').split('\t')))
                ex_id = stuff['id']
                original_strings = tsv_unescape_list(stuff['targetValue'])
                canon_strings = tsv_unescape_list(stuff['targetCanon'])
                target_values_map[ex_id] = to_value_list(original_strings, canon_strings)
    return target_values_map

def load_original_tables(jsonl_path='thought/TableQA/data/wikitq/test_lower.jsonl'):
    """加载原始表格数据"""
    original_tables = {}
    if not os.path.exists(jsonl_path):
        return original_tables

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = eval(line)
                sample_id = data.get('ids', '')
                if sample_id:
                    original_tables[sample_id] = {
                        'table_text': data.get('table_text', []),
                        'answer': data.get('answer', [])
                    }
            except Exception:
                continue

    print(f"加载了 {len(original_tables)} 个原始表格")
    return original_tables

def load_tabfact_original_tables(jsonl_path='thought/TableFV/data/tabfact/test.jsonl'):
    """加载TabFact原始表格数据"""
    original_tables = {}
    if not os.path.exists(jsonl_path):
        return original_tables

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            try:
                data = eval(line)
                sample_id = data.get('id', str(idx))
                if sample_id:
                    original_tables[sample_id] = {
                        'table_text': data.get('table_text', []),
                        'label': data.get('label', None)
                    }
            except Exception:
                continue

    print(f"加载了 {len(original_tables)} 个TabFact原始表格")
    return original_tables

class SemanticAnalyzer:
    """语义化分析器"""

    def format_chain_full(self, chain: List) -> str:
        """完整格式化思维链"""
        if not chain:
            return "无思维链"
        steps = []
        for i, step in enumerate(chain):
            if isinstance(step, dict):
                op = step.get('operation_name', 'unknown')
                thought = step.get('thought', '')
                params = step.get('parameter_and_conf', [])

                step_desc = f"步骤 {i+1}: {op}\n"
                if thought:
                    step_desc += f"  思考: {thought}\n"
                if params:
                    step_desc += f"  参数: {params}\n"
                steps.append(step_desc)
        return "\n".join(steps) if steps else "无有效思维链"

    def format_table_full(self, table: List) -> str:
        """完整格式化表格"""
        if not table:
            return "无表格数据"
        if isinstance(table, list):
            lines = []
            for row in table:
                if isinstance(row, list):
                    lines.append(" | ".join(str(c) for c in row))
                else:
                    lines.append(str(row))
            return "\n".join(lines)
        return str(table)

    def format_original_table(self, original_data: Dict) -> str:
        """格式化原始表格数据"""
        if not original_data or 'table_text' not in original_data:
            return "无原始表格数据"

        table_text = original_data['table_text']
        if not table_text:
            return "无原始表格内容"

        lines = []
        for row in table_text:
            if isinstance(row, list):
                lines.append(" | ".join(str(c) for c in row))
            else:
                lines.append(str(row))
        return "\n".join(lines)

def analyze_project(project_path: str, project_name: str, analyzer: SemanticAnalyzer, target_values_map: dict, original_tables: dict, tabfact_original_tables: dict):
    """分析单个项目"""

    print(f"\n{'='*60}")
    print(f"分析项目: {project_name}")
    print(f"{'='*60}")

    # 分析WikiTQ
    print("\n[1/2] 分析WikiTQ...")
    wikitq_path = f"{project_path}/results/refine/wikitq/sota/gpt-5.4/final_result.pkl"
    if not os.path.exists(wikitq_path):
        # 尝试其他路径
        wikitq_path = f"{project_path}/results/refine/wikitq/gpt-5.4/final_result.pkl"

    if os.path.exists(wikitq_path):
        with open(wikitq_path, 'rb') as f:
            wikitq_data = pickle.load(f)

        wikitq_bad_cases = []
        wikitq_error_types = defaultdict(list)

        for item in wikitq_data:
            if item is None:
                continue
            sample_id = item.get('ids', item.get('id', ''))
            if sample_id not in target_values_map:
                continue

            is_correct = wikitq_match_func(item, target_values_map[sample_id], strategy="top")
            if not is_correct:
                answer_list = item.get('answer', [])
                gold_answer = '|'.join(str(a) for a in answer_list) if answer_list else ''

                chain = item.get('chain', [])
                pred_answer = ''
                if chain and len(chain) > 0:
                    last_op = chain[-1]
                    if isinstance(last_op, dict):
                        param_conf = last_op.get('parameter_and_conf', [])
                        if param_conf and len(param_conf) > 0:
                            pred_answer = str(param_conf[0][0]) if param_conf[0] else ''

                error_type = classify_error_semantic(
                    item.get('statement', ''),
                    str(gold_answer),
                    pred_answer
                )

                original_table = original_tables.get(sample_id, {})

                case = {
                    'uid': sample_id,
                    'question': item.get('statement', ''),
                    'gold': str(gold_answer),
                    'pred': pred_answer,
                    'error_type': error_type,
                    'table': item.get('table_text', []),
                    'original_table': original_table,
                    'chain': chain,
                }

                wikitq_bad_cases.append(case)
                wikitq_error_types[error_type].append(sample_id)

        print(f"WikiTQ错误案例: {len(wikitq_bad_cases)}")
    else:
        print(f"未找到WikiTQ结果文件: {wikitq_path}")
        wikitq_bad_cases = []
        wikitq_error_types = defaultdict(list)

    # 分析TabFact
    print("\n[2/2] 分析TabFact...")
    tabfact_path = f"{project_path}/results/refine/tabfact/sota/gpt-5.4/final_result.pkl"
    if not os.path.exists(tabfact_path):
        tabfact_path = f"{project_path}/results/refine/tabfact/gpt-5.4/final_result.pkl"

    if os.path.exists(tabfact_path):
        with open(tabfact_path, 'rb') as f:
            tabfact_data = pickle.load(f)

        tabfact_bad_cases = []
        tabfact_error_types = defaultdict(list)

        for item in tabfact_data:
            if item is None:
                continue

            is_correct = tabfact_match_func(item, strategy="top")

            if not is_correct:
                gold_label = item.get('label', None)

                chain = item.get('chain', [])
                pred_label = None
                if chain and len(chain) > 0:
                    last_op = chain[-1]
                    if isinstance(last_op, dict):
                        param_conf = last_op.get('parameter_and_conf', [])
                        if param_conf and len(param_conf) > 0:
                            pred_result = param_conf[0][0]
                            if isinstance(pred_result, str):
                                pred_result_lower = pred_result.lower().strip()
                                if pred_result_lower in ['true', 'yes', '1']:
                                    pred_label = 1
                                elif pred_result_lower in ['false', 'no', '0']:
                                    pred_label = 0

                # 使用语义化分类
                error_type = classify_error_semantic(
                    item.get('statement', ''),
                    str(bool(gold_label)),
                    str(bool(pred_label)) if pred_label is not None else 'unknown'
                )

                original_table = tabfact_original_tables.get(item.get('id', ''), {})

                case = {
                    'uid': item.get('id', 'unknown'),
                    'question': item.get('statement', ''),
                    'gold': str(bool(gold_label)),
                    'pred': str(bool(pred_label)) if pred_label is not None else 'unknown',
                    'error_type': error_type,
                    'table': item.get('table_text', []),
                    'original_table': original_table,
                    'chain': item.get('chain', []),
                }

                tabfact_bad_cases.append(case)
                tabfact_error_types[error_type].append(case['uid'])

        print(f"TabFact错误案例: {len(tabfact_bad_cases)}")
    else:
        print(f"未找到TabFact结果文件: {tabfact_path}")
        tabfact_bad_cases = []
        tabfact_error_types = defaultdict(list)

    return {
        'wikitq_cases': wikitq_bad_cases,
        'wikitq_errors': wikitq_error_types,
        'tabfact_cases': tabfact_bad_cases,
        'tabfact_errors': tabfact_error_types,
    }

def main():
    print("=" * 60)
    print("语义化Bad Case分析（使用官方评估函数）")
    print("=" * 60)

    analyzer = SemanticAnalyzer()

    # 加载共享数据
    print("\n加载目标值映射...")
    target_values_map = load_target_values_map()
    print(f"加载了 {len(target_values_map)} 个目标值")

    print("\n加载原始表格数据...")
    original_tables = load_original_tables('thought/TableQA/data/wikitq/test_lower.jsonl')
    tabfact_original_tables = load_tabfact_original_tables('thought/TableFV/data/tabfact/test.jsonl')

    # 分析当前项目
    current_project_path = '/home/ubuntu/mnt/lx/new_TC/Table-Critic'
    current_result = analyze_project(current_project_path, "当前项目", analyzer, target_values_map, original_tables, tabfact_original_tables)

    # 分析参考项目
    reference_project_path = '/home/ubuntu/mnt/lx/Table-Critic'
    reference_result = analyze_project(reference_project_path, "参考项目", analyzer, target_values_map, original_tables, tabfact_original_tables)

    # 生成报告
    print("\n生成语义化分析报告...")

    report = ["# Table-Critic 语义化Bad Case分析报告\n\n"]
    report.append("**生成时间**: 2026-04-21\n\n")
    report.append("**方法**: 使用官方评估函数（wikitq_match_func/tabfact_match_func）判断bad case\n\n")
    report.append("**特点**: 按语义错误类型分类，关注错误背后的原因\n\n")

    # ===== 第一部分：当前项目分析 =====
    report.append("## 第一部分：当前项目分析（new_TC）\n\n")

    # WikiTQ统计
    report.append("### WikiTQ 错误统计\n\n")
    report.append(f"- **错误案例总数**: {len(current_result['wikitq_cases'])}\n\n")
    report.append("#### 错误类型分布\n\n")
    for error_type, uids in sorted(current_result['wikitq_errors'].items()):
        report.append(f"- **{error_type}**: {len(uids)} 个\n")
    report.append("\n")

    # TabFact统计
    report.append("### TabFact 错误统计\n\n")
    report.append(f"- **错误案例总数**: {len(current_result['tabfact_cases'])}\n\n")
    report.append("#### 错误类型分布\n\n")
    for error_type, uids in sorted(current_result['tabfact_errors'].items()):
        report.append(f"- **{error_type}**: {len(uids)} 个\n")
    report.append("\n")

    # 当前项目详细案例
    report.append("### WikiTQ 错误案例展示（每种类型1-2个）\n\n")

    cases_by_type = defaultdict(list)
    for case in current_result['wikitq_cases']:
        cases_by_type[case['error_type']].append(case)

    for error_type in sorted(cases_by_type.keys()):
        cases = cases_by_type[error_type][:2]
        report.append(f"#### {error_type}\n\n")

        for i, case in enumerate(cases, 1):
            report.append(f"**案例 {i}**: `{case['uid']}`\n\n")
            report.append(f"**问题**: {case['question']}\n\n")
            report.append(f"**正确答案**: `{case['gold']}`\n\n")
            report.append(f"**预测答案**: `{case['pred']}`\n\n")
            report.append(f"**完整思维链**:\n```\n{analyzer.format_chain_full(case['chain'])}\n```\n\n")
            report.append(f"**完整表格**:\n```\n{analyzer.format_table_full(case['table'])}\n```\n\n")
            report.append(f"**原始表格**:\n```\n{analyzer.format_original_table(case['original_table'])}\n```\n\n")
            report.append("---\n\n")

    # ===== 第二部分：参考项目分析 =====
    report.append("## 第二部分：参考项目分析（Table-Critic）\n\n")

    # WikiTQ统计
    report.append("### WikiTQ 错误统计\n\n")
    report.append(f"- **错误案例总数**: {len(reference_result['wikitq_cases'])}\n\n")
    report.append("#### 错误类型分布\n\n")
    for error_type, uids in sorted(reference_result['wikitq_errors'].items()):
        report.append(f"- **{error_type}**: {len(uids)} 个\n")
    report.append("\n")

    # TabFact统计
    report.append("### TabFact 错误统计\n\n")
    report.append(f"- **错误案例总数**: {len(reference_result['tabfact_cases'])}\n\n")
    report.append("#### 错误类型分布\n\n")
    for error_type, uids in sorted(reference_result['tabfact_errors'].items()):
        report.append(f"- **{error_type}**: {len(uids)} 个\n")
    report.append("\n")

    # 参考项目详细案例（简略）
    report.append("### WikiTQ 错误案例展示（每种类型1个）\n\n")

    ref_cases_by_type = defaultdict(list)
    for case in reference_result['wikitq_cases']:
        ref_cases_by_type[case['error_type']].append(case)

    for error_type in sorted(ref_cases_by_type.keys()):
        cases = ref_cases_by_type[error_type][:1]
        report.append(f"#### {error_type}\n\n")

        for case in cases:
            report.append(f"**案例**: `{case['uid']}`\n\n")
            report.append(f"**问题**: {case['question']}\n\n")
            report.append(f"**正确答案**: `{case['gold']}`\n\n")
            report.append(f"**预测答案**: `{case['pred']}`\n\n")
            report.append(f"**完整思维链**:\n```\n{analyzer.format_chain_full(case['chain'])}\n```\n\n")
            report.append("---\n\n")

    # ===== 第三部分：横向对比分析 =====
    report.append("## 第三部分：横向对比分析（当前项目特有错误）\n\n")

    # 计算当前项目特有错误
    current_wikitq_errors = set(case['uid'] for case in current_result['wikitq_cases'])
    reference_wikitq_errors = set(case['uid'] for case in reference_result['wikitq_cases'])
    current_only_errors = current_wikitq_errors - reference_wikitq_errors

    report.append(f"- **当前项目特有错误总数**: {len(current_only_errors)}\n")
    report.append(f"- **当前项目错误总数**: {len(current_wikitq_errors)}\n")
    report.append(f"- **参考项目错误总数**: {len(reference_wikitq_errors)}\n\n")

    # 按错误类型分类
    current_only_by_type = defaultdict(list)
    for case in current_result['wikitq_cases']:
        if case['uid'] in current_only_errors:
            current_only_by_type[case['error_type']].append(case['uid'])

    report.append("### 当前项目特有错误分类\n\n")
    for error_type, uids in sorted(current_only_by_type.items()):
        report.append(f"#### {error_type}\n\n")
        report.append(f"- **数量**: {len(uids)}\n")
        report.append(f"- **占比**: {len(uids)/len(current_only_errors)*100:.1f}%\n")
        report.append(f"- **ID列表**: {', '.join(uids[:10])}{'...' if len(uids) > 10 else ''}\n\n")

    # 详细案例展示
    report.append("### 当前项目特有错误案例详细分析\n\n")

    for error_type in sorted(current_only_by_type.keys()):
        cases_for_type = [case for case in current_result['wikitq_cases'] if case['uid'] in current_only_errors and case['error_type'] == error_type]
        cases = cases_for_type[:3]  # 每种类型最多3个

        if not cases:
            continue

        report.append(f"#### {error_type}\n\n")

        for i, case in enumerate(cases, 1):
            report.append(f"**案例 {i}**: `{case['uid']}`\n\n")
            report.append(f"**问题**: {case['question']}\n\n")
            report.append(f"**正确答案**: `{case['gold']}`\n\n")
            report.append(f"**预测答案**: `{case['pred']}`\n\n")
            report.append(f"**完整思维链**:\n```\n{analyzer.format_chain_full(case['chain'])}\n```\n\n")
            report.append(f"**完整表格**:\n```\n{analyzer.format_table_full(case['table'])}\n```\n\n")
            report.append(f"**原始表格**:\n```\n{analyzer.format_original_table(case['original_table'])}\n```\n\n")
            report.append("---\n\n")

    # 保存报告
    output_path = "semantic_bad_case_analysis.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(report))

    print(f"\n✅ 完成！报告已保存: {output_path}")
    print(f"报告大小: {len(''.join(report))} 字符")

    # 输出统计摘要
    print(f"\n{'='*60}")
    print("统计摘要")
    print(f"{'='*60}")
    print(f"\n当前项目（new_TC）:")
    print(f"  WikiTQ错误: {len(current_result['wikitq_cases'])}")
    print(f"  TabFact错误: {len(current_result['tabfact_cases'])}")

    print(f"\n参考项目:")
    print(f"  WikiTQ错误: {len(reference_result['wikitq_cases'])}")
    print(f"  TabFact错误: {len(reference_result['tabfact_cases'])}")

    print(f"\n横向对比:")
    print(f"  当前项目特有错误: {len(current_only_errors)}")
    print(f"  错误类型分布:")
    for error_type, uids in sorted(current_only_by_type.items()):
        print(f"    {error_type}: {len(uids)} 个")

    return output_path

if __name__ == "__main__":
    main()
