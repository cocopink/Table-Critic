#!/usr/bin/env python3
"""
综合Bad Case分析脚本
包括WikiTQ和TabFact两个数据集
提取完整的思维链、表格信息
"""

import pickle
import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import os
import re
import unicodedata

################ 评估函数 ################

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

################ 详细案例分析器 ################

class DetailedCaseAnalyzer:
    """详细案例分析器"""
    
    def __init__(self):
        pass
    
    def extract_wikitq_case(self, sample: Dict) -> Dict[str, Any]:
        """提取WikiTQ案例详情"""
        # 提取思维链
        chain = sample.get('chain', [])
        chain_text = self._format_chain(chain)
        
        # 提取表格
        table = sample.get('table_text', [])
        table_text = self._format_table(table)
        
        # 提取预测答案
        pred_answer = ""
        if chain and len(chain) > 0:
            last_op = chain[-1]
            if isinstance(last_op, dict):
                param_conf = last_op.get('parameter_and_conf', [])
                if param_conf and len(param_conf) > 0:
                    pred_answer = str(param_conf[0][0]) if param_conf[0] else ""
        
        # 提取正确答案
        answer_list = sample.get('answer', [])
        gold_answer = answer_list[0] if answer_list else ""
        
        return {
            'uid': sample.get('id', sample.get('ids', 'unknown')),
            'question': sample.get('statement', ''),
            'gold': str(gold_answer),
            'pred': pred_answer,
            'table': table_text,
            'chain': chain_text,
            'clarifier': self._format_clarifier(sample.get('clarifier', {})),
            'refine_history': self._extract_refine_history(sample),
        }
    
    def extract_tabfact_case(self, sample: Dict) -> Dict[str, Any]:
        """提取TabFact案例详情"""
        # 提取思维链
        chain = sample.get('chain', [])
        chain_text = self._format_chain(chain)
        
        # 提取表格
        table = sample.get('table_text', [])
        table_text = self._format_table(table)
        
        # 提取预测结果（TabFact使用布尔值）
        pred_result = sample.get('predicted_label', '')
        gold_label = sample.get('label', '')
        
        # 转换标签为可读形式
        gold_str = "True" if gold_label == 1 else "False"
        pred_str = "True" if pred_result == 1 else "False"
        
        return {
            'uid': sample.get('id', 'unknown'),
            'question': sample.get('statement', ''),
            'gold': gold_str,
            'pred': pred_str,
            'table': table_text,
            'chain': chain_text,
            'clarifier': self._format_clarifier(sample.get('clarifier', {})),
            'refine_history': self._extract_refine_history(sample),
        }
    
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
                    # 限制思考长度
                    thought_str = str(thought)
                    if len(thought_str) > 200:
                        thought_str = thought_str[:200] + "..."
                    step_desc += f"\n  思考: {thought_str}"
                if params:
                    # 限制参数长度
                    params_str = str(params)
                    if len(params_str) > 150:
                        params_str = params_str[:150] + "..."
                    step_desc += f"\n  参数: {params_str}"
                steps.append(step_desc)
        
        return "\n\n".join(steps) if steps else "无有效思维链"
    
    def _format_table(self, table: List) -> str:
        """格式化表格"""
        if not table:
            return "无表格数据"
        
        if isinstance(table, list) and len(table) > 0:
            lines = []
            for i, row in enumerate(table[:8]):  # 只显示前8行
                if isinstance(row, list):
                    # 限制每行长度
                    row_str = " | ".join(str(cell)[:30] for cell in row)
                    lines.append(row_str)
                else:
                    lines.append(str(row)[:100])
            return "\n".join(lines) + ("\n..." if len(table) > 8 else "")
        return str(table)[:500]
    
    def _format_clarifier(self, clarifier: Dict) -> str:
        """格式化Clarifier结果"""
        if not clarifier:
            return "无Clarifier结果"
        
        schema = clarifier.get('schema', clarifier.get('keyword_dict', {}))
        if not schema:
            return "Clarifier结果为空"
        
        items = []
        for key, value in list(schema.items())[:5]:  # 只显示前5个
            if isinstance(value, list):
                items.append(f"{key}: {', '.join(str(v)[:20] for v in value[:3])}")
            else:
                items.append(f"{key}: {str(value)[:50]}")
        
        return "\n".join(items) if items else "无有效Schema"
    
    def _extract_refine_history(self, sample: Dict) -> str:
        """提取纠错历史"""
        if 'refine_history' not in sample:
            return "无纠错历史"
        
        history = sample['refine_history']
        if not history:
            return "无纠错记录"
        
        events = []
        for i, event in enumerate(history[:3]):  # 只显示前3轮
            iteration = event.get('iteration', i)
            action = event.get('action', 'unknown')
            conclusion = event.get('conclusion', '')
            
            event_desc = f"轮次 {iteration}: {action}"
            if conclusion:
                event_desc += f" → {conclusion}"
            events.append(event_desc)
        
        return "\n".join(events) if events else "无有效纠错记录"

