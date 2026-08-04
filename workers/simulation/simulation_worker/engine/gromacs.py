"""GROMACS engine adapter — runs simulations in Docker or locally."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

GROMACS_CONTAINER = os.environ.get("MULTISCALE_GROMACS_CONTAINER", "multiscale-gromacs")
USE_DOCKER = os.environ.get("MULTISCALE_USE_DOCKER", "false").lower() == "true"
DOCKER_TIMEOUT = 10


def run_gromacs_command(cmd: list[str], work_dir: Path) -> subprocess.CompletedProcess:
    """Execute a GROMACS command either via Docker or local gmx."""

    work_dir.mkdir(parents=True, exist_ok=True)

    if USE_DOCKER:
        docker_cmd = [
            "docker", "exec",
            "-w", "/work",
            GROMACS_CONTAINER,
            *cmd,
        ]
        # Mount work_dir into container
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{work_dir.resolve()}:/work",
            "--name", f"gromacs-job-{work_dir.name}",
            "multiscale-gromacs:latest",
            *cmd,
        ]
        logger.info("Docker GROMACS: %s", " ".join(cmd))
        return subprocess.run(docker_cmd, capture_output=True, text=True, check=False, timeout=DOCKER_TIMEOUT)

    gmx = shutil.which("gmx") or shutil.which("gmx_mpi")
    if gmx is None:
        raise RuntimeError("GROMACS not found locally and Docker disabled")

    logger.info("Local GROMACS: %s", " ".join(cmd))
    return subprocess.run([gmx, *cmd[1:]], cwd=work_dir, capture_output=True, text=True, check=False)


def check_gromacs_available() -> bool:
    if USE_DOCKER:
        try:
            result = subprocess.run(
                ["docker", "images", "-q", "multiscale-gromacs:latest"],
                capture_output=True, text=True, timeout=DOCKER_TIMEOUT,
            )
            return bool(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
    return shutil.which("gmx") is not None or shutil.which("gmx_mpi") is not None
