# base_url='Qwen/Qwen2.5-72B-Instruct'
base_url='https://api.holdai.top/v1'
openai_api_key=$(cat api.txt)
model_name='qwen2.5-72b-instruct'
first_n=100
n_proc=8
chunk_size=4

thought_results_dir="results/thought_100/tabfact/${model_name}"
refine_results="results/refine_100/tabfact/${model_name}_onlyblueprint"


python thought/TableFV/main.py \
--thought_results_dir $thought_results_dir \
--base_url $base_url \
--openai_api_key $openai_api_key \
--model_name $model_name \
--first_n $first_n \
--n_proc $n_proc \
--chunk_size $chunk_size
if [ $? -ne 0 ]; then
    echo "Error in thought/TableFV/main.py"
    exit 1
fi


python refine/TableFV/main_tree_based.py \
--thought_results_dir $thought_results_dir \
--refine_results_dir $refine_results \
--base_url $base_url \
--openai_api_key $openai_api_key \
--model_name $model_name \
--first_n $first_n \
--n_proc $n_proc \
--chunk_size $chunk_size \
--use_multi_agent False \
--use_controller False
if [ $? -ne 0 ]; then
    echo "Error in refine/TableFV/main_tree_based.py"
    exit 1
fi
