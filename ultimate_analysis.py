#!/usr/bin/env python3
"""
最终简洁版综合分析脚本
使用正确的判断方法，提取完整信息
"""

import pickle
import os
import sys
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# 复制evaluate.py中的评估函数
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
    results = sample["chain"][-1]["parameter_and_conf"]
    if strategy == "top":
        res = results[0][0]
    else:
        raise NotImplementedError
    pred_answer = [res.lower()] if '|' not in res else [r for r in res.lower().split('|')]
    pred_answer = to_value_list(pred_answer)
    return check_denotation(target_values, pred_answer)

def load_target_values_map(tagged_data_path='thought/TableQA/data/wikitq/tagged_data'):
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

class SimpleAnalyzer:
    """简洁分析器"""
    
    def classify_error(self, question: str, gold: str, pred: str) -> str:
        """简单分类错误"""
        question = question.lower()
        gold = str(gold).strip().lower()
        pred = str(pred).strip().lower()
        
        # 数值错误
        if gold.isdigit() and pred.isdigit():
            if any(kw in question for kw in ['count', 'how many', 'number of']):
                return '数值统计错误'
            if any(kw in question for kw in ['sum', 'total', 'add']):
                return '数值计算错误'
            return '数值错误'
        
        # 布尔错误
        if gold in ['true', 'false', 'yes', 'no'] and pred in ['true', 'false', 'yes', 'no']:
            return '布尔判断错误'
        
        # 多答案
        if '|' in pred:
            return '多答案处理错误'
        
        # 实体/理解错误
        if any(kw in question for kw in ['who', 'which', 'what', 'name', 'where']):
            return '实体识别错误'
        
        return '其他错误'
    
    def format_chain_brief(self, chain: List) -> str:
        """简要格式化思维链"""
        if not chain:
            return "无"
        steps = []
        for i, step in enumerate(chain[:5]):  # 最多5步
            if isinstance(step, dict):
                op = step.get('operation_name', '?')
                thought = step.get('thought', '')
                if thought:
                    thought = str(thought)[:80] + "..." if len(str(thought)) > 80 else thought
                    steps.append(f"{i+1}. {op}: {thought}")
                else:
                    steps.append(f"{i+1}. {op}")
        return "\n".join(steps)
    
    def format_table_brief(self, table: List) -> str:
        """简要格式化表格"""
        if not table or not isinstance(table, list):
            return "无"
        # 只显示前5行
        rows = []
        for row in table[:5]:
            if isinstance(row, list):
                rows.append(" | ".join(str(c)[:20] for c in row))
            else:
                rows.append(str(row)[:80])
        return "\n".join(rows) + ("\n..." if len(table) > 5 else "")

