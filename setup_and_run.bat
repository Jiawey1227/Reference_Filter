@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 (
        python -m venv .venv
    )
)

call ".venv\Scripts\activate.bat"

echo [2/3] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/3] Starting GUI...
python gui.py
pause
