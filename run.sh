#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

cd frontend
npm install
cd ..

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!
cd frontend
npm run dev &
UI_PID=$!

echo "Dashboard: http://localhost:5173"
echo "API docs:  http://127.0.0.1:8000/docs"
wait $API_PID $UI_PID
