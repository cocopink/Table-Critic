#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Table-Critic 结果可视化脚本
展示三个阶段（Thought、Critic、Refine）的数据特征
"""

import os
import pickle
import json
import glob
from collections import defaultdict
from pathlib import Path


def table2string(table_text, num_rows=100):
    """将表格数据转换为字符串格式"""
    if not table_text or len(table_text) == 0:
        return "Empty table"
    
    header, rows = table_text[0], table_text[1:]
    rows = rows[:num_rows]
    
    linear_table = ""
    header = "col : " + " | ".join(header) + "\n"
    linear_table += header
    
    for row_idx, row in enumerate(rows):
        row = [str(x) for x in row]
        line = f"row {row_idx + 1} : " + " | ".join(row)
        if row_idx != len(rows) - 1:
            line += "\n"
        linear_table += line
    
    return linear_table


def load_pkl_files(directory, pattern="*.pkl"):
    """加载指定目录下的所有pkl文件"""
    pkl_files = glob.glob(os.path.join(directory, pattern))
    pkl_files.sort()
    return pkl_files


def analyze_sample(sample):
    """分析单个样本的数据特征"""
    # 处理sample可能是dict或tuple的情况
    if isinstance(sample, tuple) and len(sample) >= 1:
        # Thought阶段的pkl文件是tuple，第一个元素是原始sample
        sample = sample[0] if isinstance(sample[0], dict) else sample
    
    features = {
        'id': sample.get('id', 'N/A'),
        'statement': sample.get('statement', ''),
        'table_caption': sample.get('table_caption', ''),
        'label': sample.get('label', -1),
        'cleaned_statement': sample.get('cleaned_statement', ''),
        'table_rows': len(sample.get('table_text', [])) if sample.get('table_text') else 0,
        'table_cols': len(sample.get('table_text', [])[0]) if sample.get('table_text') else 0,
    }
    
    # 分析操作链
    chain = sample.get('chain', [])
    features['chain_length'] = len(chain)
    features['chain_operations'] = [op.get('operation_name', 'Unknown') for op in chain]
    
    # 分析Critic结果
    if 'critique' in sample:
        features['has_critique'] = True
        features['critique_length'] = len(sample.get('critique', ''))
        features['conclusion'] = sample.get('conclusion', '')
        features['max_step'] = sample.get('max_step', -1)
    else:
        features['has_critique'] = False
        features['critique_length'] = 0
        features['conclusion'] = ''
        features['max_step'] = -1
    
    return features


def display_sample_summary(sample, stage_name):
    """显示样本摘要信息"""
    features = analyze_sample(sample)
    
    print(f"\n{'='*80}")
    print(f"📊 {stage_name.upper()} 阶段样本分析")
    print(f"{'='*80}")
    
    print(f"\n📋 基本信息:")
    print(f"  样本ID: {features['id']}")
    print(f"  陈述: {features['statement'][:100]}..." if len(features['statement']) > 100 else f"  陈述: {features['statement']}")
    print(f"  表格标题: {features['table_caption']}")
    print(f"  真实标签: {features['label']} ({'✓ 正确' if features['label'] == 1 else '✗ 错误'})")
    print(f"  表格维度: {features['table_rows']} 行 × {features['table_cols']} 列")
    
    print(f"\n🔗 推理链:")
    print(f"  链长度: {features['chain_length']} 步")
    if features['chain_operations']:
        print(f"  操作序列: {' -> '.join(features['chain_operations'][:5])}")
        if len(features['chain_operations']) > 5:
            print(f"              ... (共 {len(features['chain_operations'])} 个操作)")
    
    # 显示详细操作链
    if 'chain' in sample and sample['chain']:
        print(f"\n  详细步骤:")
        for i, op in enumerate(sample['chain']):
            op_name = op.get('operation_name', 'Unknown')
            thought = op.get('thought', '')
            params = op.get('parameter_and_conf', [])
            
            print(f"    Step {i+1}: {op_name}")
            if thought:
                print(f"      思考: {thought[:80]}..." if len(thought) > 80 else f"      思考: {thought}")
            if params:
                param, conf = params[0] if params else ('', 0)
                print(f"      参数: {param}")
                print(f"      置信度: {conf:.4f}")
    
    if features['has_critique']:
        print(f"\n🎯 Critic分析结果:")
        print(f"  最大步骤: {features['max_step']}")
        print(f"  批评长度: {features['critique_length']} 字符")
        print(f"  结论: {features['conclusion']}")
        print(f"  批评内容: {sample.get('critique', '')[:200]}..." if len(sample.get('critique', '')) > 200 else f"  批评内容: {sample.get('critique', '')}")
    
    # 显示表格
    print(f"\n📄 表格内容:")
    print(table2string(sample.get('table_text', [])))
    print(f"{'='*80}\n")


def analyze_directory(directory, stage_name, max_samples=3):
    """分析目录中的所有样本"""
    print(f"\n\n{'#'*80}")
    print(f"# 📁 {stage_name.upper()} 阶段结果目录: {directory}")
    print(f"{'#'*80}\n")
    
    pkl_files = load_pkl_files(directory)
    
    if not pkl_files:
        print(f"⚠️  目录中没有找到pkl文件")
        return
    
    print(f"📦 找到 {len(pkl_files)} 个pkl文件\n")
    
    # 统计信息
    stats = {
        'total_samples': len(pkl_files),
        'has_chain': 0,
        'has_critique': 0,
        'avg_chain_length': 0,
        'correct_predictions': 0,
        'total_predictions': 0,
        'operation_types': defaultdict(int),
        'label_distribution': {0: 0, 1: 0}
    }
    
    # 加载并分析每个样本
    samples = []
    for pkl_file in pkl_files[:max_samples]:
        try:
            with open(pkl_file, 'rb') as f:
                data = pickle.load(f)
                # 处理thought阶段的tuple结构
                if isinstance(data, tuple) and len(data) >= 1:
                    sample = data[0] if isinstance(data[0], dict) else data
                else:
                    sample = data
                samples.append(sample)
                
                # 统计
                features = analyze_sample(sample)
                
                if features['chain_length'] > 0:
                    stats['has_chain'] += 1
                    stats['avg_chain_length'] += features['chain_length']
                    
                    # 统计操作类型
                    for op in features['chain_operations']:
                        stats['operation_types'][op] += 1
                
                if features['has_critique']:
                    stats['has_critique'] += 1
                
                # 统计标签分布
                stats['label_distribution'][features['label']] += 1
                
                # 统计预测正确性
                if 'chain' in sample and sample['chain']:
                    last_op = sample['chain'][-1]
                    if 'parameter_and_conf' in last_op:
                        prediction = last_op['parameter_and_conf'][0][0].lower()
                        label = sample.get('label', -1)
                        if (prediction == 'yes' and label == 1) or (prediction == 'no' and label == 0):
                            stats['correct_predictions'] += 1
                        stats['total_predictions'] += 1
                        
        except Exception as e:
            print(f"❌ 加载文件 {pkl_file} 时出错: {e}")
    
    # 计算平均值
    if stats['has_chain'] > 0:
        stats['avg_chain_length'] = stats['avg_chain_length'] / stats['has_chain']
    
    accuracy = stats['correct_predictions'] / stats['total_predictions'] if stats['total_predictions'] > 0 else 0
    
    # 显示统计信息
    print(f"📈 统计信息 (前 {min(max_samples, len(samples))} 个样本):")
    print(f"  总样本数: {stats['total_samples']}")
    print(f"  有推理链: {stats['has_chain']}")
    print(f"  有Critic分析: {stats['has_critique']}")
    print(f"  平均链长度: {stats['avg_chain_length']:.2f} 步")
    print(f"  预测准确率: {accuracy:.2%}")
    print(f"\n  标签分布:")
    print(f"    正确 (label=1): {stats['label_distribution'][1]}")
    print(f"    错误 (label=0): {stats['label_distribution'][0]}")
    
    print(f"\n  操作类型分布:")
    for op_type, count in sorted(stats['operation_types'].items(), key=lambda x: -x[1]):
        print(f"    {op_type}: {count}")
    
    # 显示详细样本
    print(f"\n{'='*80}")
    print(f"📝 详细样本展示 (前 {min(max_samples, len(samples))} 个)")
    print(f"{'='*80}")
    
    for i, sample in enumerate(samples):
        display_sample_summary(sample, f"{stage_name} 样本 {i+1}")
        print()


def compare_stages():
    """比较三个阶段的结果"""
    print(f"\n\n{'█'*80}")
    print(f"🔄 三个阶段对比分析")
    print(f"{'█'*80}\n")
    
    stages = [
        {
            'name': 'Thought',
            'directory': 'results/thought/tabfact/cache',
            'desc': '初始推理阶段 - 生成推理链'
        },
        {
            'name': 'Critic',
            'directory': 'results/critic/tabfact/cache',
            'desc': '批评分析阶段 - 识别推理错误'
        },
        {
            'name': 'Refine',
            'directory': 'results/refine/tabfact/cache',
            'desc': '改进优化阶段 - 修正推理链'
        }
    ]
    
    # 收集各阶段数据
    stage_data = {}
    for stage in stages:
        if os.path.exists(stage['directory']):
            pkl_files = load_pkl_files(stage['directory'])
            stage_data[stage['name']] = {
                'file_count': len(pkl_files),
                'directory': stage['directory'],
                'desc': stage['desc']
            }
        else:
            stage_data[stage['name']] = {
                'file_count': 0,
                'directory': stage['directory'],
                'desc': stage['desc'],
                'missing': True
            }
    
    # 显示对比表
    print(f"\n{'='*80}")
    print(f"阶段对比:")
    print(f"{'='*80}\n")
    
    print(f"{'阶段':<20} {'文件数':<15} {'目录':<40} {'描述':<30}")
    print(f"{'-'*80}")
    
    for stage in stages:
        name = stage['name']
        data = stage_data.get(name, {})
        file_count = data.get('file_count', 0)
        directory = data.get('directory', 'N/A')
        desc = data.get('desc', 'N/A')
        missing = data.get('missing', False)
        
        status = "❌ 不存在" if missing else f"✓ {file_count} 个文件"
        
        print(f"{name:<20} {file_count:<15} {directory:<40} {desc:<30}")
        if missing:
            print(f"{' '*20} {status}")
        else:
            print(f"{' '*20} {status}")
    
    print(f"{'-'*80}\n")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🎯 Table-Critic 结果可视化工具")
    print("="*80)
    print("\n本工具用于可视化三个阶段（Thought、Critic、Refine）的数据特征\n")
    
    # 比较三个阶段
    compare_stages()
    
    # 分析每个阶段（显示前2个样本）
    stages = [
        ('Thought', 'results/thought/tabfact/qwen3:32b/cache'),
        ('Critic', 'results/critic/tabfact/qwen3:32b/cache'),
        ('Refine', 'results/refine/tabfact/qwen3:32b/cache')
    ]
    
    for stage_name, directory in stages:
        if os.path.exists(directory):
            analyze_directory(directory, stage_name, max_samples=2)
        else:
            print(f"\n⚠️  目录不存在: {directory}")
    
    print(f"\n{'='*80}")
    print("✅ 分析完成！")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
