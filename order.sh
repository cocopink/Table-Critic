#!/bin/bash
# 顺序执行三个任务，每个任务完成后才启动下一个
echo "Starting 1 task (FV with qwen3:32b)..."
nohup /home/ubuntu/mnt/lx/Table-Critic/run_ollama_model.sh -t FV -m qwen3:32b -n 100 -c 8  > 0310FV_32b.log 2>&1 &
pid=$!
wait $pid
echo "1 task finished."

echo "Starting 2 task (QA with qwen3:32b)..."
nohup /home/ubuntu/mnt/lx/Table-Critic/run_ollama_model.sh -t QA -m qwen3:32b -n 100 -c 8  > 0310QA_32b.log 2>&1 &
pid=$!
wait $pid
echo "2 task finished."


# echo "Starting 4 task (FV with qwen3:14b)..."
# nohup /home/ubuntu/mnt/lx/new_TC/Table-Critic/run_ollama_model.sh -t FV -m qwen3:14b -u False > 0309FVqwen314b.log 2>&1 &
# wait
echo "All tasks completed."