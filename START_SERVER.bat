@echo off
echo ========================================
echo   ATHLETIC SPIRIT - Starting Server
echo ========================================
echo.

cd /d "%~dp0\backend"

echo [1/2] Checking Python environment...
python --version
echo.

echo [2/2] Starting FastAPI backend on port 3000...
echo Backend will be available at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python -m uvicorn main:app --host 127.0.0.1 --port 3000 --reload

pause
