"""Martini 3 coarse-grained MD via martini_openmm + insane system builder."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

from multiscale_core.lipids import insane_lipid_flags
from multiscale_core.schema.nanocarrier import NanocarrierDesign

from simulation_worker.engine.openmm_md import MDResult, _jitter_positions

logger = logging.getLogger(__name__)

MARTINI_FF_FILES = (
    "martini_v3.0.0.itp",
    "martini_v3.0.0_phospholipids_v1.itp",
    "martini_v3.0_sterols_v1.0.itp",
    "martini_v3.0.0_solvents_v1.itp",
    "martini_v3.0.0_ions_v1.itp",
)

MARTINI_AVAILABLE = False
MartiniTopFile = None

try:
    import openmm
    import openmm.unit as unit
    from openmm import LangevinMiddleIntegrator, Platform
    from openmm.app import GromacsGroFile, Simulation

    from martini_openmm.martini import MartiniTopFile as _MartiniTopFile

    MartiniTopFile = _MartiniTopFile
    MARTINI_AVAILABLE = True
except ImportError:
    openmm = None  # type: ignore


def martini_ff_dir() -> Path:
    return Path(os.environ.get("MARTINI_FF_DIR", "/app/martini_ff"))


def md_steps_for_martini(mode: str) -> int:
    """Martini systems are larger — use shorter production segments on shared CPU."""
    return {"screening": 0, "standard_md": 2500, "production_md": 12000}.get(mode, 2500)


def _ensure_force_field_files(work_dir: Path) -> None:
    src = martini_ff_dir()
    for name in MARTINI_FF_FILES:
        if not (src / name).is_file():
            raise FileNotFoundError(f"Martini force field file missing: {src / name}")
        shutil.copy2(src / name, work_dir / name)
    # insane emits #include "martini.itp"; alias core parameters for nested lookups
    shutil.copy2(work_dir / "martini_v3.0.0.itp", work_dir / "martini.itp")


def _parse_lipid_indices(gro_path: Path) -> list[int]:
    """Return zero-based indices of lipid beads (exclude water and ions)."""
    skip_resnames = {"W", "WF", "PW", "NA", "CL", "K", "CA", "MG"}
    indices: list[int] = []
    lines = gro_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) < 3:
        return indices
    for i, line in enumerate(lines[2:-1]):
        if len(line) < 10:
            continue
        resname = line[5:10].strip()
        if resname not in skip_resnames:
            indices.append(i)
    return indices


def build_martini_lnp_system(
    work_dir: Path,
    design: NanocarrierDesign,
    *,
    random_seed: int,
) -> tuple[Path, Path, list[int]]:
    """Build Martini 3 lipid + water system with insane."""
    work_dir.mkdir(parents=True, exist_ok=True)
    _ensure_force_field_files(work_dir)

    box_nm = max(8.0, min(14.0, design.target_size_nm / 2 + 4.0))
    gro_path = work_dir / "system.gro"
    top_path = work_dir / "system.top"

    cmd = [
        "insane",
        "-ff",
        "M3",
        "-o",
        str(gro_path),
        "-p",
        str(top_path),
        "-x",
        str(box_nm),
        "-y",
        str(box_nm),
        "-z",
        str(box_nm),
        "-sol",
        "W",
        "-salt",
        str(design.environment.ionic_strength_m),
        "-rand",
        str(0.05 + (random_seed % 1000) / 10000.0),
        *insane_lipid_flags(design.lipids),
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(martini_ff_dir()) + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        cmd,
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=int(os.environ.get("MARTINI_BUILD_TIMEOUT", "120")),
        env=env,
    )
    (work_dir / "insane.log").write_text(
        (result.stdout or "") + "\n" + (result.stderr or ""), encoding="utf-8"
    )
    if result.returncode != 0 or not gro_path.is_file() or not top_path.is_file():
        raise RuntimeError(f"insane failed: {(result.stderr or result.stdout)[-500:]}")

    _patch_topology_includes(top_path)
    lipid_indices = _parse_lipid_indices(gro_path)
    if not lipid_indices:
        raise RuntimeError("No lipid beads found in Martini system")

    return gro_path, top_path, lipid_indices


def _patch_topology_includes(top_path: Path) -> None:
    """Rewrite insane's generic martini.itp include to Martini 3 parameter files."""
    text = top_path.read_text(encoding="utf-8")
    include_block = "\n".join(f'#include "{name}"' for name in MARTINI_FF_FILES)
    text = re.sub(
        r'#include\s+"martini\.itp"\s*\n?',
        include_block + "\n\n",
        text,
        count=1,
    )
    if not any(f'#include "{name}"' in text for name in MARTINI_FF_FILES):
        text = include_block + "\n\n" + text
    for name in MARTINI_FF_FILES:
        text = re.sub(rf'#include\s+"[^"]*{re.escape(name)}"', f'#include "{name}"', text)
    top_path.write_text(text, encoding="utf-8")


