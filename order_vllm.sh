#!/bin/bash
# nohup python -m vllm.entrypoints.openai.api_server \
#     --model "/home/ubuntu/mnt/lx/model/Qwen3.5-9B" \
#     --host "0.0.0.0" \
#     --port "8000" \
#     --gpu-memory-utilization 0.85 \
#     --max-num-seqs 4 &


echo "Starting 1 task (FV with qwen3.5:9b)..."
nohup ./run_vllm.sh -t FV > logs/vllm_0320FV_3.5-9b.log 2>&1 &
pid=$!
wait $pid
echo "1 task finished."

echo "Starting 2 task (QA with qwen3.5:9b)..."
nohup ./run_vllm.sh -t QA > logs/vllm_0320QA_3.5-9b.log 2>&1 &
pid=$!
wait $pid
echo "2 task finished."

# echo "Starting 3 task (FV with qwen3:14b)..."
# nohup /home/ubuntu/mnt/lx/M_TC/Table-Critic/run_ollama_model.sh -t FV -m qwen3:14b -u False -n -1 -c 8  > m_0317FV_14b_new.log 2>&1 &
# pid=$!
# wait $pid
# echo "3 task finished."

# echo "Starting 4 task (QA with qwen3:14b)..."
# nohup /home/ubuntu/mnt/lx/M_TC/Table-Critic/run_ollama_model.sh -t QA -m qwen3:14b -u False -n -1 -c 8  > m_0317QA_14b_new.log 2>&1 &
# pid=$!
# wait $pid
# echo "4 task finished."





# echo "Starting 4 task (FV with qwen3:14b)..."
# nohup /home/ubuntu/mnt/lx/new_TC/Table-Critic/run_ollama_model.sh -t FV -m qwen3:14b -u False > 0309FVqwen314b.log 2>&1 &
# wait
echo "All tasks completed."