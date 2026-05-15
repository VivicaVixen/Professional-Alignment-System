@echo off
echo ========================================
echo PAS - Professional Alignment System
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo WARNING: Ollama is not running.
    echo Please start Ollama and pull the required models:
    echo   ollama pull qwen2.5-coder:7b
    echo   ollama pull deepseek-r1:7b
    echo.
    echo Starting Ollama...
    start "" "ollama" "serve"
    timeout /t 5 /nobreak >nul
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
    echo Installing dependencies...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo Starting PAS application...
echo.

REM Run Streamlit app
streamlit run ui\app.py

pause
