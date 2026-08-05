"""Write coarse-grained bead coordinates as PDB for in-browser visualization."""

from __future__ import annotations

from pathlib import Path

# Chain ID per bead role (3Dmol colors by chain)
ROLE_CHAIN: dict[str, str] = {
    "lipid": "A",
    "drug": "B",
    "protein": "C",
    "np": "A",
    "bead": "A",
    "membrane": "D",
}

ROLE_RESNAME: dict[str, str] = {
    "lipid": "LIP",
    "drug": "DRG",
    "protein": "PRO",
    "np": "NP",
    "bead": "BD",
    "membrane": "MEM",
}


def write_bead_pdb(
    path: Path,
    positions_nm: list[list[float]],
    bead_roles: list[str],
    *,
    title: str = "MultiscaleNano coarse-grained structure",
) -> None:
    """Write bead positions (nm) to PDB; coordinates stored in Angstrom."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"TITLE     {title[:70]}"]

    for idx, (pos, role) in enumerate(zip(positions_nm, bead_roles, strict=False), start=1):
        role_key = role if role in ROLE_CHAIN else "bead"
        chain = ROLE_CHAIN[role_key]
        resname = ROLE_RESNAME[role_key]
        x, y, z = (float(c) * 10.0 for c in pos[:3])
        lines.append(
            f"ATOM  {idx:5d}  CA  {resname:3s} {chain}{1:4d}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C"
        )

    lines.append("END")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
