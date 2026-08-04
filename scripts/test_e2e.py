"""Quick end-to-end API test."""

import time

import httpx

base = "http://localhost:8000"

t = httpx.get(f"{base}/api/designs/templates").json()
design = t["templates"][0]["design"]
design["name"] = "E2E Test LNP"

created = httpx.post(f"{base}/api/designs", json={"design": design}).json()
print("design_id:", created["id"])

# Test with cell_interaction enabled + standard MD
run = httpx.post(
    f"{base}/api/runs",
    json={
        "design_id": created["id"],
        "enabled_modules": [
            "encapsulation",
            "formation",
            "stability",
            "cell_interaction",
            "transport",
            "release",
        ],
        "simulation_mode": "standard_md",
    },
    timeout=120,
).json()
run_id = run["id"]
print("run_id:", run_id, "status:", run["status"])

for i in range(120):
    time.sleep(2)
    r = httpx.get(f"{base}/api/runs/{run_id}", timeout=30).json()
    mods = [f"{m['module']}:{m['status']}" for m in r["modules"]]
    print(f"  [{i*2}s] run={r['status']} modules={mods}")
    if r["status"] in ("completed", "failed"):
        break

results = httpx.get(f"{base}/api/runs/{run_id}/results", timeout=30).json()
print("results modules:", list(results.get("modules", {}).keys()))
assert r["status"] == "completed", f"Run failed: {r}"
assert "cell_interaction" in results["modules"], "cell_interaction missing"
print("E2E PASSED")
