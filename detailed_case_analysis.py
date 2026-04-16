#!/usr/bin/env python3
"""
超级详细的Bad Case分析脚本
功能：
1. 分析WikiTQ和TabFact两个数据集
2. 提取完整错误案例信息（表格、思维链、纠错历史）
3. 每个错误类型提供1-2个详细案例分析
4. 生成错误案例ID分类表格
"""

import pickle
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict, Counter
import sys
import os
import re
import unicodedata
from math import isnan, isinf
from abc import ABCMeta, abstractmethod


################ 评估函数（简化版，用于判断是否正确）################

def normalize(x):
    if not isinstance(x, str):
        x = str(x)
    x = ''.join(c for c in unicodedata.normalize('NFKD', x)
                if unicodedata.category(c) != 'Mn')
    x = re.sub(r"[‘’´`]", "'", x)
    x = re.sub(r"[“”]", "\"", x)
    x = re.sub(r"[‐‑‒–—−]", "-", x)
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


################ 错误分类器 ################

class DetailedErrorClassifier:
    """详细错误分类器"""

    def __init__(self):
        self.keywords_calculation = ['sum', 'total', 'average', 'mean', 'add', 'subtract',
                                     'multiply', 'divide', 'calculate', 'count', 'how many',
                                     'how much', 'number of', 'maximum', 'minimum', 'max', 'min']
        self.keywords_comparison = ['larger', 'smaller', 'greater', 'less', 'more', 'most',
                                    'least', 'best', 'worst', 'higher', 'lower', 'top', 'bottom']
        self.keywords_entity = ['who', 'which', 'what', 'name', 'person', 'team', 'country',
                                'city', 'place', 'building', 'yacht', 'driver']
        self.keywords_temporal = ['when', 'date', 'time', 'year', 'month', 'day', 'before',
                                  'after', 'first', 'last', 'earliest', 'latest']

    def classify_error(self, bad_case: Dict) -> str:
        """
        详细错误分类

        分类体系：
        1. 数值错误
           - 数值计算错误
           - 数值比较错误
           - 数值统计错误
        2. 理解错误
           - 实体识别错误
           - 条件理解错误
        3. 答案格式错误
           - 多答案处理错误
        4. 布尔判断错误
        5. 其他错误
        """
        question = str(bad_case['question']).lower()
        gold = str(bad_case['gold']).strip().lower()
        pred = str(bad_case['pred']).strip().lower()

        # 检查是否是数值类型
        gold_is_number = self._is_number(gold)
        pred_is_number = self._is_number(pred)

        # 检查是否是布尔类型
        gold_is_boolean = gold in ['yes', 'no', 'true', 'false']
        pred_is_boolean = pred in ['yes', 'no', 'true', 'false']

        # 1. 数值错误分类
        if gold_is_number and pred_is_number:
            return self._classify_numerical_error(question, gold, pred)

        # 2. 布尔判断错误
        if gold_is_boolean and pred_is_boolean:
            return '布尔判断错误'

        # 3. 实体识别错误
        if any(kw in question for kw in self.keywords_entity):
            if self._is_entity_name(gold) and self._is_entity_name(pred):
                return '实体识别错误'

        # 4. 答案数量错误
        if '|' in pred and '|' not in gold:
            return '多答案处理错误'

        # 5. 条件理解错误
        if any(kw in question for kw in ['next', 'previous', 'following', 'after', 'before']):
            return '条件理解错误'

        # 6. 字符串相似度分析
        if gold and pred:
            if gold in pred or pred in gold:
                return '部分匹配错误'

        # 7. 完全不匹配
        return '完全不匹配'

    def _is_number(self, text: str) -> bool:
        """检查是否是数字"""
        text = text.strip()
        try:
            float(text)
            return True
        except:
            return False

    def _is_entity_name(self, text: str) -> bool:
        """检查是否是实体名称"""
        text = text.strip().lower()
        if text in ['yes', 'no', 'true', 'false']:
            return False
        if self._is_number(text):
            return False
        return any(c.isalpha() for c in text)

    def _string_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度"""
        if not str1 or not str2:
            return 0.0
        if str1 in str2 or str2 in str1:
            return 0.8
        return 0.0

    def _classify_numerical_error(self, question: str, gold: str, pred: str) -> str:
        """分类数值错误"""
        try:
            gold_num = float(gold)
            pred_num = float(pred)
        except:
            return '数值错误'

        if any(kw in question for kw in ['sum', 'total', 'add']):
            return '数值计算错误（求和）'
        if any(kw in question for kw in ['count', 'how many', 'how much', 'number of']):
            return '数值统计错误（计数）'
        if any(kw in question for kw in ['maximum', 'max', 'most', 'largest']):
            return '数值比较错误（最大值）'
        if any(kw in question for kw in ['minimum', 'min', 'least', 'smallest']):
            return '数值比较错误（最小值）'
        return '数值计算错误（其他）'


################ 详细案例分析器 ################

class DetailedCaseAnalyzer:
    """详细案例分析器"""

    def extract_case_details(self, sample: Dict) -> Dict[str, Any]:
        """提取案例的完整详细信息"""
        details = {
            'uid': sample.get('id', sample.get('ids', 'unknown')),
            'question': sample.get('statement', ''),
            'table': self._format_table(sample.get('table', [])),
            'answer': sample.get('answer', []),
            'chain': self._format_chain(sample.get('chain', [])),
            'refine_history': self._extract_refine_history(sample),
            'clarifier': self._format_clarifier(sample.get('clarifier', {})),
            'predicted_answer': self._extract_predicted_answer(sample),
            'judge_result': sample.get('judge', ''),
        }
        return details

    def _format_table(self, table: List) -> str:
        """格式化表格"""
        if not table:
            return "无表格数据"

        if isinstance(table, list) and len(table) > 0:
            # 检查表格格式
            if isinstance(table[0], list):
                # 表格是二维列表
                lines = []
                for i, row in enumerate(table[:10]):  # 只显示前10行
                    if isinstance(row, list):
                        lines.append(" | ".join(str(cell) for cell in row))
                    else:
                        lines.append(str(row))
                return "\n".join(lines) + ("..." if len(table) > 10 else "")
            else:
                return str(table[:5])  # 只显示前5个元素
        return str(table)

    def _format_chain(self, chain: List) -> str:
        """格式化思维链"""
        if not chain:
            return "无思维链"

        steps = []
        for i, step in enumerate(chain):
            if isinstance(step, dict):
                op_name = step.get('operation_name', 'unknown')
                params = step.get('parameter_and_conf', [])
                thought = step.get('thought', '')

                step_desc = f"步骤 {i+1}: {op_name}"
                if thought:
                    step_desc += f"\n  思考: {thought}"
                if params:
                    step_desc += f"\n  参数: {str(params)[:100]}"  # 限制长度
                steps.append(step_desc)

        return "\n\n".join(steps) if steps else "无有效思维链"

    def _extract_refine_history(self, sample: Dict) -> str:
        """提取纠错历史"""
        if 'refine_history' not in sample:
            return "无纠错历史"

        history = sample['refine_history']
        if not history:
            return "无纠错记录"

        events = []
        for i, event in enumerate(history):
            iteration = event.get('iteration', i)
            action = event.get('action', 'unknown')
            conclusion = event.get('conclusion', '')

            event_desc = f"轮次 {iteration}: {action}"
            if conclusion:
                event_desc += f" → {conclusion}"
            events.append(event_desc)

        return "\n".join(events) if events else "无有效纠错记录"

    def _format_clarifier(self, clarifier: Dict) -> str:
        """格式化Clarifier结果"""
        if not clarifier:
            return "无Clarifier结果"

        schema = clarifier.get('schema', {})
        if not schema:
            return "Clarifier结果为空"

        # 格式化schema信息
        items = []
        for key, value in schema.items():
            if isinstance(value, list):
                items.append(f"{key}: {', '.join(str(v) for v in value[:5])}")
            else:
                items.append(f"{key}: {value}")

        return "\n".join(items) if items else "无有效Schema"

    def _extract_predicted_answer(self, sample: Dict) -> str:
        """提取预测答案"""
        chain = sample.get('chain', [])
        if not chain:
            return ""

        last_op = chain[-1]
        if isinstance(last_op, dict):
            param_conf = last_op.get('parameter_and_conf', [])
            if param_conf and len(param_conf) > 0:
                return str(param_conf[0][0]) if param_conf[0] else ""
        return ""


################ 主分析器 ################

class ComprehensiveAnalyzer:
    """综合分析器"""

    def __init__(self):
        self.classifier = DetailedErrorClassifier()
        self.case_analyzer = DetailedCaseAnalyzer()

    def analyze_dataset(self, data_path: str, dataset_name: str) -> Tuple[List[Dict], Dict]:
        """分析单个数据集"""
        print(f"\n分析 {dataset_name} 数据集...")

        # 加载数据
        with open(data_path, 'rb') as f:
            data = pickle.load(f)

        print(f"  加载了 {len(data)} 条记录")

        # 分析错误案例
        bad_cases = []
        error_types = defaultdict(list)  # error_type -> list of uids

        for item in data:
            if item is None:
                continue

            # 判断是否正确（简化版）
            is_correct = self._is_correct(item)

            if not is_correct:
                # 提取基本信息
                answer_list = item.get('answer', [])
                gold_answer = answer_list[0] if answer_list else ''

                chain = item.get('chain', [])
                pred_answer = ''
                if chain and len(chain) > 0:
                    last_op = chain[-1]
                    if isinstance(last_op, dict):
                        param_conf = last_op.get('parameter_and_conf', [])
                        if param_conf and len(param_conf) > 0:
                            pred_answer = param_conf[0][0] if param_conf[0] else ''

                bad_case = {
                    'uid': item.get('id', item.get('ids', 'unknown')),
                    'question': item.get('statement', ''),
                    'gold': str(gold_answer),
                    'pred': str(pred_answer),
                    'sample': item,  # 保存完整样本
                }

                # 分类错误
                error_type = self.classifier.classify_error(bad_case)
                bad_case['error_type'] = error_type
                bad_case['dataset'] = dataset_name

                bad_cases.append(bad_case)
                error_types[error_type].append(bad_case['uid'])

        print(f"  发现 {len(bad_cases)} 个错误案例")
        return bad_cases, dict(error_types)

    def _is_correct(self, item: Dict) -> bool:
        """判断样本是否正确"""
        # 对于TabFact，使用judge字段
        if 'table_caption' in item:  # TabFact特有字段
            judge = str(item.get('judge', ''))
            return '[Correct]' in judge

        # 对于WikiTQ，使用parameter_and_conf判断（与官方一致）
        chain = item.get('chain', [])
        if chain and len(chain) > 0:
            last_op = chain[-1]
            if isinstance(last_op, dict):
                param_conf = last_op.get('parameter_and_conf', [])
                if param_conf and len(param_conf) > 0:
                    pred_answer = str(param_conf[0][0]).strip().lower() if param_conf[0] else ''

                    # 获取正确答案
                    answer_list = item.get('answer', [])
                    if answer_list and len(answer_list) > 0:
                        gold_answer = str(answer_list[0]).strip().lower()

                        # 简化判断：标准化后比较
                        gold_normalized = normalize(gold_answer)
                        pred_normalized = normalize(pred_answer)

                        return gold_normalized == pred_normalized

        # 默认认为不正确
        return False

    def generate_error_id_table(self, all_error_types: Dict[str, List[str]]) -> str:
        """生成错误案例ID分类表格"""
        table = ["## 错误案例ID分类表\n\n"]
        table.append("| 错误类型 | 错误案例ID | 数量 |\n")
        table.append("|---------|-----------|------|\n")

        for error_type, uids in sorted(all_error_types.items()):
            uid_str = ", ".join(uids)
            table.append(f"| {error_type} | {uid_str} | {len(uids)} |\n")

        return ''.join(table)

    def generate_detailed_case_analysis(self, bad_cases: List[Dict], num_cases_per_type: int = 2) -> str:
        """生成详细案例分析"""
        report = ["## 详细错误案例分析\n\n"]

        # 按错误类型分组
        cases_by_type = defaultdict(list)
        for case in bad_cases:
            cases_by_type[case['error_type']].append(case)

        # 为每种错误类型选择案例
        for error_type in sorted(cases_by_type.keys()):
            cases = cases_by_type[error_type][:num_cases_per_type]

            report.append(f"### {error_type}\n\n")
            report.append(f"**案例数量**: {len(cases_by_type[error_type])}\n\n")

            for i, case in enumerate(cases, 1):
                report.append(f"#### 案例 {i}\n\n")

                # 提取详细信息
                details = self.case_analyzer.extract_case_details(case['sample'])

                report.append(f"**UID**: `{details['uid']}`\n\n")
                report.append(f"**问题**: {details['question']}\n\n")
                report.append(f"**正确答案**: `{case['gold']}`\n\n")
                report.append(f"**预测答案**: `{case['pred']}`\n\n")
                report.append(f"**错误类型**: {error_type}\n\n")

                # 表格数据
                report.append(f"**表格数据**:\n```\n{details['table']}\n```\n\n")

                # 思维链
                report.append(f"**思维链**:\n```\n{details['chain']}\n```\n\n")

                # 纠错历史
                if details['refine_history'] != "无纠错历史":
                    report.append(f"**纠错历史**:\n```\n{details['refine_history']}\n```\n\n")

                # Clarifier结果
                if details['clarifier'] != "无Clarifier结果":
                    report.append(f"**Clarifier结果**:\n```\n{details['clarifier']}\n```\n\n")

                report.append("---\n\n")

        return ''.join(report)

    def generate_summary_statistics(self, wikitq_bad_cases: List[Dict],
                                    tabfact_bad_cases: List[Dict]) -> str:
        """生成汇总统计"""
        report = ["# 汇总统计\n\n"]

        report.append("## WikiTQ 数据集\n\n")
        wikitq_types = Counter([case['error_type'] for case in wikitq_bad_cases])
        report.append(f"- **总错误数**: {len(wikitq_bad_cases)}\n")
        report.append(f"- **错误类型数**: {len(wikitq_types)}\n\n")
        report.append("### 错误类型分布\n\n")
        for error_type, count in wikitq_types.most_common():
            pct = (count / len(wikitq_bad_cases) * 100) if wikitq_bad_cases else 0
            report.append(f"- {error_type}: {count} ({pct:.1f}%)\n")

        report.append("\n## TabFact 数据集\n\n")
        tabfact_types = Counter([case['error_type'] for case in tabfact_bad_cases])
        report.append(f"- **总错误数**: {len(tabfact_bad_cases)}\n")
        report.append(f"- **错误类型数**: {len(tabfact_types)}\n\n")
        report.append("### 错误类型分布\n\n")
        for error_type, count in tabfact_types.most_common():
            pct = (count / len(tabfact_bad_cases) * 100) if tabfact_bad_cases else 0
            report.append(f"- {error_type}: {count} ({pct:.1f}%)\n")

        return ''.join(report)


def main():
    """主函数"""
    print("=" * 60)
    print("超级详细的Bad Case分析")
    print("=" * 60)

    analyzer = ComprehensiveAnalyzer()

    # 分析WikiTQ
    wikitq_path = "results/refine/wikitq/sota/gpt-5.4/final_result.pkl"
    if os.path.exists(wikitq_path):
        wikitq_bad_cases, wikitq_error_types = analyzer.analyze_dataset(wikitq_path, "WikiTQ")
    else:
        print(f"警告: WikiTQ结果文件不存在: {wikitq_path}")
        wikitq_bad_cases, wikitq_error_types = [], {}

    # 分析TabFact
    tabfact_path = "results/refine/tabfact/sota/gpt-5.4/final_result.pkl"
    if os.path.exists(tabfact_path):
        tabfact_bad_cases, tabfact_error_types = analyzer.analyze_dataset(tabfact_path, "TabFact")
    else:
        print(f"警告: TabFact结果文件不存在: {tabfact_path}")
        tabfact_bad_cases, tabfact_error_types = [], {}

    # 合并错误类型
    all_error_types = defaultdict(list)
    for error_type, uids in wikitq_error_types.items():
        all_error_types[f"WikiTQ-{error_type}"].extend(uids)
    for error_type, uids in tabfact_error_types.items():
        all_error_types[f"TabFact-{error_type}"].extend(uids)

    # 生成报告
    print("\n生成报告...")
    report = ["# 超级详细的Bad Case分析报告\n\n"]
    report.append("**生成时间**: 2026-04-16\n\n")
    report.append("---\n\n")

    # 汇总统计
    report.append(analyzer.generate_summary_statistics(wikitq_bad_cases, tabfact_bad_cases))

    # 错误案例ID分类表
    report.append("\n---\n\n")
    report.append(analyzer.generate_error_id_table(all_error_types))

    # 详细案例分析（WikiTQ）
    if wikitq_bad_cases:
        report.append("\n---\n\n")
        report.append("## WikiTQ 详细案例分析\n\n")
        report.append(analyzer.generate_detailed_case_analysis(wikitq_bad_cases, num_cases_per_type=2))

    # 详细案例分析（TabFact）
    if tabfact_bad_cases:
        report.append("\n---\n\n")
        report.append("## TabFact 详细案例分析\n\n")
        report.append(analyzer.generate_detailed_case_analysis(tabfact_bad_cases, num_cases_per_type=2))

    # 保存报告
    output_path = "detailed_bad_case_analysis.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(report))

    print(f"\n✅ 分析完成！报告已保存到: {output_path}")
    print(f"报告大小: {len(''.join(report))} 字符")

    return ''.join(report)


if __name__ == "__main__":
    main()
