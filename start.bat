@echo off
REM NVIDIA Hackathon - Accessibility Auditor Start Script for Windows
echo ========================================
echo NVIDIA Hackathon - Accessibility Auditor
echo Starting Application...
echo ========================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo [ERROR] Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo [ERROR] .env file not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Dependencies not installed
    echo Installing now...
    pip install -r requirements.txt
    if errorlevel 1 (
        pip install -r backend\requirements.txt
    )
)

REM Kill any process using port 8000
echo Checking for existing server on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo Stopping existing server (PID: %%a^)
    taskkill /F /PID %%a >nul 2>&1
)

REM Start the backend server
echo.
echo Starting backend server...
echo Backend URL: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
start "Accessibility Auditor Backend" cmd /k "call venv\Scripts\activate.bat && cd backend && python main.py"

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

REM Start frontend server
echo.
echo Starting frontend server...
echo Frontend URL: http://localhost:3000
echo.
start "Accessibility Auditor Frontend" cmd /k "call venv\Scripts\activate.bat && python serve_frontend.py"

REM Wait for frontend to start
timeout /t 2 /nobreak >nul

REM Open frontend in default browser
echo Opening frontend in browser...
start "" "http://localhost:3000"

echo.
echo ========================================
echo Application started successfully!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo Close the backend and frontend windows to stop the servers
echo ========================================
