#!/usr/bin/env python3
"""
对比分析：找出当前项目特有错误案例
当前项目出错但参考项目正确的案例
"""

import pickle
import os
import re
import unicodedata
from typing import Dict, List, Set
from collections import defaultdict

# 复制评估函数
def normalize(x):
    if not isinstance(x, str):
        x = str(x)
    x = ''.join(c for c in unicodedata.normalize('NFKD', x)
                if unicodedata.category(c) != 'Mn')
    x = re.sub(r"[‘’´`]", "'", x)
    x = re.sub(r'[“”]', '"', x)
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

def load_original_tables(jsonl_path='thought/TableQA/data/wikitq/test_lower.jsonl'):
    """加载原始表格数据"""
    original_tables = {}
    if not os.path.exists(jsonl_path):
        print(f"警告: 原始数据文件不存在: {jsonl_path}")
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
            except Exception as e:
                print(f"警告: 解析行失败: {e}")
                continue

    print(f"加载了 {len(original_tables)} 个原始表格")
    return original_tables

class DifferentialAnalyzer:
    """对比分析器"""
    
    def classify_error(self, question: str, gold: str, pred: str) -> str:
        """分类错误"""
        question = question.lower()
        gold = str(gold).strip().lower()
        pred = str(pred).strip().lower()
        
        if gold.isdigit() and pred.isdigit():
            if any(kw in question for kw in ['count', 'how many', 'number of']):
                return '数值统计错误'
            if any(kw in question for kw in ['sum', 'total', 'add']):
                return '数值计算错误'
            return '数值错误'
        
        if gold in ['true', 'false', 'yes', 'no'] and pred in ['true', 'false', 'yes', 'no']:
            return '布尔判断错误'
        
        if '|' in pred:
            return '多答案处理错误'
        
        if any(kw in question for kw in ['who', 'which', 'what', 'name', 'where']):
            return '实体识别错误'
        
        return '其他错误'
    
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

