#!/bin/sh
# MultiscaleNano — single-process production entry (API + web, one URL)
set -e

PORT="${PORT:-3000}"
API_PORT=8000

echo "==> Starting MultiscaleNano API on 127.0.0.1:${API_PORT}"
uvicorn app.main:app --host 127.0.0.1 --port "${API_PORT}" --app-dir /app/apps/api &

echo "==> Starting web on 0.0.0.0:${PORT}"
cd /app/web
export HOSTNAME=0.0.0.0
export PORT
exec node server.js
