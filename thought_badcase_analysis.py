#!/usr/bin/env python3
"""Thought 阶段 Bad Case 综合分析脚本
横向对比多个模型在 WikiTQ 和 TabFact 上的错误模式
"""

import pickle, os, re, sys, json
import unicodedata
from math import isnan, isinf
from abc import ABCMeta, abstractmethod
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).parent

# ==================== WikiTQ 评估函数 ====================

def normalize(x):
    if not isinstance(x, str):
        x = x.decode('utf8', errors='ignore')
    x = ''.join(c for c in unicodedata.normalize('NFKD', x)
                if unicodedata.category(c) != 'Mn')
    x = re.sub(r"[''`]", "'", x)
    x = re.sub(r'[""]', '"', x)
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
    __metaclass__ = ABCMeta
    _normalized = None
    @abstractmethod
    def match(self, other): pass
    @property
    def normalized(self): return self._normalized

class StringValue(Value):
    def __init__(self, content):
        assert isinstance(content, str)
        self._normalized = normalize(content)
        self._hash = hash(self._normalized)
    def __eq__(self, other):
        return isinstance(other, StringValue) and self.normalized == other.normalized
    def __hash__(self): return self._hash
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
        self._normalized = str(self._amount) if not original_string else normalize(original_string)
        self._hash = hash(self._amount)
    @property
    def amount(self): return self._amount
    def __eq__(self, other):
        return isinstance(other, NumberValue) and self.amount == other.amount
    def __hash__(self): return self._hash
    def match(self, other):
        assert isinstance(other, Value)
        if self.normalized == other.normalized: return True
        if isinstance(other, NumberValue):
            return abs(self.amount - other.amount) < 1e-6
        return False
    @staticmethod
    def parse(text):
        try: return int(text)
        except:
            try:
                amount = float(text)
                assert not isnan(amount) and not isinf(amount)
                return amount
            except: return None

class DateValue(Value):
    def __init__(self, year, month, day, original_string=None):
        self._year, self._month, self._day = year, month, day
        if not original_string:
            self._normalized = '{}-{}-{}'.format(
                year if year != -1 else 'xx', month if month != -1 else 'xx',
                day if day != '-1' else 'xx')
        else:
            self._normalized = normalize(original_string)
        self._hash = hash((self._year, self._month, self._day))
    @property
    def ymd(self): return (self._year, self._month, self._day)
    def __eq__(self, other): return isinstance(other, DateValue) and self.ymd == other.ymd
    def __hash__(self): return self._hash
    def match(self, other):
        assert isinstance(other, Value)
        if self.normalized == other.normalized: return True
        if isinstance(other, DateValue): return self.ymd == other.ymd
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
    if isinstance(original_string, Value): return original_string
    if not corenlp_value: corenlp_value = original_string
    amount = NumberValue.parse(corenlp_value)
    if amount is not None: return NumberValue(amount, original_string)
    ymd = DateValue.parse(corenlp_value)
    if ymd is not None:
        if ymd[1] == ymd[2] == -1: return NumberValue(ymd[0], original_string)
        else: return DateValue(ymd[0], ymd[1], ymd[2], original_string)
    return StringValue(original_string)

def to_value_list(original_strings, corenlp_values=None):
    assert isinstance(original_strings, (list, tuple, set))
    if corenlp_values is not None:
        return list(set(to_value(x, y) for (x, y) in zip(original_strings, corenlp_values)))
    return list(set(to_value(x) for x in original_strings))

def check_denotation(target_values, predicted_values):
    if len(target_values) != len(predicted_values): return False
    for target in target_values:
        if not any(target.match(pred) for pred in predicted_values): return False
    return True

def tsv_unescape(x):
    return x.replace(r'\n', '\n').replace(r'\p', '|').replace('\\\\', '\\')
def tsv_unescape_list(x):
    return [tsv_unescape(y) for y in x.split('|')]

def load_target_values_map(tagged_data_path):
    target_values_map = {}
    for basename in os.listdir(tagged_data_path):
        if basename[0] == '.': continue
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