################ 错误分类器 ################

class ErrorClassifier:
    """错误分类器"""
    
    def classify_wikitq_error(self, case: Dict) -> str:
        """分类WikiTQ错误"""
        question = case['question'].lower()
        gold = case['gold'].strip().lower()
        pred = case['pred'].strip().lower()
        
        # 数值错误
        if gold.isdigit() and pred.isdigit():
            if any(kw in question for kw in ['count', 'how many', 'number of']):
                return '数值统计错误（计数）'
            if any(kw in question for kw in ['sum', 'total', 'add']):
                return '数值计算错误（求和）'
            return '数值计算错误（其他）'
        
        # 实体识别错误
        if any(kw in question for kw in ['who', 'which', 'what', 'name']):
            return '实体识别错误'
        
        # 多答案处理错误
        if '|' in pred and '|' not in gold:
            return '多答案处理错误'
        
        # 部分匹配
        if gold in pred or pred in gold:
            return '部分匹配错误'
        
        return '完全不匹配'
    
    def classify_tabfact_error(self, case: Dict) -> str:
        """分类TabFact错误"""
        question = case['question'].lower()
        gold = case['gold'].strip().lower()
        pred = case['pred'].strip().lower()
        
        # TabFact主要是布尔判断错误
        if gold != pred:
            # 尝试分析错误原因
            if 'never' in question or 'always' in question:
                return '条件理解错误（绝对量词）'
            if 'more than' in question or 'less than' in question:
                return '条件理解错误（比较关系）'
            return '布尔判断错误'
        
        return '其他错误'

################ 主分析器 ################

