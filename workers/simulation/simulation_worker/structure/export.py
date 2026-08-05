"""Export MD final coordinates for 3D visualization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from multiscale_core.structure.bead_pdb import write_bead_pdb

from simulation_worker.engine.openmm_md import MDResult


def export_md_structure(
    module_dir: Path,
    md: MDResult,
    bead_roles: list[str],
    *,
    title: str = "MultiscaleNano coarse-grained structure",
) -> dict[str, Any]:
    """Write structure.pdb under module_dir and return metadata for artifact.data."""
    if not md.success or not md.final_positions_nm:
        return {"available": False}

    positions = md.final_positions_nm
    n = len(positions)
    roles = bead_roles if len(bead_roles) == n else ["bead"] * n

    pdb_path = module_dir / "structure.pdb"
    write_bead_pdb(pdb_path, positions, roles, title=title)

    return {
        "available": True,
        "pdb_file": "structure.pdb",
        "bead_count": n,
        "bead_roles": roles,
        "positions_nm": [[round(c, 4) for c in p] for p in positions],
        "units": "nm",
        "radius_of_gyration_nm": md.radius_of_gyration_nm,
    }
