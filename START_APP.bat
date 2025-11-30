@echo off
echo ========================================
echo   ATHLETIC SPIRIT - Full Stack Launch
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Starting Backend Server...
echo.
start "Athletic Spirit Backend" cmd /k "cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 3000 --reload"

timeout /t 3 /nobreak >nul

echo [2/3] Waiting for backend to start...
timeout /t 2 /nobreak >nul

echo [3/3] Opening Frontend in Browser...
echo.
start "" "athleteai.html"

echo.
echo ========================================
echo   Application Started!
echo ========================================
echo.
echo Backend: http://localhost:3000
echo Frontend: athleteai.html (opened in browser)
echo.
echo To stop: Close the backend terminal window
echo ========================================
echo.
pause
