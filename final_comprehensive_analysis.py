#!/usr/bin/env python3
"""
最终版综合分析脚本
使用经过验证的判断方法
"""

import pickle
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# 导入经过验证的评估函数
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'refine', 'TableQA', 'utils'))
try:
    from evaluate import wikitq_match_func, to_value_list, tsv_unescape_list
except:
    # 如果导入失败，定义简化版本
    def wikitq_match_func(sample, target_values, strategy="top"):
        results = sample["chain"][-1]["parameter_and_conf"]
        res = results[0][0]
        pred_answer = [res.lower()] if '|' not in res else [r for r in res.lower().split('|')]
        # 简化版本
        return str(pred_answer[0]) if len(pred_answer) == 1 else res

class DetailedCaseAnalyzer:
    """详细案例分析器"""
    
    def __init__(self):
        pass
    
    def format_chain(self, chain: List) -> str:
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
                    thought_str = str(thought)[:200]
                    if len(thought_str) == 200:
                        thought_str += "..."
                    step_desc += f"\n  思考: {thought_str}"
                if params:
                    params_str = str(params)[:150]
                    if len(params_str) == 150:
                        params_str += "..."
                    step_desc += f"\n  参数: {params_str}"
                steps.append(step_desc)
        
        return "\n\n".join(steps) if steps else "无有效思维链"
    
    def format_table(self, table: List) -> str:
        """格式化表格"""
        if not table:
            return "无表格数据"
        
        if isinstance(table, list) and len(table) > 0:
            lines = []
            for i, row in enumerate(table[:8]):
                if isinstance(row, list):
                    row_str = " | ".join(str(cell)[:30] for cell in row)
                    lines.append(row_str)
                else:
                    lines.append(str(row)[:100])
            return "\n".join(lines) + ("\n..." if len(table) > 8 else "")
        return str(table)[:500]

def load_target_values_map(tagged_data_path='thought/TableQA/data/wikitq/tagged_data'):
    """加载目标值映射"""
    target_values_map = {}
    
    if not os.path.exists(tagged_data_path):
        print(f"警告: tagged_data路径不存在: {tagged_data_path}")
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
                
                # 简化版本：直接存储原始字符串
                target_values_map[ex_id] = {
                    'original': original_strings,
                    'canon': canon_strings
                }
    
    return target_values_map

def analyze_wikitq_with_correct_method():
    """使用正确方法分析WikiTQ"""
    print("\n分析WikiTQ（使用正确方法）...")
    
    with open('results/refine/wikitq/sota/gpt-5.4/final_result.pkl', 'rb') as f:
        data = pickle.load(f)
    
    # 使用judge字段判断（经过验证的方法）
    bad_cases = []
    error_types = defaultdict(list)
    
    for item in data:
        if item is None:
            continue
        
        judge_str = str(item.get('judge', ''))
        if '[Incorrect]' in judge_str:
            # 这是错误案例
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
            
            bad_case = {
                'uid': item.get('id', item.get('ids', 'unknown')),
                'question': item.get('statement', ''),
                'gold': str(gold_answer),
                'pred': pred_answer,
                'sample': item,
            }
            
            # 简单分类
            if str(gold_answer).isdigit() and str(pred_answer).isdigit():
                bad_case['error_type'] = '数值错误'
            elif str(gold_answer) in ['true', 'false', 'yes', 'no'] or str(pred_answer) in ['true', 'false', 'yes', 'no']:
                bad_case['error_type'] = '布尔判断错误'
            elif '|' in str(pred_answer):
                bad_case['error_type'] = '多答案处理错误'
            else:
                bad_case['error_type'] = '实体识别/理解错误'
            
            bad_cases.append(bad_case)
            error_types[bad_case['error_type']].append(bad_case['uid'])
    
    print(f"发现 {len(bad_cases)} 个错误案例")
    for error_type, uids in sorted(error_types.items()):
        print(f"  {error_type}: {len(uids)}")
    
    return bad_cases, dict(error_types)

def analyze_tabfact_with_correct_method():
    """使用正确方法分析TabFact"""
    print("\n分析TabFact（使用正确方法）...")
    
    with open('results/refine/tabfact/sota/gpt-5.4/final_result.pkl', 'rb') as f:
        data = pickle.load(f)
    
    bad_cases = []
    error_types = defaultdict(list)
    
    for item in data:
        if item is None:
            continue
        
        judge_str = str(item.get('judge', ''))
        if '[Incorrect]' in judge_str:
            # 这是错误案例
            gold_label = item.get('label', '')
            pred_label = item.get('predicted_label', '')
            
            # 转换为可读形式
            gold_str = "True" if gold_label == 1 else "False"
            pred_str = "True" if pred_label == 1 else "False" if pred_label != '' else "Unknown"
            
            bad_case = {
                'uid': item.get('id', 'unknown'),
                'question': item.get('statement', ''),
                'gold': gold_str,
                'pred': pred_str,
                'sample': item,
            }
            
            # 简单分类
            bad_case['error_type'] = '布尔判断错误'
            
            bad_cases.append(bad_case)
            error_types[bad_case['error_type']].append(bad_case['uid'])
    
    print(f"发现 {len(bad_cases)} 个错误案例")
    for error_type, uids in sorted(error_types.items()):
        print(f"  {error_type}: {len(uids)}")
    
    return bad_cases, dict(error_types)

