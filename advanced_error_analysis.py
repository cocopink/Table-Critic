#!/usr/bin/env python3
"""
高级错误分类分析脚本
对bad case进行更细致的分类，包括：
- 数值错误（计算、比较、统计、单位）
- 理解错误（实体识别、关系理解、条件理解）
- 推理错误（逻辑推理、排序、筛选）
- 答案格式错误（多答案、格式不匹配）
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


################ 评估函数 ################

def normalize(x):
    if not isinstance(x, str):
        x = x.decode('utf8', errors='ignore')
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
    amount = NumberValue.parse(corenlp_value)
    if amount is not None:
        return NumberValue(amount, original_string)
    ymd = DateValue.parse(corenlp_value)
    if ymd is not None:
        if ymd[1] == ymd[2] == -1:
            return NumberValue(ymd[0], original_string)
        else:
            return DateValue(ymd[0], ymd[1], ymd[2], original_string)
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


################ 高级错误分类器 ################

class AdvancedErrorClassifier:
    """高级错误分类器"""

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
        self.keywords_boolean = ['did', 'do', 'is', 'are', 'was', 'were', 'has', 'have',
                                 'will', 'would', 'could', 'should']

    def classify_error(self, bad_case: Dict) -> str:
        """
        高级错误分类

        分类体系：
        1. 数值错误
           - 数值计算错误
           - 数值比较错误
           - 数值统计错误
           - 单位/格式错误
        2. 理解错误
           - 实体识别错误
           - 条件理解错误
           - 关系理解错误
        3. 推理错误
           - 逻辑推理错误
           - 排序错误
           - 筛选错误
        4. 答案格式错误
           - 多答案处理错误
           - 格式不匹配
        5. 其他错误
        """
        question = str(bad_case['question']).lower()
        gold = str(bad_case['gold']).strip().lower()
        pred = str(bad_case['pred']).strip().lower()

        # 检查是否是数值类型的答案
        gold_is_number = self._is_number(gold)
        pred_is_number = self._is_number(pred)

        # 检查是否是布尔类型的答案
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
                # 两个都是实体名称，但不同
                if self._are_similar_entities(gold, pred):
                    return '实体识别错误（相似实体）'
                else:
                    return '实体识别错误（完全错误）'

        # 4. 答案数量错误
        if '|' in pred and '|' not in gold:
            return '多答案处理错误（应返回单个答案）'
        if '|' in gold and '|' not in pred:
            return '多答案处理错误（应返回多个答案）'

        # 5. 条件理解错误
        if any(kw in question for kw in ['next', 'previous', 'following', 'after', 'before']):
            return '条件理解错误（时序/顺序）'

        if any(kw in question for kw in ['larger', 'smaller', 'greater', 'more', 'less']):
            return '条件理解错误（比较关系）'

        # 6. 字符串相似度分析
        if gold and pred:
            if gold in pred or pred in gold:
                return '部分匹配错误（包含关系）'
            if self._are_similar_strings(gold, pred):
                return '部分匹配错误（相似字符串）'

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
        """检查是否是实体名称（人名、地名等）"""
        # 简单判断：包含字母且不是纯数字，不是yes/no等布尔值
        text = text.strip().lower()
        if text in ['yes', 'no', 'true', 'false']:
            return False
        if self._is_number(text):
            return False
        # 包含字母
        return any(c.isalpha() for c in text)

    def _are_similar_entities(self, entity1: str, entity2: str) -> bool:
        """判断两个实体是否相似（如同一个人名的不同写法）"""
        e1 = entity1.lower().strip()
        e2 = entity2.lower().strip()

        # 完全相同
        if e1 == e2:
            return True

        # 包含关系
        if e1 in e2 or e2 in e1:
            return True

        # 相似度阈值
        similarity = self._string_similarity(e1, e2)
        return similarity > 0.6

    def _are_similar_strings(self, str1: str, str2: str) -> bool:
        """判断两个字符串是否相似"""
        return self._string_similarity(str1.lower(), str2.lower()) > 0.5

    def _string_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度（简单的编辑距离）"""
        if not str1 or not str2:
            return 0.0

        len1, len2 = len(str1), len(str2)
        if len1 < len2:
            str1, str2 = str2, str1
            len1, len2 = len2, len1

        # 简单的包含关系
        if str1 in str2 or str2 in str1:
            return 0.8

        # 计算编辑距离（简化版）
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j

        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if str1[i-1] == str2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1

        max_len = max(len1, len2)
        return 1.0 - dp[len1][len2] / max_len

    def _classify_numerical_error(self, question: str, gold: str, pred: str) -> str:
        """分类数值错误"""
        try:
            gold_num = float(gold)
            pred_num = float(pred)
        except:
            return '数值错误（无法解析）'

        # 检查问题类型
        if any(kw in question for kw in ['sum', 'total', 'add', 'aggregate']):
            return '数值计算错误（求和）'

        if any(kw in question for kw in ['average', 'mean']):
            return '数值计算错误（平均）'

        if any(kw in question for kw in ['count', 'how many', 'how much', 'number of']):
            return '数值统计错误（计数）'

        if any(kw in question for kw in ['maximum', 'max', 'most', 'largest', 'highest']):
            return '数值比较错误（最大值）'

        if any(kw in question for kw in ['minimum', 'min', 'least', 'smallest', 'lowest']):
            return '数值比较错误（最小值）'

        # 检查数值关系
        if gold_num == 0 and pred_num != 0:
            return '数值统计错误（空值误判）'

        if pred_num == 0 and gold_num != 0:
            return '数值统计错误（遗漏计数）'

        # 检查是否是倍数关系
        if gold_num != 0 and pred_num != 0:
            ratio = pred_num / gold_num
            if abs(ratio - 2.0) < 0.1:
                return '数值计算错误（2倍关系）'
            if abs(ratio - 0.5) < 0.1:
                return '数值计算错误（0.5倍关系）'

        # 检查差值
        diff = abs(gold_num - pred_num)
        if diff == 1:
            return '数值统计错误（相差1）'
        if diff <= 5:
            return '数值统计错误（小范围偏差）'

        return '数值计算错误（其他）'


