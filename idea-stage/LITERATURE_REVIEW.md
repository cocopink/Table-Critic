# Literature Review: Question-Aware Executable Table Curation

**Date**: 2026-05-26
**Research Direction**: Learned executable operation sequence prediction for table reasoning preprocessing
**Sources**: Web search (arXiv, Semantic Scholar, ACL Anthology)

---

## Core Related Work

### 1. Direct Competitors — Table Preprocessing for QA

| Paper | Venue | Method | Key Result | Relevance | Status |
|-------|-------|--------|------------|-----------|--------|
| **AutoPrep** (Pan et al.) | VLDB 2025 | Multi-agent LLM framework for question-aware data preparation: Planner → Executor → Answerer | SOTA on TQA benchmarks, +12.22 points over no-prep methods | **MOST RELEVANT** — 直接竞品！同样做 question-aware table preparation，但使用多 LLM agent，不是小模型 DSL | ✅ verified |
| **NormTab** (Nahid & Rafiei) | EMNLP 2024 Findings | LLM-based web table normalization as standalone preprocessing step | Significant improvement on Text-to-SQL and table QA after normalization | **HIGH** — 已证明值标准化有用，是我们的基础假设之一 | ✅ verified |
| **TART** (Lu, Pan et al.) | NAACL 2025 Findings | Table Formatter + Tool Maker + Explanation Generator; formats tables for LLM ingestion | Best Paper Runner-Up, NeurIPS 2024 Workshop | **HIGH** — Table Formatter 是相邻工作，但它关注线性化表示而非操作序列 | ✅ verified |

### 2. Foundational — Table Operation Chains

| Paper | Venue | Method | Key Result | Relevance | Status |
|-------|-------|--------|------------|-----------|--------|
| **Chain-of-Table** (Wang et al.) | ICLR 2024 | 6 table operations (select_row, select_column, group_by, sort, agg) executed sequentially | SOTA on WikiTQ, TabFact, FeTaQA | **FOUNDATION** — 我们的 DSL 设计直接借鉴其操作集，但用于推理前预处理而非推理中 | ✅ verified |
| **PoTable** | arXiv 2024 | Plan-then-Execute two-phase approach for table operations | Extends CoT with explicit planning | **MEDIUM** — 分离 planning 和 execution 的思想可参考 | ⚠️ UNVERIFIED |

### 3. Neurosymbolic DSL / Operation Prediction

| Paper | Venue | Method | Key Result | Relevance | Status |
|-------|-------|--------|------------|-----------|--------|
| **Latent Execution for Neural Program Synthesis** | NeurIPS 2021 | Operation predictor with operation table for program synthesis | Bridges neural prediction with executable DSL | **MEDIUM** — 操作预测 + DSL 执行的方法论参考 | ✅ verified |
| **Execution-Guided Neural Program Synthesis** | ICLR | Program execution as sequence of manipulations | DSL-based execution guides neural synthesizer | **MEDIUM** — 执行引导的思想可参考 | ✅ verified |
| **TF-Coder** (ACM) | ACM | Predict operations from input/output features and NL descriptions | TensorFlow operation prediction | **LOW** — 操作预测的通用方法论 | ✅ verified |

### 4. Table Reasoning Frameworks (Baseline Context)

| Paper | Venue | Method | Key Result | Relevance | Status |
|-------|-------|--------|------------|-----------|--------|
| **Table-Critic** (Yu et al.) | ACL 2025 | Multi-agent Critic-Validator-Refiner with memory evolution | Base framework for our work | **BASE** — 我们的基础框架 | ✅ verified |
| **PanelTR** (Ma et al.) | IJCNN 2025 | Multi-role scientist discussion → consensus voting | Zero-shot, no memory | **LOW** — 竞品但不同方向 | ⚠️ UNVERIFIED |
| **TableMind / TableMind++** | ACM TOIS 2025 / arXiv | SFT+RL self-programming agent | Requires training | **LOW** — 竞品但不同方向 | ⚠️ UNVERIFIED |
| **ReAcTable** (Zhang et al.) | VLDB 2024 | ReAct paradigm for table reasoning | Single agent | **LOW** — 不同范式 | ⚠️ UNVERIFIED |

### 5. Data Preparation / BI (Adjacent)

| Paper | Venue | Method | Key Result | Relevance | Status |
|-------|-------|--------|------------|-----------|--------|
| **Auto-Prep** (Microsoft) | VLDB 2025 | Graph-based prediction of data prep steps for BI | Studied 2K real BI projects | **LOW** — BI 场景，非 table reasoning | ✅ verified |

---

## Critical Gap Analysis

### What Exists:
1. **AutoPrep** — question-aware data prep, but uses expensive multi-LLM agents
2. **NormTab** — proves normalization helps, but uses LLM directly
3. **Chain-of-Table** — operation chain for reasoning, but during inference not before
4. **TART** — table formatting, but focuses on linearization not structural transform

### What Doesn't Exist (Our Niche):
> **No work trains a small, efficient model to predict question-conditioned, executable table preprocessing operations that are specifically optimized for downstream table reasoning accuracy.**

Specifically, the combination of ALL of:
1. **Question-conditioned** — operations depend on the query
2. **Executable DSL** — deterministic Python executor, not free-form output
3. **Small model** — SLM (3B class) with LoRA, not multi-LLM agents
4. **Downstream reward** — labels from QA/FV accuracy, not GPT distillation alone
5. **Table reasoning oriented** — designed for WikiTQ/TabFact, not general BI

### Differentiation from AutoPrep (Biggest Threat):
- AutoPrep uses **multi-LLM agents** → expensive per-sample cost
- We use **single SLM prediction** → orders of magnitude cheaper
- AutoPrep's executor is **LLM-driven** → non-deterministic
- Our executor is **deterministic Python** → reproducible, interpretable
- AutoPrep targets **general TQA** → we target **multi-stage pipeline enhancement**

### Differentiation from NormTab:
- NormTab uses **LLM directly** for normalization → expensive
- We use **SLM prediction + deterministic executor** → cheap
- NormTab is **task-agnostic** → we are **question-aware**

### Differentiation from Chain-of-Table:
- CoT operations happen **during reasoning** → they ARE the reasoning
- Our operations happen **before reasoning** → they prepare the table
- CoT requires **large LLM** → we use **small model**
- CoT has **6 reasoning operations** → we have **6 preprocessing operations** (different purpose)

---

## Synthesis

The field of table preprocessing for reasoning is converging on two insights:

1. **Question-awareness matters**: Both AutoPrep (VLDB 2025) and our TableAnalyzer show that query-specific preprocessing outperforms generic cleaning.
2. **Execution is better than generation**: Chain-of-Table (ICLR 2024) proved that structured operations with deterministic execution outperform free-form reasoning.

However, the current frontier (AutoPrep) achieves this through expensive multi-LLM pipelines. No one has explored whether a **small, fine-tuned model** can achieve comparable preprocessing quality at a fraction of the cost, using an **executable operation DSL** that guarantees interpretability.

This is our niche: **cheap, question-aware, executable table curation** — the "preprocessing version of Chain-of-Table" powered by a small model instead of a large one.

---

## Risk: AutoPrep's +12.22 Point Claim

AutoPrep reports +12.22 points improvement. If this is on the same benchmarks (WikiTQ, TabFact), it significantly compresses our novelty ceiling. We need to:
1. **Verify AutoPrep's numbers on our setting** — they may use different models/splits
2. **Position ourselves as "efficient AutoPrep"** — same quality, 100x cheaper
3. **Focus on pipeline integration** — AutoPrep is standalone; we integrate with multi-stage reasoning