def main():
    print("=" * 60)
    print("最终版综合Bad Case分析")
    print("=" * 60)
    
    analyzer = DetailedCaseAnalyzer()
    
    # 分析WikiTQ
    wikitq_bad_cases, wikitq_error_types = analyze_wikitq_with_correct_method()
    
    # 分析TabFact
    tabfact_bad_cases, tabfact_error_types = analyze_tabfact_with_correct_method()
    
    # 生成报告
    print("\n生成报告...")
    report = ["# 最终版综合Bad Case分析报告\n\n"]
    report.append("**生成时间**: 2026-04-16\n\n")
    report.append("---\n\n")
    
    # 汇总统计
    report.append("# 汇总统计\n\n")
    report.append(f"- **WikiTQ错误案例**: {len(wikitq_bad_cases)}\n")
    report.append(f"- **TabFact错误案例**: {len(tabfact_bad_cases)}\n")
    report.append(f"- **总错误案例**: {len(wikitq_bad_cases) + len(tabfact_bad_cases)}\n\n")
    
    # 错误案例ID分类表
    report.append("# 错误案例ID分类表\n\n")
    report.append("| 数据集 | 错误类型 | 错误案例ID | 数量 |\n")
    report.append("|-------|---------|-----------|------|\n")
    
    for error_type, uids in sorted(wikitq_error_types.items()):
        uid_str = ", ".join(uids)
        report.append(f"| WikiTQ | {error_type} | {uid_str} | {len(uids)} |\n")
    
    for error_type, uids in sorted(tabfact_error_types.items()):
        uid_str = ", ".join(uids)
        report.append(f"| TabFact | {error_type} | {uid_str} | {len(uids)} |\n")
    
    # WikiTQ详细案例分析（前10个）
    report.append("\n---\n\n")
    report.append("# WikiTQ详细案例分析（前10个案例）\n\n")
    
    for i, case in enumerate(wikitq_bad_cases[:10], 1):
        report.append(f"## 案例 {i}: {case['error_type']}\n\n")
        report.append(f"**UID**: `{case['uid']}`\n\n")
        report.append(f"**问题**: {case['question']}\n\n")
        report.append(f"**正确答案**: `{case['gold']}`\n\n")
        report.append(f"**预测答案**: `{case['pred']}`\n\n")
        
        # 提取详细信息
        sample = case['sample']
        
        # 表格
        table = sample.get('table_text', [])
        if table:
            report.append(f"**表格数据**:\n```\n{analyzer.format_table(table)}\n```\n\n")
        
        # 思维链
        chain = sample.get('chain', [])
        if chain:
            report.append(f"**思维链**:\n```\n{analyzer.format_chain(chain)}\n```\n\n")
        
        report.append("---\n\n")
    
    # TabFact详细案例分析（前10个）
    report.append("\n---\n\n")
    report.append("# TabFact详细案例分析（前10个案例）\n\n")
    
    for i, case in enumerate(tabfact_bad_cases[:10], 1):
        report.append(f"## 案例 {i}: {case['error_type']}\n\n")
        report.append(f"**UID**: `{case['uid']}`\n\n")
        report.append(f"**陈述**: {case['question']}\n\n")
        report.append(f"**正确标签**: `{case['gold']}`\n\n")
        report.append(f"**预测标签**: `{case['pred']}`\n\n")
        
        # 提取详细信息
        sample = case['sample']
        
        # 表格
        table = sample.get('table_text', [])
        if table:
            report.append(f"**表格数据**:\n```\n{analyzer.format_table(table)}\n```\n\n")
        
        # 思维链
        chain = sample.get('chain', [])
        if chain:
            report.append(f"**思维链**:\n```\n{analyzer.format_chain(chain)}\n```\n\n")
        
        report.append("---\n\n")
    
    # 保存报告
    output_path = "final_comprehensive_analysis.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(report))
    
    print(f"\n✅ 分析完成！")
    print(f"报告已保存到: {output_path}")
    print(f"报告大小: {len(''.join(report))} 字符")
    
    return output_path

if __name__ == "__main__":
    main()
