# MultiscaleNano

**Design and simulate lipid nanoparticles in your browser — one link, no setup for users.**

## For users (just open the link)

Deploy to [Render](https://render.com) once. Everyone uses your URL:

1. Push this repo to GitHub
2. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint** → select **MultiScaleNano** → **Apply**
3. Wait ~10–15 min for the first build
4. Open the **multiscale** service URL → click **Start a simulation**

No install, no terminal, no scripts for end users.

## For developers (local)

**Option A — Docker (one URL, matches production):**

```bash
docker compose up --build
```

Open **http://localhost:3000/simulate**

**Option B — Windows dev (two auto-started windows):**

```powershell
.\scripts\start-local.ps1
```

Open **http://localhost:3000/simulate**

## Architecture

Single container in production:

```
Browser → Web (port 3000) → proxies /api/* → API (127.0.0.1:8000) → OpenMM MD
```

Simulations run in-process inside the API. No Redis or separate worker required.

## Render notes

- Uses **one** Standard web service (~$25/mo) — MD simulations need CPU
- Persistent disk mounted at `/data` for artifacts and run history
- Health check: `GET /health`

## License

TBD