def wikitq_eval(sample, target_values):
    results = sample["chain"][-1]["parameter_and_conf"]
    res = results[0][0]
    pred_answer = [res.lower()] if '|' not in res else [r for r in res.lower().split('|')]
    pred_answer = to_value_list(pred_answer)
    return check_denotation(target_values, pred_answer)

def tabfact_eval(sample):
    results = sample["chain"][-1]["parameter_and_conf"]
    res = results[0][0].lower()
    if res == "true": res = "yes"
    if res == "false": res = "no"
    if res == "yes" and sample["label"] == 1: return True
    if res == "no" and sample["label"] == 0: return True
    return False

# ==================== 错误分类 ====================

def classify_wikitq_error(gold_raw, pred_raw):
    """更精细的 WikiTQ 错误分类"""
    gold = str(gold_raw).strip().lower()
    pred = str(pred_raw).strip().lower()

    # 空值
    if not pred and not gold: return "其他"
    if not gold and pred: return "误判为有值"
    if gold and not pred: return "误判为空值"

    # 数值比较
    try:
        g_num = float(gold)
        p_num = float(pred)
        if g_num == p_num: return "数值格式差异"  # same number, diff format
        return "数值错误"
    except: pass

    # 布尔
    if gold in ('true','false','yes','no') and pred in ('true','false','yes','no'):
        return "布尔判断错误"

    # 字符串匹配度
    if gold == pred: return "大小写/格式差异"
    if gold in pred or pred in gold: return "部分匹配"
    # edit distance
    if len(gold) > 2 and len(pred) > 2:
        common = sum(1 for c in gold if c in pred)
        ratio = common / max(len(gold), len(pred))
        if ratio > 0.6: return "近似匹配(拼写差异)"
    return "完全不匹配"

def classify_tabfact_error(sample):
    """TabFact 错误分类"""
    results = sample["chain"][-1]["parameter_and_conf"]
    pred = results[0][0].lower()
    if pred == "true": pred = "yes"
    if pred == "false": pred = "no"
    gold = "yes" if sample["label"] == 1 else "no"

    if pred not in ("yes", "no"):
        return f"格式异常(pred={pred[:20]})"

    if gold == "yes" and pred == "no":
        return "漏判(应为yes判为no)"
    elif gold == "no" and pred == "yes":
        return "误判(应为no判为yes)"
    return "其他"

def extract_chain_pattern(chain):
    """提取推理链模式"""
    ops = []
    for step in chain:
        op = step.get('operation_name', 'unknown')
        if op == 'simple_query':
            ops.append('query')
        else:
            ops.append(op.replace('select_', 'sel_').replace('group_', 'grp_').replace('sort_', 'sort_').replace('add_', 'add_'))
    return ' -> '.join(ops)

def get_chain_length(chain):
    return len([s for s in chain if s.get('operation_name')])

# ==================== 主分析 ====================

def analyze_wikitq(model_results, target_values_map):
    """分析 WikiTQ bad cases"""
    total, correct = 0, 0
    bad_cases = []
    error_types = Counter()
    chain_pattern_errors = defaultdict(int)
    chain_pattern_totals = Counter()

    for sample in model_results:
        if sample is None: continue
        sid = sample.get('ids', sample.get('id', ''))
        if sid not in target_values_map: continue

        total += 1
        chain = sample.get('chain', [])
        pattern = extract_chain_pattern(chain)
        chain_pattern_totals[pattern] += 1

        if wikitq_eval(sample, target_values_map[sid]):
            correct += 1
        else:
            # Extract gold from tagged data
            gold_vals = target_values_map[sid]
            gold_str = '|'.join(str(v._normalized) for v in gold_vals)

            # Extract pred
            results = chain[-1]["parameter_and_conf"]
            pred_str = results[0][0]

            etype = classify_wikitq_error(gold_str, pred_str)
            error_types[etype] += 1
            chain_pattern_errors[pattern] += 1

            bad_cases.append({
                'id': sid,
                'question': sample.get('statement', ''),
                'gold': gold_str,
                'pred': pred_str,
                'error_type': etype,
                'chain_pattern': pattern,
                'chain_length': get_chain_length(chain),
            })

    acc = correct / total if total > 0 else 0
    return {
        'total': total, 'correct': correct, 'accuracy': acc,
        'bad_cases': bad_cases, 'error_types': dict(error_types),
        'chain_pattern_errors': dict(chain_pattern_errors),
        'chain_pattern_totals': dict(chain_pattern_totals),
    }

