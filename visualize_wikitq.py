#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WikiTableQuestions 结果对比可视化脚本
专门用于对比 Thought 和 Refine 两个阶段的结果
"""

import os
import pickle
import glob
from collections import defaultdict
import sys

# 添加评估模块路径
sys.path.append('thought/TableQA')
from utils.evaluate import wikitq_match_func_for_samples


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
        sample = sample[0] if isinstance(sample[0], dict) else sample
    
    # 提取所有可能的ID字段
    ids = sample.get('ids', sample.get('id', 'N/A'))
    
    features = {
        'id': sample.get('id', 'N/A'),
        'ids': ids,  # WikiTableQuestions 使用 'ids'
        'statement': sample.get('statement', ''),
        'table_caption': sample.get('table_caption', ''),
        'table_rows': len(sample.get('table_text', [])) if sample.get('table_text') else 0,
        'table_cols': len(sample.get('table_text', [])[0]) if sample.get('table_text') else 0,
    }
    
    # 分析操作链
    chain = sample.get('chain', [])
    features['chain_length'] = len(chain)
    features['chain_operations'] = [op.get('operation_name', 'Unknown') for op in chain]
    
    # 获取预测答案
    if chain and 'parameter_and_conf' in chain[-1]:
        features['predicted_answer'] = chain[-1]['parameter_and_conf'][0][0]
        features['confidence'] = chain[-1]['parameter_and_conf'][0][1]
    else:
        features['predicted_answer'] = ''
        features['confidence'] = 0
    
    # 分析Critic结果（Refine阶段特有）
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
    
    # 分析Judge结果（Refine阶段特有）
    if 'judge' in sample:
        features['has_judge'] = True
        features['judge'] = sample.get('judge', '')
    else:
        features['has_judge'] = False
        features['judge'] = ''
    
    # 分析Tree结果（Refine阶段特有）
    if 'tree' in sample:
        features['has_tree'] = True
        features['tree'] = sample.get('tree', '')
    else:
        features['has_tree'] = False
        features['tree'] = ''
    
    return features


def display_sample_summary(sample, stage_name):
    """显示样本摘要信息"""
    features = analyze_sample(sample)
    
    print(f"\n{'='*80}")
    print(f"📊 {stage_name.upper()} 阶段样本分析")
    print(f"{'='*80}")
    
    print(f"\n📋 基本信息:")
    print(f"  样本ID: {features['id']}")
    print(f"  样本IDs: {features['ids']}")
    print(f"  陈述: {features['statement'][:100]}..." if len(features['statement']) > 100 else f"  陈述: {features['statement']}")
    print(f"  表格标题: {features['table_caption']}")
    print(f"  表格维度: {features['table_rows']} 行 × {features['table_cols']} 列")
    
    # 显示预测答案
    if features['predicted_answer']:
        print(f"  预测答案: {features['predicted_answer']}")
        print(f"  置信度: {features['confidence']:.4f}")
    
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
    
    if features['has_judge']:
        print(f"\n⚖️  Judge分析结果:")
        print(f"  判断: {features['judge']}")
    
    if features['has_tree']:
        print(f"\n🌳 Tree分析结果:")
        print(f"  错误路由: {features['tree']}")
    
    # 显示表格
    print(f"\n📄 表格内容:")
    print(table2string(sample.get('table_text', [])))
    print(f"{'='*80}\n")


def load_samples_from_directory(directory, stage_name):
    """从目录加载所有样本"""
    print(f"\n{'#'*80}")
    print(f"# 📁 {stage_name.upper()} 阶段结果目录: {directory}")
    print(f"{'#'*80}\n")
    
    if not os.path.exists(directory):
        print(f"⚠️  目录不存在: {directory}")
        return None
    
    pkl_files = load_pkl_files(directory)
    
    if not pkl_files:
        print(f"⚠️  目录中没有找到pkl文件")
        return None
    
    print(f"📦 找到 {len(pkl_files)} 个pkl文件\n")
    
    # 加载并分析每个样本
    samples = []
    
    # 检查是否有final_result.pkl文件（包含所有样本）
    final_result_file = os.path.join(os.path.dirname(directory), 'final_result.pkl')
    
    if os.path.exists(final_result_file):
        print(f"📄 检测到 final_result.pkl 文件，从中加载所有样本\n")
        try:
            with open(final_result_file, 'rb') as f:
                data = pickle.load(f)
                # 处理list of samples
                if isinstance(data, list):
                    for sample in data:
                        if isinstance(sample, dict):
                            samples.append(sample)
                # 处理单个sample
                elif isinstance(data, dict):
                    samples.append(data)
                # 处理tuple
                elif isinstance(data, tuple) and len(data) >= 1:
                    sample = data[0] if isinstance(data[0], dict) else data
                    samples.append(sample)
        except Exception as e:
            print(f"❌ 加载 final_result.pkl 时出错: {e}")
            return None
    else:
        # 从cache目录逐个加载
        for pkl_file in pkl_files[:]:
            try:
                with open(pkl_file, 'rb') as f:
                    data = pickle.load(f)
                    # 处理dict结构
                    if isinstance(data, dict):
                        sample = data
                        samples.append(sample)
                    # 处理tuple结构
                    elif isinstance(data, tuple) and len(data) >= 1:
                        sample = data[0] if isinstance(data[0], dict) else data
                        samples.append(sample)
                    # 处理list结构
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                samples.append(item)
            except Exception as e:
                print(f"❌ 加载文件 {pkl_file} 时出错: {e}")
    
    if not samples:
        print(f"⚠️  没有加载到任何样本")
        return None
    
    print(f"✅ 成功加载 {len(samples)} 个样本\n")
    return samples


def analyze_samples(samples, stage_name):
    """分析样本并返回统计信息"""
    if not samples:
        return None
    
    stats = {
        'total_samples': len(samples),
        'has_chain': 0,
        'has_critique': 0,
        'has_judge': 0,
        'has_tree': 0,
        'avg_chain_length': 0,
        'operation_types': defaultdict(int),
        'answer_length_distribution': defaultdict(int),
    }
    
    # 统计所有样本
    for sample in samples:
        # 处理sample可能是dict或tuple的情况
        if isinstance(sample, tuple) and len(sample) >= 1:
            sample = sample[0] if isinstance(sample[0], dict) else sample
        
        # 分析操作链
        chain = sample.get('chain', [])
        chain_length = len(chain)
        
        if chain_length > 0:
            stats['has_chain'] += 1
            stats['avg_chain_length'] += chain_length
            
            # 统计操作类型
            for op in chain:
                op_name = op.get('operation_name', 'Unknown')
                stats['operation_types'][op_name] += 1
        
        # 统计Critic结果（Refine阶段特有）
        if 'critique' in sample:
            stats['has_critique'] += 1
        
        # 统计Judge结果（Refine阶段特有）
        if 'judge' in sample:
            stats['has_judge'] += 1
        
        # 统计Tree结果（Refine阶段特有）
        if 'tree' in sample:
            stats['has_tree'] += 1
        
        # 统计答案长度分布
        if chain and 'parameter_and_conf' in chain[-1]:
            predicted_answer = chain[-1]['parameter_and_conf'][0][0]
            answer_length = len(predicted_answer)
            if answer_length <= 10:
                stats['answer_length_distribution']['1-10'] += 1
            elif answer_length <= 50:
                stats['answer_length_distribution']['11-50'] += 1
            elif answer_length <= 100:
                stats['answer_length_distribution']['51-100'] += 1
            else:
                stats['answer_length_distribution']['100+'] += 1
    
    # 计算平均值
    if stats['has_chain'] > 0:
        stats['avg_chain_length'] = stats['avg_chain_length'] / stats['has_chain']
    
    return stats


def calculate_accuracy(samples, strategy="top", tagged_dataset_path='thought/TableQA/data/wikitq/tagged_data'):
    """使用evaluate.py中的函数计算准确率"""
    try:
        accuracy = wikitq_match_func_for_samples(samples, strategy, tagged_dataset_path)
        return accuracy
    except Exception as e:
        print(f"⚠️  计算准确率时出错: {e}")
        return 0.0


def display_stats(stats, stage_name, accuracy=None):
    """显示统计信息"""
    if not stats:
        return
    
    print(f"📈 统计信息 (基于 {stats['total_samples']} 个样本):")
    print(f"  已分析样本数: {stats['total_samples']}")
    print(f"  有推理链: {stats['has_chain']}")
    print(f"  有Critic分析: {stats['has_critique']}")
    print(f"  有Judge分析: {stats['has_judge']}")
    print(f"  有Tree分析: {stats['has_tree']}")
    print(f"  平均链长度: {stats['avg_chain_length']:.2f} 步")
    
    if accuracy is not None:
        print(f"  预测准确率: {accuracy:.4f}")
    else:
        print(f"  ⚠️  未加载标签数据或样本ID不匹配，无法计算准确率")
    
    print(f"\n  答案长度分布:")
    for length_range, count in sorted(stats['answer_length_distribution'].items()):
        percentage = count / stats['total_samples'] * 100 if stats['total_samples'] > 0 else 0
        print(f"    {length_range} 字符: {count} ({percentage:.1f}%)")
    
    print(f"\n  操作类型分布:")
    for op_type, count in sorted(stats['operation_types'].items(), key=lambda x: -x[1]):
        print(f"    {op_type}: {count}")


def compare_stages(stages):
    """比较两个阶段的结果"""
    print(f"\n\n{'█'*80}")
    print(f"🔄 两个阶段对比分析")
    print(f"{'█'*80}\n")
    
    # 收集各阶段数据
    stage_data = {}
    for stage in stages:
        if os.path.exists(stage['directory']):
            pkl_files = load_pkl_files(stage['directory'])
            # 检查是否有final_result.pkl
            final_result_file = os.path.join(os.path.dirname(stage['directory']), 'final_result.pkl')
            sample_count = 0
            
            if os.path.exists(final_result_file):
                try:
                    with open(final_result_file, 'rb') as f:
                        data = pickle.load(f)
                        if isinstance(data, list):
                            sample_count = len(data)
                        elif isinstance(data, dict):
                            sample_count = 1
                except:
                    pass
            elif pkl_files:
                # 如果没有final_result.pkl，统计cache中的文件数
                sample_count = len(pkl_files)
            
            stage_data[stage['name']] = {
                'file_count': len(pkl_files),
                'sample_count': sample_count,
                'directory': stage['directory'],
                'desc': stage['desc'],
                'has_final_result': os.path.exists(final_result_file)
            }
        else:
            stage_data[stage['name']] = {
                'file_count': 0,
                'sample_count': 0,
                'directory': stage['directory'],
                'desc': stage['desc'],
                'missing': True,
                'has_final_result': False
            }
    
    # 显示对比表
    print(f"\n{'='*80}")
    print(f"阶段对比:")
    print(f"{'='*80}\n")
    
    print(f"{'阶段':<20} {'样本数':<15} {'Cache文件数':<15} {'目录':<35}")
    print(f"{'-'*80}")
    
    for stage in stages:
        name = stage['name']
        data = stage_data.get(name, {})
        sample_count = data.get('sample_count', 0)
        file_count = data.get('file_count', 0)
        directory = data.get('directory', 'N/A')
        desc = data.get('desc', 'N/A')
        missing = data.get('missing', False)
        has_final_result = data.get('has_final_result', False)
        
        if missing:
            print(f"{name:<20} {'❌ 不存在':<15} {'❌ 不存在':<15} {directory:<35}")
        else:
            source = "final_result.pkl" if has_final_result else "cache目录"
            print(f"{name:<20} {sample_count:<15} {file_count:<15} {directory:<35}")
            print(f"{' '*20} 来源: {source}")
    
    print(f"{'-'*80}\n")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🎯 WikiTableQuestions 结果对比可视化工具")
    print("="*80)
    print("\n本工具用于对比 Thought 和 Refine 两个阶段的结果\n")
    
    # 设置路径
    thought_path = '/home/ubuntu/mnt/lx/Table-Critic/results/thought/wikitq/qwen3:32b/cache'
    refine_path = '/home/ubuntu/mnt/lx/Table-Critic/results/refine/wikitq/qwen3:32b/cache'
    tagged_data_path = 'thought/TableQA/data/wikitq/tagged_data'

    stages = [
        {
            'name': 'Thought',
            'directory': thought_path,
            'desc': '初始推理阶段 - 生成推理链'
        },
        {
            'name': 'Refine',
            'directory': refine_path,
            'desc': '改进优化阶段 - 修正推理链'
        }
    ]
    
    # 比较两个阶段
    compare_stages(stages)
    
    # 加载并分析每个阶段
    results = {}
    for stage in stages:
        stage_name = stage['name']
        directory = stage['directory']
        
        samples = load_samples_from_directory(directory, stage_name)
        
        if samples:
            stats = analyze_samples(samples, stage_name)
            # display_stats(stats, stage_name)
            
            # 计算准确率
            print(f"\n📊 计算准确率...")
            accuracy = calculate_accuracy(samples, strategy="top", tagged_dataset_path=tagged_data_path)
            
            # 重新显示包含准确率的统计信息
            print(f"\n{'='*80}")
            display_stats(stats, stage_name, accuracy)
            
            results[stage_name] = {
                'accuracy': accuracy,
                'correct': int(accuracy * len(samples)),
                'total': len(samples),
                'stats': stats
            }
        else:
            print(f"\n⚠️  目录不存在或分析失败: {directory}")
    
    # 显示准确率对比
    if 'Thought' in results and 'Refine' in results:
        print(f"\n\n{'█'*80}")
        print(f"📊 准确率对比")
        print(f"{'█'*80}\n")
        
        print(f"{'阶段':<20} {'准确率':<15} {'正确数':<15} {'总数':<15}")
        print(f"{'-'*80}")
        
        for stage_name in ['Thought', 'Refine']:
            if stage_name in results:
                r = results[stage_name]
                print(f"{stage_name:<20} {r['accuracy']:.4f}        {r['correct']:<15} {r['total']:<15}")
        
        print(f"{'-'*80}\n")
        
        # 显示前2个样本的详细信息
        print(f"\n{'█'*80}")
        print(f"📝 详细样本展示 (前2个)")
        print(f"{'█'*80}\n")
        
        for stage in stages:
            stage_name = stage['name']
            directory = stage['directory']
            
            samples = load_samples_from_directory(directory, stage_name)
            
            if samples:
                # 显示前2个样本
                for i in range(min(2, len(samples))):
                    display_sample_summary(samples[i], f"{stage_name} 样本 {i+1}")
            else:
                print(f"\n⚠️  无法加载样本: {directory}")
        
        # 计算准确率提升
        thought_acc = results['Thought']['accuracy']
        refine_acc = results['Refine']['accuracy']
        improvement = refine_acc - thought_acc
        improvement_pct = (improvement / thought_acc * 100) if thought_acc > 0 else 0
        
        print(f"📈 准确率提升:")
        print(f"  Thought: {thought_acc:.4f}")
        print(f"  Refine:  {refine_acc:.4f}")
        print(f"  提升:    {improvement:+.4f} ({improvement_pct:+.2f}%)\n")
        
        # 显示操作类型对比
        print(f"\n{'█'*80}")
        print(f"📊 操作类型对比")
        print(f"{'█'*80}\n")
        
        thought_ops = results['Thought']['stats']['operation_types']
        refine_ops = results['Refine']['stats']['operation_types']
        
        all_ops = set(thought_ops.keys()) | set(refine_ops.keys())
        
        print(f"{'操作类型':<30} {'Thought':<15} {'Refine':<15} {'变化':<15}")
        print(f"{'-'*80}")
        
        for op_type in sorted(all_ops):
            thought_count = thought_ops.get(op_type, 0)
            refine_count = refine_ops.get(op_type, 0)
            change = refine_count - thought_count
            change_str = f"{change:+d}" if change != 0 else "0"
            
            print(f"{op_type:<30} {thought_count:<15} {refine_count:<15} {change_str:<15}")
        
        print(f"{'-'*80}\n")
        
        # 显示推理链长度对比
        print(f"\n{'█'*80}")
        print(f"📊 推理链长度对比")
        print(f"{'█'*80}\n")
        
        thought_avg_len = results['Thought']['stats']['avg_chain_length']
        refine_avg_len = results['Refine']['stats']['avg_chain_length']
        len_change = refine_avg_len - thought_avg_len
        
        print(f"{'阶段':<20} {'平均链长度':<20} {'变化':<20}")
        print(f"{'-'*80}")
        print(f"{'Thought':<20} {thought_avg_len:.2f} {'':<20}")
        print(f"{'Refine':<20} {refine_avg_len:.2f} {len_change:+.2f}")
        print(f"{'-'*80}\n")
    
    print(f"{'='*80}")
    print("✅ 分析完成！")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
