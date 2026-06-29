@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    call setup_and_run.bat
    exit /b %errorlevel%
)
call .venv\Scripts\activate.bat
python gui.py
pause