def main():
    print("=" * 60)
    print("最终简洁版综合分析")
    print("=" * 60)
    
    analyzer = SimpleAnalyzer()
    
    # ===== 分析WikiTQ =====
    print("\n[1/3] 加载WikiTQ数据...")
    with open('results/refine/wikitq/sota/gpt-5.4/final_result.pkl', 'rb') as f:
        wikitq_data = pickle.load(f)
    
    print("[2/3] 加载目标值映射...")
    target_values_map = load_target_values_map()
    print(f"加载了 {len(target_values_map)} 个目标值")
    
    print("[3/3] 分析WikiTQ错误案例...")
    wikitq_bad_cases = []
    wikitq_error_types = defaultdict(list)
    
    for item in wikitq_data:
        if item is None:
            continue
        sample_id = item.get('ids', item.get('id', ''))
        if sample_id not in target_values_map:
            continue
        
        # 使用正确的方法判断
        is_correct = wikitq_match_func(item, target_values_map[sample_id], strategy="top")
        if not is_correct:
            answer_list = item.get('answer', [])
            gold_answer = answer_list[0] if answer_list else ''
            
            chain = item.get('chain', [])
            pred_answer = ''
            if chain and len(chain) > 0:
                last_op = chain[-1]
                if isinstance(last_op, dict):
                    param_conf = last_op.get('parameter_and_conf', [])
                    if param_conf and len(param_conf) > 0:
                        pred_answer = str(param_conf[0][0]) if param_conf[0] else ''
            
            error_type = analyzer.classify_error(
                item.get('statement', ''),
                str(gold_answer),
                pred_answer
            )
            
            case = {
                'uid': sample_id,
                'question': item.get('statement', ''),
                'gold': str(gold_answer),
                'pred': pred_answer,
                'error_type': error_type,
                'table': item.get('table_text', []),
                'chain': chain,
                'clarifier': item.get('clarifier', {}),
            }
            
            wikitq_bad_cases.append(case)
            wikitq_error_types[error_type].append(sample_id)
    
    print(f"发现 {len(wikitq_bad_cases)} 个错误案例")
    
    # ===== 分析TabFact =====
    print("\n[1/2] 加载TabFact数据...")
    with open('results/refine/tabfact/sota/gpt-5.4/final_result.pkl', 'rb') as f:
        tabfact_data = pickle.load(f)
    
    print("[2/2] 分析TabFact错误案例...")
    tabfact_bad_cases = []
    tabfact_error_types = defaultdict(list)
    
    for item in tabfact_data:
        if item is None:
            continue
        
        # TabFact: 使用label字段判断
        gold_label = item.get('label', None)
        pred_label = item.get('predicted_label', None)
        
        # 如果没有predicted_label，从chain推断
        if pred_label is None:
            chain = item.get('chain', [])
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
        
        if gold_label is not None and pred_label is not None and gold_label != pred_label:
            case = {
                'uid': item.get('id', 'unknown'),
                'question': item.get('statement', ''),
                'gold': str(bool(gold_label)),
                'pred': str(bool(pred_label)),
                'error_type': '布尔判断错误',
                'table': item.get('table_text', []),
                'chain': item.get('chain', []),
                'clarifier': item.get('clarifier', {}),
            }
            
            tabfact_bad_cases.append(case)
            tabfact_error_types[case['error_type']].append(case['uid'])
    
    print(f"发现 {len(tabfact_bad_cases)} 个错误案例")
    
    # ===== 生成简洁报告 =====
    print("\n生成简洁报告...")
    report = ["# 综合Bad Case分析报告（简洁版）\n\n"]
    report.append("**生成时间**: 2026-04-16\n\n")
    
    # 汇总
    report.append("## 汇总统计\n\n")
    report.append(f"- **WikiTQ**: {len(wikitq_bad_cases)} 个错误案例\n")
    report.append(f"- **TabFact**: {len(tabfact_bad_cases)} 个错误案例\n\n")
    
    # WikiTQ错误分类
    report.append("## WikiTQ错误分类\n\n")
    for error_type, uids in sorted(wikitq_error_types.items()):
        report.append(f"- **{error_type}**: {len(uids)} 个案例\n")
    
    # TabFact错误分类
    report.append("\n## TabFact错误分类\n\n")
    for error_type, uids in sorted(tabfact_error_types.items()):
        report.append(f"- **{error_type}**: {len(uids)} 个案例\n")
    
    # 错误案例ID表
    report.append("\n## 错误案例ID分类表\n\n")
    report.append("| 数据集 | 类型 | ID列表 |\n")
    report.append("|-------|------|--------|\n")
    
    for error_type, uids in sorted(wikitq_error_types.items()):
        uid_str = ", ".join(uids[:10]) + ("..." if len(uids) > 10 else "")
        report.append(f"| WikiTQ | {error_type} | {uid_str} |\n")
    
    for error_type, uids in sorted(tabfact_error_types.items()):
        uid_str = ", ".join(uids[:10]) + ("..." if len(uids) > 10 else "")
        report.append(f"| TabFact | {error_type} | {uid_str} |\n")
    
    # WikiTQ示例案例
    report.append("\n## WikiTQ错误案例示例\n\n")
    
    for error_type in sorted(wikitq_error_types.keys()):
        cases = [c for c in wikitq_bad_cases if c['error_type'] == error_type][:1]
        if not cases:
            continue
        
        case = cases[0]
        report.append(f"### {error_type}\n\n")
        report.append(f"**UID**: `{case['uid']}`\n\n")
        report.append(f"**问题**: {case['question']}\n\n")
        report.append(f"**正确答案**: `{case['gold']}`\n\n")
        report.append(f"**预测答案**: `{case['pred']}`\n\n")
        
        # 简要思维链
        chain_brief = analyzer.format_chain_brief(case['chain'])
        report.append(f"**思维链**:\n```\n{chain_brief}\n```\n\n")
        
        # 简要表格
        table_brief = analyzer.format_table_brief(case['table'])
        report.append(f"**表格（前5行）**:\n```\n{table_brief}\n```\n\n")
        
        report.append("---\n\n")
    
    # TabFact示例案例
    report.append("## TabFact错误案例示例\n\n")
    
    cases = tabfact_bad_cases[:3]
    for i, case in enumerate(cases, 1):
        report.append(f"### 案例 {i}\n\n")
        report.append(f"**UID**: `{case['uid']}`\n\n")
        report.append(f"**陈述**: {case['question']}\n\n")
        report.append(f"**正确答案**: `{case['gold']}`\n\n")
        report.append(f"**预测答案**: `{case['pred']}`\n\n")
        
        # 简要思维链
        chain_brief = analyzer.format_chain_brief(case['chain'])
        report.append(f"**思维链**:\n```\n{chain_brief}\n```\n\n")
        
        report.append("---\n\n")
    
    # 保存
    output_path = "ultimate_analysis.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(report))
    
    print(f"\n✅ 完成！报告已保存: {output_path}")
    print(f"报告大小: {len(''.join(report))} 字符")
    
    return output_path

if __name__ == "__main__":
    main()
