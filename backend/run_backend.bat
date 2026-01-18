@echo off
echo ==========================================
echo      EcoPackAI Backend Launcher
echo ==========================================

cd /d "%~dp0"

echo [1/2] Installing/Verifying Dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [WARNING] pip install returned an error.
    echo If you are using Anaconda, ignore this if packages are already installed.
    echo.
)

echo.
echo [2/2] Starting Flask Application...
python app.py

pause
