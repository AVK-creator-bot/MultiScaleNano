"""Job queue with Redis, plus in-process fallback for local dev."""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor

import httpx
import redis.asyncio as redis

from app.config import settings
from multiscale_core.schema.simulation import SimulationMode

logger = logging.getLogger(__name__)

QUEUE_NAME = "multiscale:simulation_jobs"
WORKER_HEARTBEAT_KEY = "multiscale:worker:heartbeat"
_executor = ThreadPoolExecutor(max_workers=2)


async def get_redis() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


async def _worker_is_alive(r: redis.Redis) -> bool:
    heartbeat = await r.get(WORKER_HEARTBEAT_KEY)
    return heartbeat is not None


def _run_job_sync(
    run_id: str,
    design_json: str,
    modules: list[str],
    mode: SimulationMode,
) -> None:
    import httpx

    from simulation_worker.pipeline import execute_pipeline

    try:
        execute_pipeline(
            run_id=run_id,
            design_json=design_json,
            modules=modules,
            mode=mode,
            api_url=settings.api_url,
        )
    except Exception as exc:
        logger.exception("Simulation job failed for run %s", run_id)
        try:
            httpx.patch(
                f"{settings.api_url}/api/runs/{run_id}/modules/{modules[0]}",
                params={"status": "failed", "error": str(exc)[:2000]},
                timeout=10,
            )
        except httpx.HTTPError:
            pass


async def enqueue_simulation_job(
    run_id: str,
    design_json: str,
    modules: list[str],
    mode: SimulationMode = SimulationMode.STANDARD_MD,
) -> None:
    job = {
        "run_id": run_id,
        "design_json": design_json,
        "modules": modules,
        "mode": mode.value,
    }

    # Simulations run in-process by default. Redis queue is opt-in only.
    use_in_process = True
    use_redis = settings.redis_url and settings.use_redis_queue

    if use_redis:
        try:
            r = await get_redis()
            await r.ping()
            if await _worker_is_alive(r):
                await r.rpush(QUEUE_NAME, json.dumps(job))
                await r.aclose()
                logger.info("Enqueued job %s to Redis (worker active)", run_id)
                use_in_process = False
            else:
                await r.aclose()
                logger.warning(
                    "Redis up but no worker heartbeat — running in-process for %s", run_id
                )
        except Exception as exc:
            logger.warning("Redis unavailable (%s) — running in-process", exc)

    if use_in_process:
        loop = asyncio.get_event_loop()
        loop.run_in_executor(_executor, _run_job_sync, run_id, design_json, modules, mode)
