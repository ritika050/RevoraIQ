@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher "py" was not found. Install Python 3.11+ and retry.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -3.11 -m venv .venv 2>nul || py -3 -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt

where npm >nul 2>nul
if errorlevel 1 (
  echo Node.js/npm not found. Backend will still start. Install Node LTS and re-run to start the dashboard.
  start "RevoralQ API" cmd /k "cd /d %~dp0 && .venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
  echo API: http://127.0.0.1:8000/docs
  exit /b 0
)

cd frontend
if not exist node_modules (
  npm install
)
cd ..

start "RevoralQ API" cmd /k "cd /d %~dp0 && .venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
timeout /t 3 /nobreak >nul
start "RevoralQ UI" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo RevoralQ is starting.
echo Dashboard: http://localhost:5173
echo API docs:  http://127.0.0.1:8000/docs
echo.
