@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND_URL=http://127.0.0.1:8000"
set "FRONTEND_URL=http://127.0.0.1:5173"

cd /d "%ROOT%"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Python virtual environment not found: %ROOT%.venv
  echo Create it and install dependencies first:
  echo   python -m venv .venv
  echo   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -c "import fastapi, uvicorn, multipart" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Backend dependencies are missing from .venv.
  echo Install them first:
  echo   set NO_PROXY=*
  echo   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo [ERROR] Frontend dependencies not found: %ROOT%frontend\node_modules
  echo Install them first:
  echo   cd frontend
  echo   npm install
  pause
  exit /b 1
)

echo Starting backend at %BACKEND_URL%
start "AI Scorer Backend" /D "%ROOT%" cmd /k "set NO_PROXY=* && set no_proxy=* && .\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000"

echo Starting frontend at %FRONTEND_URL%
start "AI Scorer Frontend" /D "%ROOT%frontend" cmd /k "npm run dev -- --host 127.0.0.1"

timeout /t 3 /nobreak >nul
start "" "%FRONTEND_URL%"

echo.
echo Web app is starting.
echo Frontend: %FRONTEND_URL%
echo Backend:  %BACKEND_URL%
echo Close the two opened terminal windows to stop the app.
echo.
pause
