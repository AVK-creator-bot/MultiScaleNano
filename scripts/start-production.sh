#!/bin/sh
# MultiscaleNano — single-process production entry (API + web, one URL)
set -e

PORT="${PORT:-3000}"
API_PORT=8000

echo "==> Starting MultiscaleNano API on 127.0.0.1:${API_PORT}"
uvicorn app.main:app --host 127.0.0.1 --port "${API_PORT}" --app-dir /app/apps/api &

echo "==> Waiting for API to accept connections..."
for i in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1; then
    echo "==> API ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "==> ERROR: API did not become ready in time" >&2
    exit 1
  fi
  sleep 1
done

echo "==> Starting web on 0.0.0.0:${PORT}"
cd /app/web
export HOSTNAME=0.0.0.0
export PORT
exec node server.js
