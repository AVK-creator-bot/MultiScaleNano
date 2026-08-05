# MultiscaleNano — ONE container, ONE URL (API + web)
# Used by Render and: docker compose up --build

FROM node:20-alpine AS web-builder

WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

COPY apps/web .
ENV API_INTERNAL_URL=http://127.0.0.1:8000
ENV NEXT_TELEMETRY_DISABLED=1
RUN mkdir -p public
RUN npm run build

FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    nodejs \
    curl \
    git \
    && (command -v node >/dev/null 2>&1 || ln -s /usr/bin/nodejs /usr/bin/node) \
    && rm -rf /var/lib/apt/lists/*

COPY packages/core /app/packages/core
COPY workers/simulation /app/workers/simulation
COPY apps/api /app/apps/api
COPY scripts/download-martini-ff.sh /app/scripts/download-martini-ff.sh

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir "setuptools>=68,<82" \
    && pip install --no-cache-dir openmm simopt \
    && pip install --no-cache-dir "git+https://github.com/maccallumlab/martini_openmm.git" \
    && pip install --no-cache-dir "git+https://github.com/Tsjerk/Insane.git" \
    && pip install --no-cache-dir -e /app/packages/core \
    && pip install --no-cache-dir -e /app/workers/simulation \
    && pip install --no-cache-dir -e /app/apps/api \
    && sed -i 's/\r$//' /app/scripts/download-martini-ff.sh \
    && chmod +x /app/scripts/download-martini-ff.sh \
    && /app/scripts/download-martini-ff.sh /app/martini_ff

COPY --from=web-builder /app/public /app/web/public
COPY --from=web-builder /app/.next/standalone /app/web
COPY --from=web-builder /app/.next/static /app/web/.next/static

COPY scripts/start-production.sh /app/start-production.sh
RUN sed -i 's/\r$//' /app/start-production.sh \
    && chmod +x /app/start-production.sh \
    && mkdir -p /data/artifacts /data/store

ENV MULTISCALE_ARTIFACT_DIR=/data/artifacts
ENV MULTISCALE_FORCE_FIELD=martini3
ENV MARTINI_FF_DIR=/app/martini_ff
ENV MULTISCALE_MD_PROFILE=web
ENV MULTISCALE_API_URL=http://127.0.0.1:8000
ENV API_INTERNAL_URL=http://127.0.0.1:8000
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0

EXPOSE 3000

CMD ["/app/start-production.sh"]
