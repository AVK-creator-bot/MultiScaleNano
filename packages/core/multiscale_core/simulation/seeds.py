"""Per-run random seeds so identical designs produce distinct MD trajectories."""

from __future__ import annotations

import hashlib


def run_seed(run_id: str, module: str, replicate: int = 0) -> int:
    """Stable seed for a specific run/module/replicate; varies across runs."""
    payload = f"{run_id}:{module}:{replicate}".encode()
    digest = hashlib.sha256(payload).digest()
    # OpenMM velocity seeds must fit in a signed 32-bit int.
    return int.from_bytes(digest[:4], "big") % 2_147_483_647