def _run_martini_production(
    work_dir: Path,
    gro_path: Path,
    top_path: Path,
    lipid_indices: list[int],
    steps: int,
    temperature_k: float,
    random_seed: int,
) -> MDResult:
    if not MARTINI_AVAILABLE or MartiniTopFile is None:
        return MDResult(False, None, None, log="martini_openmm not installed")

    log: list[str] = []
    energy_samples: list[float] = []

    try:
        conf = GromacsGroFile(str(gro_path))
        box_vectors = conf.getPeriodicBoxVectors()
        top = MartiniTopFile(
            str(top_path),
            periodicBoxVectors=box_vectors,
            epsilon_r=15.0,
        )
        system = top.create_system(nonbonded_cutoff=1.1 * unit.nanometer)
        integrator = LangevinMiddleIntegrator(
            temperature_k * unit.kelvin,
            1.0 / unit.picosecond,
            20.0 * unit.femtosecond,
        )
        platform = Platform.getPlatformByName("CPU")
        simulation = Simulation(top.topology, system, integrator, platform)

        positions = list(conf.getPositions(asNumpy=False))
        from openmm import Vec3
        import openmm.unit as unit

        vec_positions = []
        for p in positions:
            if hasattr(p, "value_in_unit"):
                v = p.value_in_unit(unit.nanometer)
                vec_positions.append(Vec3(v[0], v[1], v[2]))
            else:
                vec_positions.append(p)
        positions = _jitter_positions(vec_positions, random_seed ^ 0x4D415254)
        simulation.context.setPositions(positions)
        simulation.context.applyConstraints(1e-5)
        simulation.minimizeEnergy(maxIterations=200)
        log.append("Martini energy minimization complete")
        simulation.context.setVelocitiesToTemperature(temperature_k * unit.kelvin, random_seed)

        sample_interval = max(50, steps // 50)
        remaining = steps
        while remaining > 0:
            chunk = min(sample_interval, remaining)
            simulation.step(chunk)
            remaining -= chunk
            state = simulation.context.getState(getEnergy=True)
            energy_samples.append(
                state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
            )

        state = simulation.context.getState(getEnergy=True, getPositions=True)
        pe = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        import numpy as np

        all_pos = np.array([[p.x, p.y, p.z] for p in state.getPositions()])
        lip_pos = all_pos[lipid_indices]
        com = lip_pos.mean(axis=0)
        rg_nm = float(np.sqrt(((lip_pos - com) ** 2).sum(axis=1).mean()))
        final_positions = lip_pos.tolist()

        dists = np.linalg.norm(lip_pos - com, axis=1)
        inner_cut = np.percentile(dists, 25)
        drug_core = float((dists <= inner_cut).mean())

        n_lip = len(lipid_indices)
        expected_rg = 0.5 * (3 * n_lip / (4 * 3.14159)) ** (1 / 3) * 0.45
        compactness = float(min(1.0, max(0.01, expected_rg / max(rg_nm, 0.01))))
        energy_std = float(np.std(energy_samples)) if energy_samples else 0.0

        (work_dir / "md.log").write_text("\n".join(log), encoding="utf-8")

        return MDResult(
            success=True,
            potential_energy_kj_mol=pe,
            radius_of_gyration_nm=rg_nm,
            energy_std_kj_mol=energy_std,
            compactness=compactness,
            drug_core_fraction=drug_core,
            steps=steps,
            engine=f"martini3-openmm-{openmm.__version__}",
            log="\n".join(log),
            energy_samples=energy_samples,
            final_positions_nm=final_positions,
        )
    except Exception as exc:
        logger.exception("Martini MD failed")
        log.append(str(exc))
        (work_dir / "md.log").write_text("\n".join(log), encoding="utf-8")
        return MDResult(False, None, None, log=str(exc))


def run_martini_formation_md(
    work_dir: Path,
    design: NanocarrierDesign,
    steps: int,
    temperature_k: float,
    random_seed: int = 42,
) -> MDResult:
    work_dir.mkdir(parents=True, exist_ok=True)
    gro, top, lipid_idx = build_martini_lnp_system(work_dir, design, random_seed=random_seed)
    return _run_martini_production(
        work_dir, gro, top, lipid_idx, steps, temperature_k, random_seed
    )


def run_martini_encapsulation_md(
    work_dir: Path,
    design: NanocarrierDesign,
    steps: int,
    temperature_k: float,
    random_seed: int = 42,
    **_kwargs,
) -> MDResult:
    """Martini lipid assembly — inner-core occupancy proxies drug encapsulation."""
    return run_martini_formation_md(
        work_dir, design, steps, temperature_k, random_seed=random_seed
    )