def analyze_tabfact(model_results):
    """分析 TabFact bad cases"""
    total, correct = 0, 0
    bad_cases = []
    error_types = Counter()
    chain_pattern_errors = defaultdict(int)
    chain_pattern_totals = Counter()

    for sample in model_results:
        if sample is None: continue
        total += 1
        chain = sample.get('chain', [])
        pattern = extract_chain_pattern(chain)
        chain_pattern_totals[pattern] += 1

        if tabfact_eval(sample):
            correct += 1
        else:
            results = chain[-1]["parameter_and_conf"]
            pred_str = results[0][0]
            gold_label = sample.get('label', -1)

            etype = classify_tabfact_error(sample)
            error_types[etype] += 1
            chain_pattern_errors[pattern] += 1

            bad_cases.append({
                'id': sample.get('id', sample.get('table_id', '')),
                'statement': sample.get('statement', ''),
                'gold': "yes" if gold_label == 1 else "no",
                'pred': pred_str,
                'error_type': etype,
                'chain_pattern': pattern,
                'chain_length': get_chain_length(chain),
            })

    acc = correct / total if total > 0 else 0
    return {
        'total': total, 'correct': correct, 'accuracy': acc,
        'bad_cases': bad_cases, 'error_types': dict(error_types),
        'chain_pattern_errors': dict(chain_pattern_errors),
        'chain_pattern_totals': dict(chain_pattern_totals),
    }

def load_pkl(path):
    with open(path, 'rb') as f:
        return pickle.load(f)

# ==================== 报告生成 ====================

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def format_pct(n, total):
    return f"{n}/{total} ({n/total*100:.1f}%)" if total > 0 else "N/A"

