#!/usr/bin/env python3
"""
Bad Case 分析脚本（修复版）
分析两个项目的 gpt-5.4 结果，提取错误案例并生成对比分析报告
使用官方的准确率计算方法（wikitq_match_func）
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


################ 评估函数（从refine/TableQA/utils/evaluate.py复制） ################

def normalize(x):
    if not isinstance(x, str):
        x = x.decode('utf8', errors='ignore')
    # Remove diacritics
    x = ''.join(c for c in unicodedata.normalize('NFKD', x)
                if unicodedata.category(c) != 'Mn')
    # Normalize quotes and dashes
    x = re.sub(r"[‘’´`]", "'", x)
    x = re.sub(r"[“”]", "\"", x)
    x = re.sub(r"[‐‑‒–—−]", "-", x)
    while True:
        old_x = x
        # Remove citations
        x = re.sub(r"((?<!^)\[[^\]]*\]|\[\d+\]|[•♦†‡*#+])*$", "", x.strip())
        # Remove details in parenthesis
        x = re.sub(r"(?<!^)( \([^)]*\))*$", "", x.strip())
        # Remove outermost quotation mark
        x = re.sub(r'^"([^"]*)"$', r'\1', x.strip())
        if x == old_x:
            break
    # Remove final '.'
    if x and x[-1] == '.':
        x = x[:-1]
    # Collapse whitespaces and convert to lower case
    x = re.sub(r'\s+', ' ', x, flags=re.U).lower().strip()
    return x


class Value(object):
    __metaclass__ = ABCMeta
    _normalized = None

    @abstractmethod
    def match(self, other):
        pass

    @property
    def normalized(self):
        return self._normalized


class StringValue(Value):
    def __init__(self, content):
        assert isinstance(content, str)
        self._normalized = normalize(content)
        self._hash = hash(self._normalized)

    def __eq__(self, other):
        return isinstance(other, StringValue) and self.normalized == other.normalized

    def __hash__(self):
        return self._hash

    def match(self, other):
        assert isinstance(other, Value)
        return self.normalized == other.normalized


class NumberValue(Value):
    def __init__(self, amount, original_string=None):
        assert isinstance(amount, (int, float))
        if abs(amount - round(amount)) < 1e-6:
            self._amount = int(amount)
        else:
            self._amount = float(amount)
        if not original_string:
            self._normalized = str(self._amount)
        else:
            self._normalized = normalize(original_string)
        self._hash = hash(self._amount)

    @property
    def amount(self):
        return self._amount

    def __eq__(self, other):
        return isinstance(other, NumberValue) and self.amount == other.amount

    def __hash__(self):
        return self._hash

    def match(self, other):
        assert isinstance(other, Value)
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
                amount = float(text)
                assert not isnan(amount) and not isinf(amount)
                return amount
            except:
                return None


class DateValue(Value):
    def __init__(self, year, month, day, original_string=None):
        assert isinstance(year, int)
        assert isinstance(month, int) and (month == -1 or 1 <= month <= 12)
        assert isinstance(day, int) and (day == -1 or 1 <= day <= 31)
        assert not (year == month == day == -1)
        self._year = year
        self._month = month
        self._day = day
        if not original_string:
            self._normalized = '{}-{}-{}'.format(
                year if year != -1 else 'xx',
                month if month != -1 else 'xx',
                day if day != '-1' else 'xx')
        else:
            self._normalized = normalize(original_string)
        self._hash = hash((self._year, self._month, self._day))

    @property
    def ymd(self):
        return (self._year, self._month, self._day)

    def __eq__(self, other):
        return isinstance(other, DateValue) and self.ymd == other.ymd

    def __hash__(self):
        return self._hash

    def match(self, other):
        assert isinstance(other, Value)
        if self.normalized == other.normalized:
            return True
        if isinstance(other, DateValue):
            return self.ymd == other.ymd
        return False

    @staticmethod
    def parse(text):
        try:
            ymd = text.lower().split('-')
            assert len(ymd) == 3
            year = -1 if ymd[0] in ('xx', 'xxxx') else int(ymd[0])
            month = -1 if ymd[1] == 'xx' else int(ymd[1])
            day = -1 if ymd[2] == 'xx' else int(ymd[2])
            assert not (year == month == day == -1)
            assert month == -1 or 1 <= month <= 12
            assert day == -1 or 1 <= day <= 31
            return (year, month, day)
        except:
            return None


def to_value(original_string, corenlp_value=None):
    if isinstance(original_string, Value):
        return original_string
    if not corenlp_value:
        corenlp_value = original_string
    # Number?
    amount = NumberValue.parse(corenlp_value)
    if amount is not None:
        return NumberValue(amount, original_string)
    # Date?
    ymd = DateValue.parse(corenlp_value)
    if ymd is not None:
        if ymd[1] == ymd[2] == -1:
            return NumberValue(ymd[0], original_string)
        else:
            return DateValue(ymd[0], ymd[1], ymd[2], original_string)
    # String.
    return StringValue(original_string)


def to_value_list(original_strings, corenlp_values=None):
    assert isinstance(original_strings, (list, tuple, set))
    if corenlp_values is not None:
        assert isinstance(corenlp_values, (list, tuple, set))
        assert len(original_strings) == len(corenlp_values)
        return list(set(to_value(x, y) for (x, y)
                        in zip(original_strings, corenlp_values)))
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
    results = sample["chain"][-1]["parameter_and_conf"]

    if strategy == "top":
        res = results[0][0]
    elif strategy == "weighted":
        res_conf_dict = {}
        for res, conf in results:
            if res not in res_conf_dict:
                res_conf_dict[res] = 0
            res_conf_dict[res] += conf
        res_conf_rank = sorted(res_conf_dict.items(), key=lambda x: x[1], reverse=True)
        res = res_conf_rank[0][0]
    else:
        raise NotImplementedError

    pred_answer = [res.lower()] if '|' not in res else [r for r in res.lower().split('|')]
    pred_answer = to_value_list(pred_answer)

    if check_denotation(target_values, pred_answer):
        return True
    else:
        return False


################ Bad Case 分析器 ################

class BadCaseAnalyzer:
    """Bad Case 分析器"""

    def __init__(self, current_project_path: str, reference_project_path: str):
        self.current_project_path = Path(current_project_path)
        self.reference_project_path = Path(reference_project_path)
        self.current_data = None
        self.reference_data = None

    def load_pkl(self, pkl_path: str) -> List[Dict]:
        """加载 pkl 文件"""
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
        return data

    def load_data(self):
        """加载两个项目的数据"""
        # 当前项目数据
        current_pkl = self.current_project_path / "final_result.pkl"
        self.current_data = self.load_pkl(str(current_pkl))

        # 参考项目数据
        reference_pkl = self.reference_project_path / "final_result.pkl"
        self.reference_data = self.load_pkl(str(reference_pkl))

        print(f"✓ 当前项目加载完成：{len(self.current_data)} 条记录")
        print(f"✓ 参考项目加载完成：{len(self.reference_data)} 条记录")

    def load_target_values_map(self, tagged_data_path: str = 'thought/TableQA/data/wikitq/tagged_data') -> Dict[str, Any]:
        """加载目标值映射"""
        target_values_map = {}

        if not os.path.exists(tagged_data_path):
            print(f"⚠️  警告: tagged_data 路径不存在: {tagged_data_path}")
            return target_values_map

        file_count = 0
        for basename in os.listdir(tagged_data_path):
            if basename[0] == '.':
                continue
            filepath = os.path.join(tagged_data_path, basename)
            file_count += 1
            with open(filepath, 'r', encoding='utf8') as fin:
                header = fin.readline().rstrip('\n').split('\t')
                for line in fin:
                    stuff = dict(zip(header, line.rstrip('\n').split('\t')))
                    ex_id = stuff['id']
                    original_strings = tsv_unescape_list(stuff['targetValue'])
                    canon_strings = tsv_unescape_list(stuff['targetCanon'])

                    target_values_map[ex_id] = to_value_list(
                        original_strings, canon_strings)

        print(f"✓ 从 {file_count} 个文件加载了 {len(target_values_map)} 个目标值")
        return target_values_map

    def analyze_bad_cases(self, data: List[Dict], target_values_map: Dict[str, Any] = None) -> Tuple[List[Dict], Dict]:
        """分析 bad cases"""
        bad_cases = []
        error_types = defaultdict(int)
        error_length_distribution = []

        # 如果没有提供target_values_map，尝试加载
        if target_values_map is None:
            target_values_map = self.load_target_values_map()

        for item in data:
            # 跳过 None 值
            if item is None:
                continue

            # 使用官方的wikitq_match_func来判断是否正确
            sample_id = item.get('ids', item.get('id', ''))

            # 如果没有目标值，跳过
            if sample_id not in target_values_map:
                continue

            # 判断是否正确
            is_correct = wikitq_match_func(item, target_values_map[sample_id], strategy="top")

            if not is_correct:
                # 提取答案
                answer_list = item.get('answer', [])
                if isinstance(answer_list, list) and len(answer_list) > 0:
                    gold_answer = answer_list[0] if answer_list else ''
                else:
                    gold_answer = str(answer_list) if answer_list else ''

                # 提取预测（从 chain 中获取最后一个操作的 parameter_and_conf）
                chain = item.get('chain', [])
                pred_answer = ''
                if isinstance(chain, list) and len(chain) > 0:
                    # 获取最后一个操作
                    last_op = chain[-1]
                    if isinstance(last_op, dict):
                        # 从 parameter_and_conf 提取预测值
                        param_conf = last_op.get('parameter_and_conf', [])
                        if param_conf and len(param_conf) > 0:
                            pred_answer = param_conf[0][0] if param_conf[0] else ''

                bad_case = {
                    'uid': sample_id,
                    'question': item.get('statement', ''),
                    'gold': gold_answer,
                    'pred': str(pred_answer),
                    'chain_length': len(chain) if isinstance(chain, list) else 0,
                }

                # 分析错误类型
                error_type = self.classify_error(bad_case)
                bad_case['error_type'] = error_type
                error_types[error_type] += 1

                # 记录问题长度
                if bad_case['question']:
                    error_length_distribution.append(len(bad_case['question']))

                bad_cases.append(bad_case)

        return bad_cases, dict(error_types)

    def classify_error(self, bad_case: Dict) -> str:
        """分类错误类型"""
        gold = str(bad_case['gold']).strip().lower()
        pred = str(bad_case['pred']).strip().lower()

        # 数值错误
        if gold.isdigit() and pred.isdigit():
            return '数值错误'

        # 布尔值错误
        if gold in ['true', 'false', 'yes', 'no'] and pred in ['true', 'false', 'yes', 'no']:
            return '布尔判断错误'

        # 空值错误
        if not gold and pred:
            return '误判为有值'
        if gold and not pred:
            return '误判为空值'

        # 字符串相似度
        if gold and pred and gold in pred or pred in gold:
            return '部分匹配错误'

        # 完全不匹配
        if gold and pred:
            return '完全不匹配'

        return '其他错误'

    def generate_error_summary(self, bad_cases: List[Dict], error_types: Dict) -> str:
        """生成错误摘要"""
        total = len(bad_cases)
        summary = [
            f"## 错误案例统计\n",
            f"- **总错误数**: {total}\n",
            f"- **错误类型分布**:\n"
        ]

        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            summary.append(f"  - {error_type}: {count} ({percentage:.1f}%)\n")

        return ''.join(summary)

    def generate_case_examples(self, bad_cases: List[Dict], limit: int = 10) -> str:
        """生成错误案例示例"""
        examples = ["## 错误案例示例\n\n"]
        examples.append(f"展示前 {min(limit, len(bad_cases))} 个错误案例：\n\n")

        for i, case in enumerate(bad_cases[:limit], 1):
            examples.append(f"### 案例 {i}\n\n")
            examples.append(f"**UID**: `{case['uid']}`\n\n")
            examples.append(f"**问题**: {case['question']}\n\n")
            examples.append(f"**正确答案**: `{case['gold']}`\n\n")
            examples.append(f"**预测答案**: `{case['pred']}`\n\n")
            examples.append(f"**错误类型**: {case['error_type']}\n\n")
            examples.append(f"**Chain长度**: {case['chain_length']}\n\n")
            examples.append("---\n\n")

        return ''.join(examples)

    def compare_bad_cases(self, current_bad_cases: List[Dict],
                         reference_bad_cases: List[Dict]) -> str:
        """对比两个项目的 bad cases"""
        # 创建 UID 到 bad case 的映射
        current_uids = {case['uid'] for case in current_bad_cases}
        reference_uids = {case['uid'] for case in reference_bad_cases}

        # 找出共同错误和独有错误
        common_errors = current_uids & reference_uids
        current_only = current_uids - reference_uids
        reference_only = reference_uids - current_uids

        comparison = [
            "## Bad Case 对比分析\n\n",
            f"### 错误数量对比\n\n",
            f"- **当前项目错误数**: {len(current_bad_cases)}\n",
            f"- **参考项目错误数**: {len(reference_bad_cases)}\n",
            f"- **共同错误案例**: {len(common_errors)}\n",
            f"- **当前项目独有错误**: {len(current_only)}\n",
            f"- **参考项目独有错误**: {len(reference_only)}\n\n",
        ]

        # 分析改进情况
        if len(current_only) < len(reference_only):
            improvement = len(reference_only) - len(current_only)
            comparison.append(f"✅ **当前项目相比参考项目减少了 {improvement} 个错误案例**\n\n")
        elif len(current_only) > len(reference_only):
            regression = len(current_only) - len(reference_only)
            comparison.append(f"⚠️ **当前项目相比参考项目增加了 {regression} 个错误案例**\n\n")
        else:
            comparison.append("➖ **两个项目的错误数量相同**\n\n")

        # 共同错误示例
        if common_errors:
            comparison.append("### 共同错误案例示例\n\n")
            common_cases = [case for case in current_bad_cases if case['uid'] in common_errors]
            for i, case in enumerate(common_cases[:5], 1):
                comparison.append(f"#### 共同错误 {i}\n\n")
                comparison.append(f"**UID**: `{case['uid']}`\n\n")
                comparison.append(f"**问题**: {case['question']}\n\n")
                comparison.append(f"**正确答案**: `{case['gold']}`\n\n")
                comparison.append(f"**预测答案**: `{case['pred']}`\n\n")
                comparison.append(f"**错误类型**: {case['error_type']}\n\n")
                comparison.append("---\n\n")

        # 当前项目独有错误示例
        if current_only:
            comparison.append("### 当前项目独有错误案例（需要修复）\n\n")
            current_only_cases = [case for case in current_bad_cases if case['uid'] in current_only]
            for i, case in enumerate(current_only_cases[:5], 1):
                comparison.append(f"#### 独有错误 {i}\n\n")
                comparison.append(f"**UID**: `{case['uid']}`\n\n")
                comparison.append(f"**问题**: {case['question']}\n\n")
                comparison.append(f"**正确答案**: `{case['gold']}`\n\n")
                comparison.append(f"**预测答案**: `{case['pred']}`\n\n")
                comparison.append(f"**错误类型**: {case['error_type']}\n\n")
                comparison.append("---\n\n")

        # 参考项目独有错误示例（已修复）
        if reference_only:
            comparison.append("### 参考项目独有错误案例（当前项目已修复）\n\n")
            reference_only_cases = [case for case in reference_bad_cases if case['uid'] in reference_only]
            for i, case in enumerate(reference_only_cases[:5], 1):
                comparison.append(f"#### 已修复错误 {i}\n\n")
                comparison.append(f"**UID**: `{case['uid']}`\n\n")
                comparison.append(f"**问题**: {case['question']}\n\n")
                comparison.append(f"**正确答案**: `{case['gold']}`\n\n")
                comparison.append(f"**参考项目预测**: `{case['pred']}`\n\n")
                comparison.append(f"**错误类型**: {case['error_type']}\\n\n")
                comparison.append("---\n\n")

        return ''.join(comparison)

    def generate_full_report(self) -> str:
        """生成完整分析报告"""
        print("开始生成分析报告...")

        # 加载数据
        self.load_data()

        # 加载目标值映射
        print("\n加载目标值映射...")
        target_values_map = self.load_target_values_map()

        # 分析 bad cases
        print("\n分析当前项目 bad cases...")
        current_bad_cases, current_error_types = self.analyze_bad_cases(self.current_data, target_values_map)
        print(f"发现 {len(current_bad_cases)} 个错误案例")

        print("\n分析参考项目 bad cases...")
        reference_bad_cases, reference_error_types = self.analyze_bad_cases(self.reference_data, target_values_map)
        print(f"发现 {len(reference_bad_cases)} 个错误案例")

        # 生成报告
        report = [
            "# Bad Case 对比分析报告\n\n",
            f"**生成时间**: {self._get_timestamp()}\n\n",
            "---\n\n",
            "# 项目信息\n\n",
            f"## 当前项目\n\n",
            f"- **路径**: `{self.current_project_path}`\n",
            f"- **准确率**: {self._get_accuracy(self.current_project_path)}\n",
            f"- **错误案例数**: {len(current_bad_cases)}\n\n",
            f"## 参考项目\n\n",
            f"- **路径**: `{self.reference_project_path}`\n",
            f"- **准确率**: {self._get_accuracy(self.reference_project_path)}\n",
            f"- **错误案例数**: {len(reference_bad_cases)}\n\n",
            "---\n\n",
            "# 当前项目 Bad Case 分析\n\n",
            self.generate_error_summary(current_bad_cases, current_error_types),
            "\n",
            self.generate_case_examples(current_bad_cases, limit=10),
            "\n",
            "---\n\n",
            "# 参考项目 Bad Case 分析\n\n",
            self.generate_error_summary(reference_bad_cases, reference_error_types),
            "\n",
            self.generate_case_examples(reference_bad_cases, limit=10),
            "\n",
            "---\n\n",
            self.compare_bad_cases(current_bad_cases, reference_bad_cases),
            "\n",
            "---\n\n",
            "# 结论与建议\n\n",
            self._generate_conclusions(current_bad_cases, reference_bad_cases,
                                     current_error_types, reference_error_types),
        ]

        return ''.join(report)

    def _get_accuracy(self, project_path: Path) -> str:
        """获取准确率"""
        acc_file = project_path / "acc.txt"
        if acc_file.exists():
            with open(acc_file, 'r') as f:
                return f.read().strip()
        return "未知"

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _generate_conclusions(self, current_bad_cases: List[Dict],
                             reference_bad_cases: List[Dict],
                             current_error_types: Dict,
                             reference_error_types: Dict) -> str:
        """生成结论与建议"""
        conclusions = ["## 主要发现\n\n"]

        # 错误数量对比
        current_errors = len(current_bad_cases)
        reference_errors = len(reference_bad_cases)

        if current_errors < reference_errors:
            improvement = reference_errors - current_errors
            conclusions.append(f"1. **性能提升**: 当前项目相比参考项目减少了 {improvement} 个错误案例（{improvement/reference_errors*100:.1f}%）\n\n")
        elif current_errors > reference_errors:
            regression = current_errors - reference_errors
            conclusions.append(f"1. **性能下降**: 当前项目相比参考项目增加了 {regression} 个错误案例（{regression/reference_errors*100:.1f}%）\n\n")
        else:
            conclusions.append(f"1. **性能持平**: 两个项目的错误数量相同\n\n")

        # 错误类型分析
        conclusions.append("## 错误类型对比\n\n")
        all_error_types = set(current_error_types.keys()) | set(reference_error_types.keys())

        for error_type in sorted(all_error_types):
            current_count = current_error_types.get(error_type, 0)
            reference_count = reference_error_types.get(error_type, 0)

            if current_count > reference_count:
                diff = current_count - reference_count
                conclusions.append(f"- ⚠️ **{error_type}**: 当前项目更多（{current_count} vs {reference_count}, +{diff}）\n")
            elif current_count < reference_count:
                diff = reference_count - current_count
                conclusions.append(f"- ✅ **{error_type}**: 参考项目更多（{current_count} vs {reference_count}, -{diff}）\n")
            else:
                conclusions.append(f"- ➖ **{error_type}**: 相同（{current_count}）\n")

        conclusions.append("\n\n## 改进建议\n\n")

        # 找出当前项目的主要错误类型
        if current_error_types:
            top_errors = sorted(current_error_types.items(), key=lambda x: x[1], reverse=True)[:3]
            conclusions.append("### 优先修复的错误类型\n\n")
            for error_type, count in top_errors:
                percentage = (count / current_errors * 100) if current_errors > 0 else 0
                conclusions.append(f"- **{error_type}**: {count} 个案例 ({percentage:.1f}%)\n")

        conclusions.append("\n\n### 具体建议\n\n")
        conclusions.append("1. **针对共同错误**: 这些是两个项目都存在的问题，可能是数据质量或任务固有的难度\n")
        conclusions.append("2. **针对独有错误**: 当前项目的独有错误是优先修复的重点\n")
        conclusions.append("3. **错误类型分析**: 关注占比最高的错误类型，优化相关的推理逻辑\n")

        return ''.join(conclusions)


def main():
    """主函数"""
    # 配置路径
    current_project = "results/refine/wikitq/sota/gpt-5.4"
    reference_project = "/home/ubuntu/mnt/lx/Table-Critic/results/refine/wikitq/gpt-5.4"

    print("=" * 60)
    print("Bad Case 对比分析")
    print("=" * 60)
    print(f"\n当前项目: {current_project}")
    print(f"参考项目: {reference_project}\n")

    # 创建分析器
    analyzer = BadCaseAnalyzer(current_project, reference_project)

    # 生成报告
    try:
        report = analyzer.generate_full_report()

        # 保存报告
        output_path = "bad-case-analysis.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✅ 分析完成！报告已保存到: {output_path}")
        print(f"报告大小: {len(report)} 字符")

        return report

    except Exception as e:
        print(f"\n❌ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
