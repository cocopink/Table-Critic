#!/usr/bin/env python3
"""
Bad Case 分析脚本
分析两个项目的 gpt-5.4 结果，提取错误案例并生成对比分析报告
"""

import pickle
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
import sys
import os

# 导入官方的准确率计算函数
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'refine', 'TableQA', 'utils'))
from evaluate import wikitq_match_func, wikitq_match_func_for_samples


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
        from evaluate import to_value_list, tsv_unescape_list

        target_values_map = {}

        if not os.path.exists(tagged_data_path):
            print(f"⚠️  警告: tagged_data 路径不存在: {tagged_data_path}")
            return target_values_map

        for basename in os.listdir(tagged_data_path):
            if basename[0] == '.':
                continue
            filepath = os.path.join(tagged_data_path, basename)
            with open(filepath, 'r', 'utf8') as fin:
                header = fin.readline().rstrip('\n').split('\t')
                for line in fin:
                    stuff = dict(zip(header, line.rstrip('\n').split('\t')))
                    ex_id = stuff['id']
                    original_strings = tsv_unescape_list(stuff['targetValue'])
                    canon_strings = tsv_unescape_list(stuff['targetCanon'])

                    target_values_map[ex_id] = to_value_list(
                        original_strings, canon_strings)

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
        print(f"✓ 加载了 {len(target_values_map)} 个目标值")

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
