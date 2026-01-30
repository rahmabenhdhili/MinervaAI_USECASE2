@echo off
REM Quick start script for Unified MinervaAI Platform (Windows)

echo ================================================================================
echo   UNIFIED MINERVA AI PLATFORM - STARTUP SCRIPT
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [INFO] Virtual environment not found. Creating...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Check if requirements are installed
echo [INFO] Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies already installed
)
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo [INFO] Copying .env.example to .env...
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [OK] .env file created from .env.example
        echo [ACTION REQUIRED] Please edit .env file with your API keys
        echo.
        pause
    ) else (
        echo [ERROR] .env.example not found
        echo Please create .env file manually with required API keys
        pause
        exit /b 1
    )
)

echo ================================================================================
echo   STARTING UNIFIED PLATFORM
echo ================================================================================
echo.
echo   Services Available:
echo   - B2C Marketplace:        /api/b2c/*
echo   - B2B Supplier Search:    /api/b2b/*
echo   - Usershop Recommendations: /api/usershop/*
echo   - ShopGPT Image Search:   /api/shopgpt/*
echo.
echo   Server:       http://localhost:8000
echo   API Docs:     http://localhost:8000/docs
echo   Health Check: http://localhost:8000/health
echo.
echo   Press Ctrl+C to stop the server
echo ================================================================================
echo.

REM Start the unified server
python main_unified.py

REM If server stops
echo.
echo ================================================================================
echo   SERVER STOPPED
echo ================================================================================
pause
