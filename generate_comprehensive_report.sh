#!/bin/bash

echo "开始生成综合分析报告..."
echo ""

# 1. 生成基础分析报告（已有）
echo "1. 基础分析报告已存在：bad-case-analysis.md"

# 2. 将详细分析追加到飞书文档
echo ""
echo "2. 准备上传到飞书..."
lark-cli docs +update \
  --doc-id "Y5otdboS7oxoE8x8s9acY9v1ncb" \
  --mode append \
  --markdown "$(cat bad-case-analysis.md)" 2>&1 | tail -20

echo ""
echo "✅ 综合分析报告生成完成！"
echo ""
echo "报告包括："
echo "- 基础错误分类分析"
echo "- 高级错误分类分析（18种详细类型）"
echo "- WikiTQ和TabFact对比分析"
echo "- 详细错误案例分析"
echo "- 错误案例ID分类表"