def report_wikitq(all_results):
    print_section("WikiTQ Thought 阶段 Bad Case 分析（多模型横向对比）")

    # Accuracy overview
    print("## 1. 准确率概览\n")
    print(f"{'模型':<25} {'准确率':>10} {'正确/总数':>15} {'错误数':>8}")
    print("-" * 60)
    for model, r in sorted(all_results.items(), key=lambda x: x[1]['accuracy'], reverse=True):
        print(f"{model:<25} {r['accuracy']*100:>9.1f}% {r['correct']:>8}/{r['total']:<8} {len(r['bad_cases']):>8}")

    # Error type comparison
    print("\n## 2. 错误类型分布对比\n")
    all_types = set()
    for r in all_results.values():
        all_types.update(r['error_types'].keys())
    all_types = sorted(all_types)

    header = f"{'错误类型':<20}"
    for model in all_results:
        header += f" {model:>12}"
    print(header)
    print("-" * (20 + 13 * len(all_results)))

    for etype in all_types:
        row = f"{etype:<20}"
        for model, r in all_results.items():
            n = r['error_types'].get(etype, 0)
            total_bad = len(r['bad_cases'])
            pct = f"{n}({n/total_bad*100:.0f}%)" if total_bad > 0 else "0"
            row += f" {pct:>12}"
        print(row)

    # Chain pattern error rates
    print("\n## 3. 推理链模式的错误率（Top 10 高错误率模式）\n")
    # Collect all patterns
    pattern_stats = defaultdict(lambda: {'total': 0, 'errors': defaultdict(int)})
    for model, r in all_results.items():
        for pat, total in r['chain_pattern_totals'].items():
            pattern_stats[pat]['total'] += total
            pattern_stats[pat]['errors'][model] = r['chain_pattern_errors'].get(pat, 0)

    # Sort by total error count
    sorted_patterns = sorted(pattern_stats.items(), key=lambda x: sum(x[1]['errors'].values()), reverse=True)[:15]

    print(f"{'推理链模式':<40} {'总样本':>8}", end="")
    for model in all_results:
        print(f" {model[:8]:>10}", end="")
    print()
    print("-" * (40 + 8 + 10 * len(all_results)))

    for pat, stats in sorted_patterns:
        total = stats['total']
        row = f"{pat:<40} {total:>8}"
        for model in all_results:
            err = stats['errors'].get(model, 0)
            # Get total for this model+pattern
            model_total = all_results[model]['chain_pattern_totals'].get(pat, 0)
            rate = f"{err}/{model_total}" if model_total > 0 else "-"
            row += f" {rate:>10}"
        print(row)

    # Cross-model bad case overlap
    print("\n## 4. 模型间 Bad Case 重叠分析\n")
    model_ids = {}
    for model, r in all_results.items():
        model_ids[model] = set(bc['id'] for bc in r['bad_cases'])

    models_list = sorted(all_results.keys())
    for i, m1 in enumerate(models_list):
        for m2 in models_list[i+1:]:
            common = model_ids[m1] & model_ids[m2]
            only_m1 = model_ids[m1] - model_ids[m2]
            only_m2 = model_ids[m2] - model_ids[m1]
            print(f"  {m1} vs {m2}:")
            print(f"    共同错误: {len(common)}, 仅{m1}错: {len(only_m1)}, 仅{m2}错: {len(only_m2)}")

    # Universal hard cases (all models wrong)
    if len(models_list) >= 2:
        universal = model_ids[models_list[0]]
        for m in models_list[1:]:
            universal &= model_ids[m]
        print(f"\n  所有模型都错的样本数: {len(universal)}")
        if universal:
            print(f"  占总样本比例: {len(universal)/all_results[models_list[0]]['total']*100:.1f}%")

    # Representative bad cases
    print("\n## 5. 典型 Bad Case 示例\n")
    # Pick the best and worst model
    best_model = max(all_results.items(), key=lambda x: x[1]['accuracy'])[0]
    worst_model = min(all_results.items(), key=lambda x: x[1]['accuracy'])[0]

    for label, model in [("最佳模型: " + best_model, best_model), ("最弱模型: " + worst_model, worst_model)]:
        bcs = all_results[model]['bad_cases']
        print(f"\n### {label} ({len(bcs)} 个错误)\n")
        # Show one example per error type
        shown_types = set()
        for bc in bcs:
            if bc['error_type'] not in shown_types:
                shown_types.add(bc['error_type'])
                q = bc['question'][:100] + "..." if len(bc['question']) > 100 else bc['question']
                print(f"  [{bc['error_type']}] ID={bc['id']}")
                print(f"    问题: {q}")
                print(f"    Gold: {bc['gold']}")
                print(f"    Pred: {bc['pred']}")
                print(f"    Chain: {bc['chain_pattern']}")
                print()

