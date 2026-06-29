@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   AI 文献评分工具 - 打包构建脚本
echo ========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/5] Creating virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 (
        python -m venv .venv
    )
) else (
    echo [1/5] Virtual environment already exists.
)

call ".venv\Scripts\activate.bat"

echo [2/5] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo [3/5] Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [4/5] Building EXE...
pyinstaller "AI 文献评分工具.spec" --clean --noconfirm

if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo [5/5] Done.
echo Build output: dist\AI 文献评分工具.exe
pause