def main():
    print("=" * 60)
    print("横向对比分析：当前项目特有错误案例")
    print("=" * 60)
    
    analyzer = DifferentialAnalyzer()
    
    # 加载目标值映射
    print("\n加载目标值映射...")
    target_values_map = load_target_values_map()
    print(f"加载了 {len(target_values_map)} 个目标值")

    # 加载原始表格数据
    print("\n加载原始表格数据...")
    original_tables = load_original_tables('thought/TableQA/data/wikitq/test_lower.jsonl')

    # 加载当前项目数据
    print("\n[1/4] 加载当前项目数据...")
    with open('results/refine/wikitq/sota/gpt-5.4/final_result.pkl', 'rb') as f:
        current_data = pickle.load(f)
    print(f"当前项目 WikiTQ: {len(current_data)} 条")
    
    # 加载参考项目数据
    print("[2/4] 加载参考项目数据...")
    ref_wikitq_path = "/home/ubuntu/mnt/lx/Table-Critic/results/refine/wikitq/gpt-5.4/final_result.pkl"
    with open(ref_wikitq_path, 'rb') as f:
        reference_data = pickle.load(f)
    print(f"参考项目 WikiTQ: {len(reference_data)} 条")
    
    # 判断当前项目的错误案例
    print("[3/4] 分析当前项目错误案例...")
    current_errors = set()
    current_error_details = {}
    
    for item in current_data:
        if item is None:
            continue
        sample_id = item.get('ids', item.get('id', ''))
        if sample_id not in target_values_map:
            continue
        
        is_correct = wikitq_match_func(item, target_values_map[sample_id], strategy="top")
        if not is_correct:
            current_errors.add(sample_id)
            
            # 提取详细信息
            answer_list = item.get('answer', [])
            # 修复：完整显示所有答案，而不是只取第一个
            gold_answer = '|'.join(str(a) for a in answer_list) if answer_list else ''
            
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

            # 获取原始表格数据
            original_table = original_tables.get(sample_id, {})

            current_error_details[sample_id] = {
                'uid': sample_id,
                'question': item.get('statement', ''),
                'gold': str(gold_answer),
                'pred': pred_answer,
                'error_type': error_type,
                'table': item.get('table_text', []),
                'original_table': original_table,
                'chain': chain,
            }
    
    print(f"当前项目错误案例: {len(current_errors)}")
    
    # 判断参考项目的错误案例
    print("[4/4] 分析参考项目错误案例...")
    reference_errors = set()
    
    for item in reference_data:
        if item is None:
            continue
        sample_id = item.get('ids', item.get('id', ''))
        if sample_id not in target_values_map:
            continue
        
        is_correct = wikitq_match_func(item, target_values_map[sample_id], strategy="top")
        if not is_correct:
            reference_errors.add(sample_id)
    
    print(f"参考项目错误案例: {len(reference_errors)}")
    
    # 找出当前项目特有的错误案例
    current_only_errors = current_errors - reference_errors
    
    print(f"\n当前项目特有错误: {len(current_only_errors)}")
    print(f"参考项目特有错误: {len(reference_errors - current_errors)}")
    
    # 按错误类型分类
    current_only_by_type = defaultdict(list)
    for uid in current_only_errors:
        if uid in current_error_details:
            error_type = current_error_details[uid]['error_type']
            current_only_by_type[error_type].append(uid)
    
    print("\n当前项目特有错误分类:")
    for error_type, uids in sorted(current_only_by_type.items()):
        print(f"  {error_type}: {len(uids)} 个")
    
    # 生成报告
    print("\n生成对比分析报告...")
    report = ["\n\n---\n\n"]
    report.append("# 第三部分：横向对比分析 - 当前项目特有错误案例\n\n")
    report.append("**生成时间**: 2026-04-16\n\n")
    report.append("**说明**: 本部分分析当前项目(new_TC)出错但参考项目(Table-Critic)正确的案例，这是当前项目的特有问题，需要重点改进。\n\n")
    
    # 汇总统计
    report.append("## 汇总统计\n\n")
    report.append(f"- **当前项目特有错误案例总数**: {len(current_only_errors)}\n")
    report.append(f"- **当前项目错误案例总数**: {len(current_errors)}\n")
    report.append(f"- **参考项目错误案例总数**: {len(reference_errors)}\n")
    report.append(f"- **特有错误占比**: {len(current_only_errors)/len(current_errors)*100:.1f}%\n\n")
    
    # 错误分类统计
    report.append("## 当前项目特有错误分类\n\n")
    for error_type, uids in sorted(current_only_by_type.items()):
        report.append(f"### {error_type}\n\n")
        report.append(f"- **数量**: {len(uids)}\n")
        report.append(f"- **占比**: {len(uids)/len(current_only_errors)*100:.1f}%\n")
        report.append(f"- **ID列表**: {', '.join(uids[:10])}{'...' if len(uids) > 10 else ''}\n\n")
    
    # 详细案例展示（每种类型2-3个）
    report.append("## 当前项目特有错误案例详细分析\n\n")
    
    for error_type in sorted(current_only_by_type.keys()):
        uids = current_only_by_type[error_type][:3]  # 每种类型最多3个案例
        
        report.append(f"### {error_type}\n\n")
        
        for i, uid in enumerate(uids, 1):
            if uid not in current_error_details:
                continue
            
            case = current_error_details[uid]
            report.append(f"#### 案例 {i}: `{uid}`\n\n")
            report.append(f"**问题**: {case['question']}\n\n")
            report.append(f"**正确答案**: `{case['gold']}`\n\n")
            report.append(f"**当前项目预测**: `{case['pred']}`\n\n")
            
            # 完整思维链
            report.append(f"**完整思维链**:\n```\n{analyzer.format_chain_full(case['chain'])}\n```\n\n")

            # 完整表格
            report.append(f"**完整表格**:\n```\n{analyzer.format_table_full(case['table'])}\n```\n\n")

            # 原始表格
            report.append(f"**原始表格**:\n```\n{analyzer.format_original_table(case['original_table'])}\n```\n\n")

            report.append("---\n\n")
    
    # 保存报告
    output_path = "differential_analysis.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(report))
    
    print(f"\n✅ 完成！报告已保存: {output_path}")
    print(f"报告大小: {len(''.join(report))} 字符")
    
    return output_path

if __name__ == "__main__":
    main()