################ 分析器 ################

class AdvancedBadCaseAnalyzer:
    """高级Bad Case分析器"""

    def __init__(self, current_project_path: str, reference_project_path: str):
        self.current_project_path = Path(current_project_path)
        self.reference_project_path = Path(reference_project_path)
        self.current_data = None
        self.reference_data = None
        self.classifier = AdvancedErrorClassifier()

    def load_pkl(self, pkl_path: str) -> List[Dict]:
        """加载 pkl 文件"""
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
        return data

    def load_data(self):
        """加载两个项目的数据"""
        current_pkl = self.current_project_path / "final_result.pkl"
        self.current_data = self.load_pkl(str(current_pkl))

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

        if target_values_map is None:
            target_values_map = self.load_target_values_map()

        for item in data:
            if item is None:
                continue

            sample_id = item.get('ids', item.get('id', ''))

            if sample_id not in target_values_map:
                continue

            is_correct = wikitq_match_func(item, target_values_map[sample_id], strategy="top")

            if not is_correct:
                answer_list = item.get('answer', [])
                if isinstance(answer_list, list) and len(answer_list) > 0:
                    gold_answer = answer_list[0] if answer_list else ''
                else:
                    gold_answer = str(answer_list) if answer_list else ''

                chain = item.get('chain', [])
                pred_answer = ''
                if isinstance(chain, list) and len(chain) > 0:
                    last_op = chain[-1]
                    if isinstance(last_op, dict):
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

                # 使用高级分类器
                error_type = self.classifier.classify_error(bad_case)
                bad_case['error_type'] = error_type
                error_types[error_type] += 1

                bad_cases.append(bad_case)

        return bad_cases, dict(error_types)

    def generate_advanced_analysis_report(self, current_bad_cases: List[Dict],
                                         reference_bad_cases: List[Dict],
                                         current_error_types: Dict,
                                         reference_error_types: Dict) -> str:
        """生成高级分析报告"""

        report = ["\n\n---\n\n"]
        report.append("# 高级错误分类分析\n\n")
        report.append("## 错误分类体系\n\n")
        report.append("本分析将错误分为以下几大类：\n\n")
        report.append("### 1. 数值错误\n")
        report.append("- 数值计算错误（求和、平均等）\n")
        report.append("- 数值比较错误（最大值、最小值）\n")
        report.append("- 数值统计错误（计数、偏差）\n\n")
        report.append("### 2. 理解错误\n")
        report.append("- 实体识别错误（相似实体、完全错误）\n")
        report.append("- 条件理解错误（时序/顺序、比较关系）\n\n")
        report.append("### 3. 答案格式错误\n")
        report.append("- 多答案处理错误\n\n")
        report.append("### 4. 其他错误\n")
        report.append("- 部分匹配错误\n")
        report.append("- 完全不匹配\n\n")

        report.append("---\n\n")
        report.append("## 当前项目错误分类详情\n\n")

        # 按大类汇总
        current_categories = self._group_by_category(current_error_types)
        report.append(self._format_category_stats("当前项目", current_categories, len(current_bad_cases)))

        report.append("\n### 详细错误类型分布\n\n")
        for error_type, count in sorted(current_error_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(current_bad_cases) * 100) if current_bad_cases else 0
            report.append(f"- **{error_type}**: {count} ({percentage:.1f}%)\n")

        report.append("\n---\n\n")
        report.append("## 参考项目错误分类详情\n\n")

        reference_categories = self._group_by_category(reference_error_types)
        report.append(self._format_category_stats("参考项目", reference_categories, len(reference_bad_cases)))

        report.append("\n### 详细错误类型分布\n\n")
        for error_type, count in sorted(reference_error_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(reference_bad_cases) * 100) if reference_bad_cases else 0
            report.append(f"- **{error_type}**: {count} ({percentage:.1f}%)\n")

        report.append("\n---\n\n")
        report.append("## 对比分析\n\n")

        # 大类对比
        all_categories = set(current_categories.keys()) | set(reference_categories.keys())
        report.append("### 大类对比\n\n")

        for category in sorted(all_categories):
            current_count = current_categories.get(category, 0)
            reference_count = reference_categories.get(category, 0)

            current_pct = (current_count / len(current_bad_cases) * 100) if current_bad_cases else 0
            reference_pct = (reference_count / len(reference_bad_cases) * 100) if reference_bad_cases else 0

            if current_count > reference_count:
                diff = current_count - reference_count
                report.append(f"- ⚠️ **{category}**: 当前项目更多 ({current_count}/{current_pct:.1f}% vs {reference_count}/{reference_pct:.1f}%, +{diff})\n")
            elif current_count < reference_count:
                diff = reference_count - current_count
                report.append(f"- ✅ **{category}**: 参考项目更多 ({current_count}/{current_pct:.1f}% vs {reference_count}/{reference_pct:.1f}%, -{diff})\n")
            else:
                report.append(f"- ➖ **{category}**: 相同 ({current_count}/{current_pct:.1f}%)\n")

        # 具体错误类型对比
        report.append("\n### 具体错误类型对比（Top 10）\n\n")
        all_error_types = set(current_error_types.keys()) | set(reference_error_types.keys())

        # 按总错误数排序
        sorted_errors = sorted(all_error_types,
                             key=lambda x: current_error_types.get(x, 0) + reference_error_types.get(x, 0),
                             reverse=True)[:10]

        for error_type in sorted_errors:
            current_count = current_error_types.get(error_type, 0)
            reference_count = reference_error_types.get(error_type, 0)

            if current_count == 0 and reference_count == 0:
                continue

            report.append(f"#### {error_type}\n\n")
            report.append(f"- 当前项目: {current_count} ({(current_count/len(current_bad_cases)*100):.1f}%)\n")
            report.append(f"- 参考项目: {reference_count} ({(reference_count/len(reference_bad_cases)*100):.1f}%)\n")

            if current_count > reference_count:
                report.append(f"- **差异**: 当前项目多 {current_count - reference_count} 个\n")
            elif current_count < reference_count:
                report.append(f"- **差异**: 参考项目多 {reference_count - current_count} 个\n")
            else:
                report.append(f"- **差异**: 相同\n")

            report.append("\n")

        # 典型错误案例
        report.append("---\n\n")
        report.append("## 典型错误案例分析\n\n")

        # 每个大类的典型案例
        for category in ['数值错误', '理解错误', '答案格式错误']:
            report.append(f"### {category}\n\n")

            # 找到该大类的案例
            category_cases = [case for case in current_bad_cases
                            if self._get_error_category(case['error_type']) == category][:3]

            for i, case in enumerate(category_cases, 1):
                report.append(f"#### 案例 {i}\n\n")
                report.append(f"**UID**: `{case['uid']}`\n\n")
                report.append(f"**问题**: {case['question']}\n\n")
                report.append(f"**正确答案**: `{case['gold']}`\n\n")
                report.append(f"**预测答案**: `{case['pred']}`\n\n")
                report.append(f"**错误类型**: {case['error_type']}\n\n")
                report.append("---\n\n")

        return ''.join(report)

    def _group_by_category(self, error_types: Dict[str, int]) -> Dict[str, int]:
        """按大类汇总错误类型"""
        categories = defaultdict(int)

        for error_type, count in error_types.items():
            category = self._get_error_category(error_type)
            categories[category] += count

        return dict(categories)

    def _get_error_category(self, error_type: str) -> str:
        """获取错误类型所属的大类"""
        if '数值' in error_type:
            return '数值错误'
        elif '理解' in error_type or '实体' in error_type or '条件' in error_type:
            return '理解错误'
        elif '格式' in error_type or '多答案' in error_type:
            return '答案格式错误'
        elif '布尔' in error_type:
            return '布尔判断错误'
        else:
            return '其他错误'

    def _format_category_stats(self, project_name: str, categories: Dict[str, int], total: int) -> str:
        """格式化大类统计"""
        report = [f"### {project_name}大类统计\n\n"]
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            report.append(f"- **{category}**: {count} ({percentage:.1f}%)\n")
        return ''.join(report)


