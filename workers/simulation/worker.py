"""Simulation worker — pulls jobs from Redis and runs simulation modules."""

from __future__ import annotations

import json
import logging
import os
import sys
import time

import redis

from multiscale_core.schema.simulation import SimulationMode
from simulation_worker.pipeline import execute_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("MULTISCALE_REDIS_URL", "redis://localhost:6379/0")
API_URL = os.environ.get("MULTISCALE_API_URL", "http://localhost:8000")
QUEUE_NAME = "multiscale:simulation_jobs"
HEARTBEAT_KEY = "multiscale:worker:heartbeat"
HEARTBEAT_TTL = 30


def process_job(job: dict) -> None:
    run_id = job["run_id"]
    mode = SimulationMode(job.get("mode", SimulationMode.STANDARD_MD.value))
    logger.info("Processing run %s mode=%s modules=%s", run_id, mode.value, job["modules"])

    execute_pipeline(
        run_id=run_id,
        design_json=job["design_json"],
        modules=job["modules"],
        mode=mode,
        api_url=API_URL,
    )


def main() -> None:
    logger.info("MultiscaleNano simulation worker starting...")
    logger.info("Redis: %s", REDIS_URL)

    r = redis.from_url(REDIS_URL, decode_responses=True)

    while True:
        try:
            r.setex(HEARTBEAT_KEY, HEARTBEAT_TTL, "1")
            result = r.blpop(QUEUE_NAME, timeout=5)
            if result is None:
                continue

            _, payload = result
            job = json.loads(payload)
            process_job(job)
        except redis.ConnectionError:
            logger.warning("Redis connection lost — retrying in 5s")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Worker shutting down")
            sys.exit(0)
        except Exception:
            logger.exception("Unexpected error processing job")
            time.sleep(1)


if __name__ == "__main__":
    main()