def main():
    print("=" * 60)
    print("综合Bad Case分析")
    print("=" * 60)
    
    analyzer = DetailedCaseAnalyzer()
    classifier = ErrorClassifier()
    
    # 分析WikiTQ
    print("\n分析WikiTQ数据集...")
    with open('results/refine/wikitq/sota/gpt-5.4/final_result.pkl', 'rb') as f:
        wikitq_data = pickle.load(f)
    
    wikitq_bad_cases = []
    wikitq_error_types = defaultdict(list)
    
    for item in wikitq_data:
        if item is None:
            continue
        
        judge_str = str(item.get('judge', ''))
        if '[Incorrect]' not in judge_str:
            continue
        
        # 提取案例详情
        case = analyzer.extract_wikitq_case(item)
        
        # 分类错误
        error_type = classifier.classify_wikitq_error(case)
        case['error_type'] = error_type
        case['dataset'] = 'WikiTQ'
        
        wikitq_bad_cases.append(case)
        wikitq_error_types[error_type].append(case['uid'])
    
    print(f"WikiTQ错误案例: {len(wikitq_bad_cases)}")
    
    # 分析TabFact
    print("\n分析TabFact数据集...")
    with open('results/refine/tabfact/sota/gpt-5.4/final_result.pkl', 'rb') as f:
        tabfact_data = pickle.load(f)
    
    tabfact_bad_cases = []
    tabfact_error_types = defaultdict(list)
    
    for item in tabfact_data:
        if item is None:
            continue
        
        judge_str = str(item.get('judge', ''))
        if '[Incorrect]' not in judge_str:
            continue
        
        # 提取案例详情
        case = analyzer.extract_tabfact_case(item)
        
        # 分类错误
        error_type = classifier.classify_tabfact_error(case)
        case['error_type'] = error_type
        case['dataset'] = 'TabFact'
        
        tabfact_bad_cases.append(case)
        tabfact_error_types[error_type].append(case['uid'])
    
    print(f"TabFact错误案例: {len(tabfact_bad_cases)}")
    
    # 生成报告
    print("\n生成综合分析报告...")
    report = ["# 综合Bad Case分析报告\n\n"]
    report.append("**生成时间**: 2026-04-16\n\n")
    report.append("---\n\n")
    
    # 汇总统计
    report.append("# 汇总统计\n\n")
    report.append(f"- **WikiTQ错误案例**: {len(wikitq_bad_cases)}\n")
    report.append(f"- **TabFact错误案例**: {len(tabfact_bad_cases)}\n")
    report.append(f"- **总错误案例**: {len(wikitq_bad_cases) + len(tabfact_bad_cases)}\n\n")
    
    # WikiTQ错误类型分布
    report.append("## WikiTQ错误类型分布\n\n")
    for error_type, uids in sorted(wikitq_error_types.items()):
        report.append(f"- {error_type}: {len(uids)}\n")
    
    # TabFact错误类型分布
    report.append("\n## TabFact错误类型分布\n\n")
    for error_type, uids in sorted(tabfact_error_types.items()):
        report.append(f"- {error_type}: {len(uids)}\n")
    
    # 错误案例ID分类表
    report.append("\n---\n\n")
    report.append("# 错误案例ID分类表\n\n")
    report.append("| 数据集 | 错误类型 | 错误案例ID | 数量 |\n")
    report.append("|-------|---------|-----------|------|\n")
    
    for error_type, uids in sorted(wikitq_error_types.items()):
        uid_str = ", ".join(uids)
        report.append(f"| WikiTQ | {error_type} | {uid_str} | {len(uids)} |\n")
    
    for error_type, uids in sorted(tabfact_error_types.items()):
        uid_str = ", ".join(uids)
        report.append(f"| TabFact | {error_type} | {uid_str} | {len(uids)} |\n")
    
    # WikiTQ详细案例分析
    report.append("\n---\n\n")
    report.append("# WikiTQ详细案例分析\n\n")
    
    # 按错误类型分组
    wikitq_cases_by_type = defaultdict(list)
    for case in wikitq_bad_cases:
        wikitq_cases_by_type[case['error_type']].append(case)
    
    for error_type in sorted(wikitq_cases_by_type.keys()):
        cases = wikitq_cases_by_type[error_type][:2]  # 每个类型2个案例
        
        report.append(f"## {error_type}\n\n")
        report.append(f"**案例数量**: {len(wikitq_cases_by_type[error_type])}\n\n")
        
        for i, case in enumerate(cases, 1):
            report.append(f"### 案例 {i}\n\n")
            report.append(f"**UID**: `{case['uid']}`\n\n")
            report.append(f"**问题**: {case['question']}\n\n")
            report.append(f"**正确答案**: `{case['gold']}`\n\n")
            report.append(f"**预测答案**: `{case['pred']}`\n\n")
            report.append(f"**错误类型**: {error_type}\n\n")
            
            # 表格
            report.append(f"**表格数据**:\n```\n{case['table']}\n```\n\n")
            
            # 思维链
            report.append(f"**思维链**:\n```\n{case['chain']}\n```\n\n")
            
            # Clarifier
            if case['clarifier'] != "无Clarifier结果":
                report.append(f"**Clarifier结果**:\n```\n{case['clarifier']}\n```\n\n")
            
            # 纠错历史
            if case['refine_history'] != "无纠错历史":
                report.append(f"**纠错历史**:\n```\n{case['refine_history']}\n```\n\n")
            
            report.append("---\n\n")
    
    # TabFact详细案例分析
    report.append("\n---\n\n")
    report.append("# TabFact详细案例分析\n\n")
    
    # 按错误类型分组
    tabfact_cases_by_type = defaultdict(list)
    for case in tabfact_bad_cases:
        tabfact_cases_by_type[case['error_type']].append(case)
    
    for error_type in sorted(tabfact_cases_by_type.keys()):
        cases = tabfact_cases_by_type[error_type][:2]  # 每个类型2个案例
        
        report.append(f"## {error_type}\n\n")
        report.append(f"**案例数量**: {len(tabfact_cases_by_type[error_type])}\n\n")
        
        for i, case in enumerate(cases, 1):
            report.append(f"### 案例 {i}\n\n")
            report.append(f"**UID**: `{case['uid']}`\n\n")
            report.append(f"**陈述**: {case['question']}\n\n")
            report.append(f"**正确标签**: `{case['gold']}`\n\n")
            report.append(f"**预测标签**: `{case['pred']}`\n\n")
            report.append(f"**错误类型**: {error_type}\n\n")
            
            # 表格
            report.append(f"**表格数据**:\n```\n{case['table']}\n```\n\n")
            
            # 思维链
            report.append(f"**思维链**:\n```\n{case['chain']}\n```\n\n")
            
            report.append("---\n\n")
    
    # 保存报告
    output_path = "comprehensive_bad_case_analysis.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(report))
    
    print(f"\n✅ 分析完成！")
    print(f"报告已保存到: {output_path}")
    print(f"报告大小: {len(''.join(report))} 字符")
    
    return output_path

if __name__ == "__main__":
    main()
