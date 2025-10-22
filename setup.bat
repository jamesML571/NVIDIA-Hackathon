@echo off
REM NVIDIA Hackathon - Accessibility Auditor Setup Script for Windows
echo ========================================
echo NVIDIA Hackathon - Accessibility Auditor
echo Windows Setup Script
echo ========================================
echo.

REM Check if Python is installed
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
python --version
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment and install dependencies
echo [3/5] Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    echo Trying to install from backend directory...
    pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo [ERROR] Could not install dependencies
        pause
        exit /b 1
    )
)
echo Dependencies installed successfully
echo.

REM Setup .env file
echo [4/5] Setting up environment configuration...
if exist .env (
    echo .env file already exists
) else (
    if exist .env.example (
        copy .env.example .env >nul
        echo Created .env file from template
    ) else (
        echo Creating .env file...
        (
            echo # NVIDIA NIM API Configuration
            echo NVIDIA_API_KEY=your_nvidia_api_key_here
            echo NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
            echo.
            echo # Model Configuration
            echo NEMOTRON_MODEL=nvidia/nemotron-4-340b-instruct
            echo LLAMA_MODEL=meta/llama-3.1-70b-instruct
            echo.
            echo # Server Configuration
            echo PORT=8000
            echo HOST=0.0.0.0
            echo ENVIRONMENT=development
            echo.
            echo # Frontend URL
            echo FRONTEND_URL=http://localhost:3000
        ) > .env
        echo Created .env file
    )
)
echo.

REM Final instructions
echo [5/5] Setup complete!
echo ========================================
echo.
echo IMPORTANT: Configure your NVIDIA API key
echo 1. Open .env file in a text editor
echo 2. Replace 'your_nvidia_api_key_here' with your actual API key
echo 3. Get your API key at: https://build.nvidia.com
echo.
echo To start the application, run: start.bat
echo.
echo ========================================
pause