def main():
    """主函数"""
    current_project = "results/refine/wikitq/sota/gpt-5.4"
    reference_project = "/home/ubuntu/mnt/lx/Table-Critic/results/refine/wikitq/gpt-5.4"

    print("=" * 60)
    print("高级错误分类分析")
    print("=" * 60)
    print(f"\n当前项目: {current_project}")
    print(f"参考项目: {reference_project}\n")

    # 创建分析器
    analyzer = AdvancedBadCaseAnalyzer(current_project, reference_project)

    # 加载数据
    print("开始生成分析报告...")
    analyzer.load_data()

    # 加载目标值映射
    print("\n加载目标值映射...")
    target_values_map = analyzer.load_target_values_map()

    # 分析 bad cases
    print("\n分析当前项目 bad cases...")
    current_bad_cases, current_error_types = analyzer.analyze_bad_cases(analyzer.current_data, target_values_map)
    print(f"发现 {len(current_bad_cases)} 个错误案例")

    print("\n分析参考项目 bad cases...")
    reference_bad_cases, reference_error_types = analyzer.analyze_bad_cases(analyzer.reference_data, target_values_map)
    print(f"发现 {len(reference_bad_cases)} 个错误案例")

    # 生成高级分析报告
    print("\n生成高级分析报告...")
    advanced_report = analyzer.generate_advanced_analysis_report(
        current_bad_cases, reference_bad_cases,
        current_error_types, reference_error_types
    )

    # 追加到现有报告
    output_path = "bad-case-analysis.md"
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(advanced_report)

    print(f"\n✅ 高级分析完成！报告已追加到: {output_path}")
    print(f"新增内容大小: {len(advanced_report)} 字符")

    return advanced_report


if __name__ == "__main__":
    main()
