# MultiscaleNano

**Design and simulate lipid nanoparticles in your browser.**

Project nanotech — no command line, no scripts, no local setup for end users. Just open the app and run simulations.

## Use it on the web

### Option A — Hosted (recommended for users)

Deploy once to Render, Railway, or any Docker host. Users visit your URL and click **Start a simulation**.

**Render (one-click):**
1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint → connect repo
3. Render reads `render.yaml` and deploys API + web
4. Share the `multiscale-web` URL with your team

### Option B — Self-host with Docker (one command)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) only:

```bash
docker compose up --build
```

Open **http://localhost:3000** — that's it. No Python, Node, or scripts to run manually.

### Option C — Local development (for contributors)

```powershell
.\scripts\start-local.ps1
```

Hot-reload for API and web during development.

## What users see

1. Open the website
2. Click **Start a simulation**
3. Pick an example (mRNA or Paclitaxel) — structure auto-validates
4. Walk through the wizard
5. Click **Start simulation** and view results

No terminal. No installation.

## Architecture

```
Browser  →  Web (Next.js, port 3000)
              ↓ proxy /api/*
           API (FastAPI, port 8000)
              ↓
           OpenMM MD simulations
```

The web app proxies all API calls — users only ever talk to one URL.

## Requirements for hosting

| Resource | Minimum |
|----------|---------|
| CPU | 2 cores (MD is CPU-bound) |
| RAM | 4 GB |
| Disk | 5 GB (simulation artifacts) |

Serverless platforms with short timeouts are not suitable — simulations run 30–45 minutes.

## License

TBD