def report_tabfact(all_results):
    print_section("TabFact Thought 阶段 Bad Case 分析（多模型横向对比）")

    print("## 1. 准确率概览\n")
    print(f"{'模型':<25} {'准确率':>10} {'正确/总数':>15} {'错误数':>8}")
    print("-" * 60)
    for model, r in sorted(all_results.items(), key=lambda x: x[1]['accuracy'], reverse=True):
        print(f"{model:<25} {r['accuracy']*100:>9.1f}% {r['correct']:>8}/{r['total']:<8} {len(r['bad_cases']):>8}")

    # Error type comparison
    print("\n## 2. 错误类型分布对比\n")
    all_types = set()
    for r in all_results.values():
        all_types.update(r['error_types'].keys())

    header = f"{'错误类型':<25}"
    for model in all_results:
        header += f" {model:>12}"
    print(header)
    print("-" * (25 + 13 * len(all_results)))

    for etype in sorted(all_types):
        row = f"{etype:<25}"
        for model, r in all_results.items():
            n = r['error_types'].get(etype, 0)
            total_bad = len(r['bad_cases'])
            pct = f"{n}({n/total_bad*100:.0f}%)" if total_bad > 0 else "0"
            row += f" {pct:>12}"
        print(row)

    # Chain pattern error rates
    print("\n## 3. 推理链模式的错误率（Top 10 高错误率模式）\n")
    pattern_stats = defaultdict(lambda: {'total': 0, 'errors': defaultdict(int)})
    for model, r in all_results.items():
        for pat, total in r['chain_pattern_totals'].items():
            pattern_stats[pat]['total'] += total
            pattern_stats[pat]['errors'][model] = r['chain_pattern_errors'].get(pat, 0)

    sorted_patterns = sorted(pattern_stats.items(), key=lambda x: sum(x[1]['errors'].values()), reverse=True)[:15]

    print(f"{'推理链模式':<40} {'总样本':>8}", end="")
    for model in all_results:
        print(f" {model[:8]:>10}", end="")
    print()
    print("-" * (40 + 8 + 10 * len(all_results)))

    for pat, stats in sorted_patterns:
        total = stats['total']
        row = f"{pat:<40} {total:>8}"
        for model in all_results:
            err = stats['errors'].get(model, 0)
            model_total = all_results[model]['chain_pattern_totals'].get(pat, 0)
            rate = f"{err}/{model_total}" if model_total > 0 else "-"
            row += f" {rate:>10}"
        print(row)

    # Cross-model overlap
    print("\n## 4. 模型间 Bad Case 重叠分析\n")
    model_ids = {}
    for model, r in all_results.items():
        model_ids[model] = set(bc['id'] for bc in r['bad_cases'])

    models_list = sorted(all_results.keys())
    for i, m1 in enumerate(models_list):
        for m2 in models_list[i+1:]:
            common = model_ids[m1] & model_ids[m2]
            only_m1 = model_ids[m1] - model_ids[m2]
            only_m2 = model_ids[m2] - model_ids[m1]
            print(f"  {m1} vs {m2}:")
            print(f"    共同错误: {len(common)}, 仅{m1}错: {len(only_m1)}, 仅{m2}错: {len(only_m2)}")

    if len(models_list) >= 2:
        universal = model_ids[models_list[0]]
        for m in models_list[1:]:
            universal &= model_ids[m]
        print(f"\n  所有模型都错的样本数: {len(universal)}")
        if universal:
            print(f"  占总样本比例: {len(universal)/all_results[models_list[0]]['total']*100:.1f}%")

    # Representative bad cases
    print("\n## 5. 典型 Bad Case 示例\n")
    best_model = max(all_results.items(), key=lambda x: x[1]['accuracy'])[0]
    worst_model = min(all_results.items(), key=lambda x: x[1]['accuracy'])[0]

    for label, model in [("最佳模型: " + best_model, best_model), ("最弱模型: " + worst_model, worst_model)]:
        bcs = all_results[model]['bad_cases']
        print(f"\n### {label} ({len(bcs)} 个错误)\n")
        shown_types = set()
        for bc in bcs[:30]:
            if bc['error_type'] not in shown_types:
                shown_types.add(bc['error_type'])
                stmt = bc['statement'][:100] + "..." if len(bc['statement']) > 100 else bc['statement']
                print(f"  [{bc['error_type']}] ID={bc['id']}")
                print(f"    陈述: {stmt}")
                print(f"    Gold: {bc['gold']}, Pred: {bc['pred']}")
                print(f"    Chain: {bc['chain_pattern']}")
                print()

