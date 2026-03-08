@echo off
REM ================================================
REM TableQA Pipeline - Background Execution Script
REM ================================================

REM Generate timestamp for log filename
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

REM Log file with timestamp
set LOG_FILE=0307_%TIMESTAMP%.log

echo ================================================
echo Starting TableQA Pipeline in background...
echo Log file: %LOG_FILE%
echo ================================================
echo.

REM Start the main script in background with output redirection
start /min cmd /c run_new_QA.bat >> %LOG_FILE% 2>&1

echo.
echo ================================================
echo Task started successfully!
echo.
echo The pipeline is running in the background.
echo All output will be saved to: %LOG_FILE%
echo.
echo To monitor progress, use:
echo   powershell -Command "Get-Content %LOG_FILE% -Wait -Tail 20"
echo.
echo ================================================

timeout /t 3 >nul
