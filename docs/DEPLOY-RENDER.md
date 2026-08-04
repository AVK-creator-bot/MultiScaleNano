# Deploy to Render (5 minutes)

You only need to do **one thing I cannot do for you**: sign in to Render and connect your GitHub account. Everything else is below.

## Before you start

- A [GitHub](https://github.com) account
- A [Render](https://render.com) account (free to create)
- This project pushed to a GitHub repository

## Step 1 — Put the code on GitHub

If you haven't already, from the project folder:

```powershell
cd C:\Users\aryak\Projects\MultiscaleNano
git add .
git commit -m "Initial MultiscaleNano web app"
```

Create a new repo on GitHub (e.g. `MultiscaleNano`), then:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/MultiscaleNano.git
git branch -M main
git push -u origin main
```

## Step 2 — Connect Render (one-time)

1. Go to **[dashboard.render.com](https://dashboard.render.com)**
2. Sign up / sign in → choose **Sign in with GitHub**
3. Authorize Render to access your repositories

That's the "connect Render" step — it takes about 30 seconds.

## Step 3 — Deploy from blueprint

1. In Render, click **New +** → **Blueprint**
2. Connect the `MultiscaleNano` repository you just pushed
3. Render reads `render.yaml` and shows two services:
   - `multiscale-api` — simulation engine (Standard plan, ~$25/mo — needed for CPU/RAM)
   - `multiscale-web` — the website users visit (Starter plan)
4. Click **Apply**

First deploy takes ~10–15 minutes (Docker build includes OpenMM).

## Step 4 — Share the URL

When deploy finishes, open the **`multiscale-web`** service URL, e.g.:

`https://multiscale-web-xxxx.onrender.com`

That is your public app. Users open it and click **Start a simulation** — no install, no scripts.

## Costs (approximate)

| Service | Plan | Why |
|---------|------|-----|
| multiscale-web | Starter (~$7/mo) | Serves the website |
| multiscale-api | Standard (~$25/mo) | Runs 30–45 min MD simulations |

Simulations need always-on CPU; free tier will time out.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Web shows "Service unavailable" | Wait for API health check to pass (OpenMM install on first boot) |
| API deploy fails | Check logs — needs Standard plan + disk |
| Simulations fail | API service must stay running; don't use free tier for API |

## Alternative — no Render bill

Run on your own machine or a VPS with Docker only:

```bash
docker compose up --build
```

Share via tunnel (ngrok, Cloudflare Tunnel) if you want others to access it temporarily.
