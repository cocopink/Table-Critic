#!/bin/bash


echo "Starting 1 task (FV with qwen3:32b)..."
nohup bash run_ollama_model.sh -t FV -m qwen3:32b  -n -1 -p 1 -c 1 --use_controller True --use_clarifier True 2>&1 >logs/cl_0328_run_FV_qwen332b.log &
pid=$!
wait $pid
echo "1 task finished."

echo "Starting 2 task (QA with qwen3:32b)..."
nohup bash run_ollama_model.sh -t QA -m qwen3:32b -n -1 -p 1 -c 1 --use_controller True --use_clarifier True 2>&1 >logs/cl_0328_run_QA_qwen332b.log &
pid=$!
wait $pid
echo "2 task finished."


# echo "Starting 4 task (FV with qwen3:14b)..."
# nohup /home/ubuntu/mnt/lx/new_TC/Table-Critic/run_ollama_model.sh -t FV -m qwen3:14b -u False > 0309FVqwen314b.log 2>&1 &
# wait
echo "All tasks completed."