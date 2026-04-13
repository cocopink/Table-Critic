model_name='glm-5'
base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
openai_api_key="$DASHSCOPE_API_KEY"
# 不行的：qwen3.5-397b-a17b、qwen3.5-plus-2026-02-15 glm-5
# 可行的：deepseek-v3.2
#  kimi-k2-thinking deepseek-v3.1 qwen3-235b-a22b qwen3-max qwen2.5-math-72b-instruct

# base_url='https://yunwu.ai/v1'
# openai_api_key="$YUNWU_API_KEY"
# model_name='gpt-5.4'

# base_url='https://open.bigmodel.cn/api/paas/v4'
# openai_api_key="${GLM_API_KEY}"
# model_name='glm-4.5-air'

# base_url='https://api.holdai.top/v1'
# openai_api_key="${HAOMIAO_API_KEY}"
# model_name='gpt-4.1-mini'

first_n=-1
n_proc=8
chunk_size=4

# Mode switch: set to "orig" for original mode, "new" for new mode
MODE="new"

thought_results_dir="results/${MODE}/thought/tabfact/qwen3-32b"
refine_results="results/${MODE}/refine/tabfact/${model_name}"

python thought/TableFV/main.py \
--thought_results_dir $thought_results_dir \
--base_url $base_url \
--openai_api_key $openai_api_key \
--model_name $model_name \
--first_n $first_n \
--n_proc $n_proc \
--chunk_size $chunk_size \
--use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False")

if [ $? -ne 0 ]; then
    echo "Error in thought/TableFV/main.py"
    exit 1
fi

echo $first_n

python refine/TableFV/main_tree_based.py \
--thought_results_dir $thought_results_dir \
--refine_results_dir $refine_results \
--base_url $base_url \
--openai_api_key $openai_api_key \
--model_name $model_name \
--first_n $first_n \
--n_proc $n_proc \
--chunk_size $chunk_size \
--use_controller $([ "$MODE" = "new" ] && echo "True" || echo "False") \
--use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False")

if [ $? -ne 0 ]; then
    echo "Error in refine/TableFV/main_tree_based.py"
    exit 1
fi
