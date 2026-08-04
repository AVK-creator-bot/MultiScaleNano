# Deploy MultiscaleNano to Render (one public URL)

Users open your Render URL — no install, no scripts.

## Steps

1. Push this repo to GitHub (`AVK-creator-bot/MultiScaleNano`)

2. Go to [dashboard.render.com](https://dashboard.render.com) → sign in with GitHub

3. **New +** → **Blueprint** → select **MultiScaleNano** → **Apply**

4. Render creates **one** service (`multiscale`) from `render.yaml` + root `Dockerfile`

5. Wait for the first build (~10–15 minutes). Open the service URL when it shows **Live**

6. Share that URL — e.g. `https://multiscale-xxxx.onrender.com/simulate`

## If a previous two-service deploy failed

Delete the old `multiscale-api` and `multiscale-web` services in Render, then re-apply the Blueprint. The new setup uses **one container** (API + web together).

## Cost

- **Standard** plan (~$25/mo) — required for CPU-heavy MD simulations
- **5 GB disk** — stores simulation artifacts and run history

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Build failed exit 1 | Pull latest `main` — PyPI dependency bug is fixed |
| Page loads but can't simulate | Check logs for OpenMM; redeploy after latest push |
| Simulation stuck on "Waiting" | Fixed in latest — run status starts immediately |

## Health check

Render pings `GET /health` on the web port. The web service proxies to the internal API.
