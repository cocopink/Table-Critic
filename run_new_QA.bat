@echo off
REM ================================================
REM Game-Driven Memory Evolution TableQA Framework
REM New QA Pipeline with Multi-Agent System
REM ================================================

REM ============== Configuration ==============
REM Read API key from siliconflow.txt
set /p SILICONFLOW_API_KEY=<siliconflow.txt

REM SiliconFlow API Configuration
set BASE_URL=https://api.siliconflow.cn/v1
set OPENAI_API_KEY=%SILICONFLOW_API_KEY%
set MODEL_NAME=Qwen/Qwen2.5-72B-Instruct

REM Dataset Configuration
set DATASET_PATH=thought/TableQA/data/wikitq/test_lower.jsonl
set FIRST_N=100

REM Results Directory Configuration
set MODEL_DIR=qwen2.5-72b-instruct
set THOUGHT_RESULTS_DIR=results/%MODEL_DIR%/thought
set REFINE_RESULTS_DIR=results/%MODEL_DIR%/refine

REM Processing Configuration
set N_PROC=4
set CHUNK_SIZE=2

REM Multi-Agent Configuration
set USE_MULTI_AGENT=true

REM ============== Print Configuration ==============
echo ================================================
echo TableQA Multi-Agent Pipeline
echo ================================================
echo Model: %MODEL_NAME%
echo Dataset: %DATASET_PATH%
echo First N: %FIRST_N%
echo Parallel Processes: %N_PROC%
echo Multi-Agent: %USE_MULTI_AGENT%
echo ================================================
echo.

REM ============== Stage 1: Thought Phase with Clarifier ==============
echo [Stage 1] Running Thought phase with ClarifierAgent...
echo Output: %THOUGHT_RESULTS_DIR%

python thought/TableQA/main.py ^
    --dataset_path "%DATASET_PATH%" ^
    --thought_results_dir "%THOUGHT_RESULTS_DIR%" ^
    --base_url "%BASE_URL%" ^
    --openai_api_key "%OPENAI_API_KEY%" ^
    --model_name "%MODEL_NAME%" ^
    --first_n %FIRST_N% ^
    --n_proc %N_PROC% ^
    --chunk_size %CHUNK_SIZE%

if errorlevel 1 (
    echo X Error in thought/TableQA/main.py
    exit /b 1
)

REM Check thought stage accuracy
if exist "%THOUGHT_RESULTS_DIR%/acc.txt" (
    echo /F Thought Stage Accuracy:
    type "%THOUGHT_RESULTS_DIR%/acc.txt"
)

echo.
echo [Stage 1] OK Thought phase completed
echo.

REM ============== Stage 2: Refinement Phase with Multi-Agent Framework ==============
echo [Stage 2] Running Refinement phase with Multi-Agent Framework...
echo Output: %REFINE_RESULTS_DIR%

python refine/TableQA/main_tree_based.py ^
    --thought_results_dir "%THOUGHT_RESULTS_DIR%" ^
    --refine_results_dir "%REFINE_RESULTS_DIR%" ^
    --base_url "%BASE_URL%" ^
    --openai_api_key "%OPENAI_API_KEY%" ^
    --model_name "%MODEL_NAME%" ^
    --first_n %FIRST_N% ^
    --n_proc %N_PROC% ^
    --chunk_size %CHUNK_SIZE% ^
    --use_multi_agent %USE_MULTI_AGENT%

if errorlevel 1 (
    echo X Error in refine/TableQA/main_tree_based.py
    exit /b 1
)

REM Check refine stage accuracy
if exist "%REFINE_RESULTS_DIR%/acc.txt" (
    echo /F Refinement Stage Accuracy:
    type "%REFINE_RESULTS_DIR%/acc.txt"
)

if exist "%REFINE_RESULTS_DIR%/result.txt" (
    echo /F Final Result:
    type "%REFINE_RESULTS_DIR%/result.txt"
)

echo.
echo [Stage 2] OK Refinement phase completed
echo.

REM ============== Summary ==============
echo ================================================
echo Pipeline Execution Summary
echo ================================================
echo Thought Results: %THOUGHT_RESULTS_DIR%
echo   - Final result: %THOUGHT_RESULTS_DIR%/final_result.pkl
echo   - Accuracy: %THOUGHT_RESULTS_DIR%/acc.txt
echo   - Clarifier outputs: %THOUGHT_RESULTS_DIR%/clarifier/
echo.
echo Refinement Results: %REFINE_RESULTS_DIR%
echo   - Final result: %REFINE_RESULTS_DIR%/final_result.pkl
echo   - Accuracy: %REFINE_RESULTS_DIR%/acc.txt
echo   - Thinking chains: %REFINE_RESULTS_DIR%/cache/
echo ================================================
echo.
echo OK TableQA pipeline completed successfully!
