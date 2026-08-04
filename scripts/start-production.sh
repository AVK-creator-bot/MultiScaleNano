#!/bin/sh
# MultiscaleNano — single-process production entry (API + web, one URL)
set -e

PORT="${PORT:-3000}"
API_PORT=8000

echo "==> Starting MultiscaleNano API on 127.0.0.1:${API_PORT}"
uvicorn app.main:app --host 127.0.0.1 --port "${API_PORT}" --app-dir /app/apps/api &
API_PID=$!

echo "==> Waiting for API..."
ready=0
i=0
while [ "$i" -lt 60 ]; do
  if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${API_PORT}/health', timeout=2)" 2>/dev/null; then
    ready=1
    break
  fi
  i=$((i + 1))
  sleep 1
done

if [ "$ready" -ne 1 ]; then
  echo "ERROR: API failed to start"
  kill "$API_PID" 2>/dev/null || true
  exit 1
fi

# Verify OpenMM (simulations require it)
python -c "
from simulation_worker.engine.openmm_md import OPENMM_AVAILABLE
import sys
if not OPENMM_AVAILABLE:
    print('WARNING: OpenMM not available — simulations disabled')
    sys.exit(0)
import openmm
print(f'OpenMM {openmm.__version__} ready')
"

echo "==> Starting web on 0.0.0.0:${PORT}"
cd /app/web
export HOSTNAME=0.0.0.0
export PORT
exec node server.js
