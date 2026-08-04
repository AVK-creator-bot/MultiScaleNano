"""Quick simulation test against a running API."""

import sys
import time

import httpx

base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"

h = httpx.get(f"{base}/health/ready", timeout=10).json()
print("health:", h)
if not h.get("simulations_ready"):
    raise SystemExit("OpenMM not ready — cannot simulate")

t = httpx.get(f"{base}/api/designs/templates").json()
design = t["templates"][0]["design"]
design["name"] = "Sim test"

created = httpx.post(f"{base}/api/designs", json={"design": design}).json()
run = httpx.post(
    f"{base}/api/runs",
    json={"design_id": created["id"], "simulation_mode": "standard_md"},
    timeout=120,
).json()
print("run_id:", run["id"], "modules:", [m["module"] for m in run["modules"]])
run_id = run["id"]

final = None
for i in range(90):
    time.sleep(2)
    r = httpx.get(f"{base}/api/runs/{run_id}", timeout=30).json()
    mods = [f"{m['module']}:{m['status']}" for m in r["modules"]]
    print(f"  [{i * 2}s] run={r['status']} {mods}")
    final = r
    if r["status"] in ("completed", "failed"):
        break

results = httpx.get(f"{base}/api/runs/{run_id}/results", timeout=30).json()
print("result modules:", list(results.get("modules", {}).keys()))

if final and final["status"] == "completed":
    print("SIMULATION PASSED")
else:
    raise SystemExit(f"SIMULATION FAILED: {final}")