def report_improvement_suggestions(wikitq_results, tabfact_results):
    print_section("综合改进建议")

    print("## A. WikiTQ 改进建议\n")

    # Find patterns with highest error rates across models
    print("### 1. 高错误率推理链模式 → 针对性优化\n")
    all_wikitq = wikitq_results
    pattern_total_errors = defaultdict(int)
    pattern_total_samples = defaultdict(int)
    for model, r in all_wikitq.items():
        for pat, total in r['chain_pattern_totals'].items():
            pattern_total_errors[pat] += r['chain_pattern_errors'].get(pat, 0)
            pattern_total_samples[pat] += total

    worst_patterns = sorted(pattern_total_errors.items(), key=lambda x: x[1]/x[1] if x[1] > 0 else 0, reverse=True)[:5]
    for pat, errs in worst_patterns:
        total = pattern_total_samples[pat]
        rate = errs / total * 100 if total > 0 else 0
        print(f"  - `{pat}`: 累计错误 {errs}/{total} ({rate:.1f}%)")

    print("\n### 2. 错误类型驱动的改进方向\n")
    # Aggregate error types across all models
    total_errors_by_type = Counter()
    for model, r in all_wikitq.items():
        for etype, count in r['error_types'].items():
            total_errors_by_type[etype] += count

    suggestions = {
        "数值错误": "→ 优化 sort_by / group_column 操作的数值提取逻辑，增强 TableAnalyzer 的 format_normalizations 覆盖",
        "部分匹配": "→ 增强 select_row 的模糊匹配能力，利用 ColumnNormalization 的相似度排序",
        "完全不匹配": "→ 检查推理链中间步骤是否选错了行/列，Refine 阶段的 Critic 应重点诊断此类错误",
        "误判为有值": "→ final_query 阶段增加空值检测逻辑，当表格数据不足时输出空答案",
        "误判为空值": "→ 检查 chain 中间步骤是否过度过滤了行，导致最终无数据可查",
        "数值格式差异": "→ 统一数值格式化逻辑，final_query 的 answer_format_hint 应覆盖更多格式变体",
        "近似匹配(拼写差异)": "→ 利用 ColumnNormalization 的 pylcs 相似度匹配，减少拼写错误",
        "大小写/格式差异": "→ 评估函数已 normalize，此类错误应较少，检查是否有特殊字符问题",
        "布尔判断错误": "→ WikiTQ 不应出现布尔答案，检查是否误用了 TabFact 的推理模式",
    }

    for etype, count in total_errors_by_type.most_common():
        suggestion = suggestions.get(etype, "→ 需进一步分析")
        print(f"  - {etype} (累计 {count} 个): {suggestion}")

    print("\n## B. TabFact 改进建议\n")

    all_tabfact = tabfact_results
    total_errors_by_type_tf = Counter()
    for model, r in all_tabfact.items():
        for etype, count in r['error_types'].items():
            total_errors_by_type_tf[etype] += count

    tf_suggestions = {
        "漏判(应为yes判为no)": "→ 模型倾向保守，对 entailed 陈述过于严格。Critic prompt 可增加对 entailed 的敏感度",
        "误判(应为no判为yes)": "→ 模型倾向宽松，对 refuted 陈述缺乏足够的验证。应加强数值/事实核对的推理深度",
        "格式异常": "→ final_query 输出格式不规范，需约束输出为 yes/no",
    }

    for etype, count in total_errors_by_type_tf.most_common():
        suggestion = tf_suggestions.get(etype, "→ 需进一步分析")
        print(f"  - {etype} (累计 {count} 个): {suggestion}")

    print("\n### TabFact 推理链模式优化\n")
    pattern_total_errors_tf = defaultdict(int)
    pattern_total_samples_tf = defaultdict(int)
    for model, r in all_tabfact.items():
        for pat, total in r['chain_pattern_totals'].items():
            pattern_total_errors_tf[pat] += r['chain_pattern_errors'].get(pat, 0)
            pattern_total_samples_tf[pat] += total

    worst_patterns_tf = sorted(pattern_total_errors_tf.items(), key=lambda x: x[1], reverse=True)[:5]
    for pat, errs in worst_patterns_tf:
        total = pattern_total_samples_tf[pat]
        rate = errs / total * 100 if total > 0 else 0
        print(f"  - `{pat}`: 累计错误 {errs}/{total} ({rate:.1f}%)")

    print("\n## C. 跨模型互补策略\n")
    # Find cases where some models get right and others get wrong
    print("### 模型互补分析（基于 gpt-5.4 和 qwen3:32b）\n")
    if 'gpt-5.4' in all_wikitq and 'qwen3:32b' in all_wikitq:
        gpt_ids = set(bc['id'] for bc in all_wikitq['gpt-5.4']['bad_cases'])
        qwen_ids = set(bc['id'] for bc in all_wikitq['qwen3:32b']['bad_cases'])
        gpt_only_wrong = gpt_ids - qwen_ids
        qwen_only_wrong = qwen_ids - gpt_ids
        print(f"  WikiTQ:")
        print(f"    gpt-5.4 独有错误: {len(gpt_only_wrong)} (qwen3:32b 能答对)")
        print(f"    qwen3:32b 独有错误: {len(qwen_only_wrong)} (gpt-5.4 能答对)")
        print(f"    → 若能互补，理论可额外挽回 {len(gpt_only_wrong) + len(qwen_only_wrong)} 个错误")

    if 'gpt-5.4' in all_tabfact and 'qwen3:14b' in all_tabfact:
        gpt_ids = set(bc['id'] for bc in all_tabfact['gpt-5.4']['bad_cases'])
        qwen_ids = set(bc['id'] for bc in all_tabfact['qwen3:14b']['bad_cases'])
        gpt_only_wrong = gpt_ids - qwen_ids
        qwen_only_wrong = qwen_ids - gpt_ids
        print(f"  TabFact:")
        print(f"    gpt-5.4 独有错误: {len(gpt_only_wrong)} (qwen3:14b 能答对)")
        print(f"    qwen3:14b 独有错误: {len(qwen_only_wrong)} (gpt-5.4 能答对)")
        print(f"    → 若能互补，理论可额外挽回 {len(gpt_only_wrong) + len(qwen_only_wrong)} 个错误")


