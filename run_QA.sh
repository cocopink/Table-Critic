# base_url='https://yunwu.ai/v1'
# openai_api_key="$YUNWU_API_KEY"
# model_name='gpt-5.4'

model_name='glm-5'
base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
openai_api_key="$DASHSCOPE_API_KEY"

first_n=-1
n_proc=8
chunk_size=4

thought_results_dir="results/thought/wikitq/${model_name}"
refine_results="results/refine/wikitq/${model_name}"


python thought/TableQA/main.py \
--thought_results_dir $thought_results_dir \
--base_url $base_url \
--openai_api_key $openai_api_key \
--model_name $model_name \
--first_n $first_n
if [ $? -ne 0 ]; then
    echo "Error in thought/TableQA/main.py"
    exit 1
fi


python refine/TableQA/main_tree_based.py \
--thought_results_dir $thought_results_dir \
--refine_results_dir $refine_results \
--base_url $base_url \
--openai_api_key $openai_api_key \
--model_name $model_name \
--first_n $first_n
if [ $? -ne 0 ]; then
    echo "Error in refine/TableQA/main_tree_based.py"
    exit 1
fi