def main():
    os.chdir(ROOT)

    # ===== WikiTQ =====
    wikitq_models = {
        'gpt-5.4': 'results/thought/wikitq/gpt-5.4/final_result.pkl',
        'qwen3:14b': 'results/thought/wikitq/qwen3:14b/final_result.pkl',
        'qwen3:32b': 'results/thought/wikitq/qwen3:32b/final_result.pkl',
        'qwen3-32b': 'results/thought/wikitq/qwen3-32b/final_result.pkl',
        'max_cache': 'results/thought/wikitq/max_cache/final_result.pkl',
    }

    print("Loading WikiTQ target values...")
    target_values_map = load_target_values_map('thought/TableQA/data/wikitq/tagged_data')
    print(f"Loaded {len(target_values_map)} target values")

    wikitq_results = {}
    for model, path in wikitq_models.items():
        if not os.path.exists(path):
            print(f"  [SKIP] {model}: {path} not found")
            continue
        print(f"  Loading {model}...")
        data = load_pkl(path)
        wikitq_results[model] = analyze_wikitq(data, target_values_map)
        print(f"    Acc={wikitq_results[model]['accuracy']*100:.1f}%, Errors={len(wikitq_results[model]['bad_cases'])}")

    # ===== TabFact =====
    tabfact_models = {
        'gpt-5.4': 'results/thought/tabfact/gpt-5.4/final_result.pkl',
        'qwen3:14b': 'results/thought/tabfact/qwen3:14b/final_result.pkl',
        'max_cache': 'results/thought/tabfact/max_cache/final_result.pkl',
    }

    tabfact_results = {}
    for model, path in tabfact_models.items():
        if not os.path.exists(path):
            print(f"  [SKIP] {model}: {path} not found")
            continue
        print(f"  Loading {model}...")
        data = load_pkl(path)
        tabfact_results[model] = analyze_tabfact(data)
        print(f"    Acc={tabfact_results[model]['accuracy']*100:.1f}%, Errors={len(tabfact_results[model]['bad_cases'])}")

    # ===== Generate Reports =====
    report_wikitq(wikitq_results)
    report_tabfact(tabfact_results)
    report_improvement_suggestions(wikitq_results, tabfact_results)

    print_section("分析完成")

if __name__ == "__main__":
    main()
