"""Real molecular dynamics using OpenMM — outputs used directly for analysis."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

OPENMM_AVAILABLE = False
try:
    import openmm
    import openmm.unit as unit
    from openmm import HarmonicBondForce, LangevinMiddleIntegrator, NonbondedForce, Platform, System, Vec3
    from openmm.app import Element, Simulation, Topology

    OPENMM_AVAILABLE = True
except ImportError:
    pass


@dataclass
class MDResult:
    success: bool
    potential_energy_kj_mol: float | None
    radius_of_gyration_nm: float | None
    energy_std_kj_mol: float | None = None
    compactness: float | None = None
    drug_core_fraction: float | None = None
    steps: int = 0
    engine: str = "none"
    log: str = ""
    energy_samples: list[float] = field(default_factory=list)
    final_positions_nm: list[list[float]] | None = None


def md_steps_for_mode(mode: str) -> int:
    return {"screening": 0, "standard_md": 5000, "production_md": 25000}.get(mode, 5000)


def replicate_count_for_mode(mode: str) -> int:
    return {"screening": 0, "standard_md": 3, "production_md": 5}.get(mode, 3)


def _build_lj_cluster_system(n_particles: int, box_nm: float, epsilon: float = 2.0) -> System:
    specs = [(72.0, 0.45, epsilon)] * n_particles
    return _build_typed_lj_system(specs, box_nm)


def _build_typed_lj_system(
    bead_specs: list[tuple[float, float, float]],
    box_nm: float,
) -> System:
    """Build LJ system from (mass_amu, sigma_nm, epsilon_kj_mol) per bead."""
    system = System()
    a = Vec3(box_nm, 0, 0)
    b = Vec3(0, box_nm, 0)
    c = Vec3(0, 0, box_nm)
    system.setDefaultPeriodicBoxVectors(a, b, c)

    nb = NonbondedForce()
    nb.setNonbondedMethod(NonbondedForce.CutoffPeriodic)
    nb.setCutoffDistance(1.2 * unit.nanometer)

    for mass_amu, sigma_nm, epsilon in bead_specs:
        system.addParticle(mass_amu * unit.amu)
        nb.addParticle(0.0, sigma_nm * unit.nanometer, epsilon * unit.kilojoule_per_mole)

    bonds = HarmonicBondForce()
    n = len(bead_specs)
    for i in range(n - 1):
        bonds.addBond(
            i, i + 1, 0.45 * unit.nanometer, 1200 * unit.kilojoule_per_mole / unit.nanometer**2
        )
    if n > 4:
        bonds.addBond(
            0, n // 2, 0.7 * unit.nanometer, 400 * unit.kilojoule_per_mole / unit.nanometer**2
        )

    system.addForce(nb)
    system.addForce(bonds)
    return system


def _initial_encapsulation_positions(
    n_lipid: int, n_drug: int, radius_nm: float
) -> tuple[list, list[int]]:
    """Drug beads at core, lipid beads on shell."""
    import math

    positions: list = []
    drug_indices = list(range(n_drug))

    golden = math.pi * (3 - math.sqrt(5))
    inner_r = radius_nm * 0.35
    for i in range(n_drug):
        t = golden * i
        y = 1 - (i / max(n_drug - 1, 1)) * 2
        r = math.sqrt(max(0, 1 - y * y))
        positions.append(Vec3(math.cos(t) * r * inner_r, y * inner_r, math.sin(t) * r * inner_r))

    outer_r = radius_nm * 0.85
    for i in range(n_lipid):
        t = golden * (i + n_drug)
        y = 1 - (i / max(n_lipid - 1, 1)) * 2
        r = math.sqrt(max(0, 1 - y * y))
        positions.append(
            Vec3(math.cos(t) * r * outer_r, y * outer_r, math.sin(t) * r * outer_r)
        )

    return positions, drug_indices


def _initial_sphere_positions(n: int, radius_nm: float) -> list:
    import math

    positions = []
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        t = golden * i
        y = 1 - (i / max(n - 1, 1)) * 2
        r = math.sqrt(max(0, 1 - y * y))
        positions.append(Vec3(math.cos(t) * r * radius_nm, y * radius_nm, math.sin(t) * r * radius_nm))
    return positions


def _run_md(
    system: System,
    positions: list,
    steps: int,
    temperature_k: float,
    work_dir: Path,
    drug_indices: list[int] | None = None,
    sample_interval: int = 100,
    random_seed: int = 42,
) -> MDResult:
    if not OPENMM_AVAILABLE:
        return MDResult(False, None, None, log="OpenMM not installed — pip install openmm")

    log: list[str] = []
    energy_samples: list[float] = []

    try:
        n = system.getNumParticles()
        topology = Topology()
        chain = topology.addChain()
        res = topology.addResidue("BEAD", chain)
        for i in range(n):
            topology.addAtom(f"B{i}", Element.getBySymbol("C"), res)

        integrator = LangevinMiddleIntegrator(
            temperature_k * unit.kelvin,
            1.0 / unit.picosecond,
            2.0 * unit.femtosecond,
        )
        simulation = Simulation(topology, system, integrator, Platform.getPlatformByName("CPU"))
        simulation.context.setPositions(positions)

        simulation.minimizeEnergy(maxIterations=500)
        log.append("energy minimization complete")
        simulation.context.setVelocitiesToTemperature(
            temperature_k * unit.kelvin, random_seed
        )

        remaining = steps
        while remaining > 0:
            chunk = min(sample_interval, remaining)
            simulation.step(chunk)
            remaining -= chunk
            state = simulation.context.getState(getEnergy=True)
            energy_samples.append(
                state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
            )

        log.append(f"MD production complete: {steps} steps, {len(energy_samples)} samples")

        state = simulation.context.getState(getEnergy=True, getPositions=True)
        pe = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)

        import numpy as np

        pos = np.array([[p.x, p.y, p.z] for p in state.getPositions()])
        com = pos.mean(axis=0)
        rg_nm = float(np.sqrt(((pos - com) ** 2).sum(axis=1).mean()))
        final_positions = pos.tolist()

        # Compactness: inverse of normalized Rg (simulated geometry)
        expected_rg = 0.5 * (3 * n / (4 * 3.14159)) ** (1 / 3) * 0.45
        compactness = float(min(1.0, max(0.01, expected_rg / max(rg_nm, 0.01))))

        drug_core = None
        if drug_indices:
            dists = np.linalg.norm(pos[drug_indices] - com, axis=1)
            drug_core = float((dists < rg_nm * 0.6).mean())

        energy_std = float(np.std(energy_samples)) if energy_samples else 0.0

        (work_dir / "md.log").write_text("\n".join(log), encoding="utf-8")
        (work_dir / "energy_samples.txt").write_text(
            "\n".join(f"{e:.4f}" for e in energy_samples), encoding="utf-8"
        )

        return MDResult(
            success=True,
            potential_energy_kj_mol=pe,
            radius_of_gyration_nm=rg_nm,
            energy_std_kj_mol=energy_std,
            compactness=compactness,
            drug_core_fraction=drug_core,
            steps=steps,
            engine=f"openmm-{openmm.__version__}",
            log="\n".join(log),
            energy_samples=energy_samples,
            final_positions_nm=final_positions,
        )
    except Exception as exc:
        logger.exception("MD simulation failed")
        log.append(str(exc))
        (work_dir / "md.log").write_text("\n".join(log), encoding="utf-8")
        return MDResult(False, None, None, log=str(exc))


def run_encapsulation_md(
    work_dir: Path,
    lipid_bead_count: int,
    drug_bead_count: int,
    steps: int,
    temperature_k: float,
    target_radius_nm: float,
    random_seed: int = 42,
    lipid_bead_specs: list[tuple[float, float, float]] | None = None,
) -> MDResult:
    """Drug-in-LNP encapsulation: core drug beads + lipid shell beads."""
    work_dir.mkdir(parents=True, exist_ok=True)
    n_lipid = max(8, lipid_bead_count)
    n_drug = max(2, drug_bead_count)
    box = max(target_radius_nm * 4, 10.0)

    if lipid_bead_specs and len(lipid_bead_specs) == n_lipid:
        drug_specs = [(80.0, 0.40, 2.8)] * n_drug
        system = _build_typed_lj_system(lipid_bead_specs + drug_specs, box_nm=box)
    else:
        system = _build_lj_cluster_system(n_lipid + n_drug, box_nm=box, epsilon=2.2)

    positions, drug_indices = _initial_encapsulation_positions(n_lipid, n_drug, target_radius_nm)
    return _run_md(
        system, positions, steps, temperature_k, work_dir,
        drug_indices=drug_indices, random_seed=random_seed,
    )


def run_formation_md(
    work_dir: Path,
    n_beads: int,
    radius_nm: float,
    steps: int,
    temperature_k: float,
    random_seed: int = 42,
    lipid_bead_specs: list[tuple[float, float, float]] | None = None,
) -> MDResult:
    work_dir.mkdir(parents=True, exist_ok=True)
    n = max(15, min(n_beads, 80))
    box = max(radius_nm * 4, 10.0)
    if lipid_bead_specs and len(lipid_bead_specs) == n:
        system = _build_typed_lj_system(lipid_bead_specs, box_nm=box)
    else:
        system = _build_lj_cluster_system(n, box_nm=box, epsilon=1.8)
    positions = _initial_sphere_positions(n, radius_nm=radius_nm / 2)
    return _run_md(system, positions, steps, temperature_k, work_dir, random_seed=random_seed)


def run_replicated_md(run_fn, n_replicates: int = 3) -> list[MDResult]:
    """Run independent MD replicates (different velocity seeds) for uncertainty."""
    results = []
    for i in range(n_replicates):
        results.append(run_fn(replicate=i))
    return results


def run_thermal_stability_md(
    work_dir: Path,
    n_beads: int,
    radius_nm: float,
    steps: int,
    temperature_k: float,
    random_seed: int = 42,
) -> tuple[MDResult, MDResult, float]:
    """MD at T and T+10K — stability from structural response."""

    md_base = run_formation_md(
        work_dir / "base",
        n_beads,
        radius_nm,
        steps,
        temperature_k,
        random_seed=random_seed,
    )
    md_hot = run_formation_md(
        work_dir / "perturbed",
        n_beads,
        radius_nm,
        steps,
        temperature_k + 10.0,
        random_seed=random_seed + 1000,
    )

    if not md_base.success or not md_hot.success:
        return md_base, md_hot, 0.0

    rg_base = md_base.radius_of_gyration_nm or 1.0
    rg_hot = md_hot.radius_of_gyration_nm or rg_base
    stability = max(0.0, min(1.0, 1.0 - abs(rg_hot - rg_base) / max(rg_base, 0.01)))
    return md_base, md_hot, stability


def run_corona_adsorption_md(
    work_dir: Path,
    np_beads: int,
    protein_beads: int,
    np_radius_nm: float,
    steps: int,
    temperature_k: float,
    random_seed: int = 42,
) -> tuple[MDResult, int, float]:
    """NP cluster + protein beads — count surface adsorption from final configuration."""
    work_dir.mkdir(parents=True, exist_ok=True)
    n_np = max(10, np_beads)
    n_prot = max(5, protein_beads)
    n_total = n_np + n_prot
    box = max(np_radius_nm * 8, 15.0)

    system = _build_lj_cluster_system(n_total, box_nm=box, epsilon=1.5)
    np_pos = _initial_sphere_positions(n_np, np_radius_nm / 2)
    import random

    random.seed(7)
    prot_pos = []
    for _ in range(n_prot):
        import math

        theta = random.uniform(0, 2 * math.pi)
        phi = random.uniform(0, math.pi)
        r = np_radius_nm * 1.5 + random.uniform(0, 2)
        prot_pos.append(
            Vec3(
                r * math.sin(phi) * math.cos(theta),
                r * math.sin(phi) * math.sin(theta),
                r * math.cos(phi),
            )
        )
    positions = np_pos + prot_pos

    md = _run_md(system, positions, steps, temperature_k, work_dir, random_seed=random_seed)

    adsorbed = 0
    ligand_frac = 1.0
    if md.success and md.final_positions_nm:
        import numpy as np

        pos = np.array(md.final_positions_nm)
        np_com = pos[:n_np].mean(axis=0)
        np_rg = float(np.sqrt(((pos[:n_np] - np_com) ** 2).sum(axis=1).mean()))
        cutoff_nm = np_rg + 1.2
        for prot in pos[n_np:]:
            if float(np.linalg.norm(prot - np_com)) < cutoff_nm:
                adsorbed += 1
        ligand_frac = max(0.05, 1.0 - adsorbed / max(n_prot, 1) * 0.6)

    return md, adsorbed, ligand_frac


def run_membrane_approach_md(
    work_dir: Path,
    n_beads: int,
    radius_nm: float,
    steps: int,
    temperature_k: float,
    random_seed: int = 42,
) -> tuple[MDResult, float]:
    """NP cluster with harmonic wall (membrane proxy) — adhesion from minimum energy."""
    from openmm import CustomExternalForce

    work_dir.mkdir(parents=True, exist_ok=True)
    n = max(12, n_beads)
    box = max(radius_nm * 4, 12.0)
    system = _build_lj_cluster_system(n, box_nm=box, epsilon=2.0)
    positions = _initial_sphere_positions(n, radius_nm=radius_nm / 2)

    wall_z = -box / 2 + 1.0
    wall = CustomExternalForce(f"0.5 * k * (z - {wall_z})^2 * step({wall_z} - z)")
    wall.addGlobalParameter("k", 500.0)
    wall.addPerParticleParameter("dummy")
    for i in range(n):
        wall.addParticle(i, [0])
    system.addForce(wall)

    md = _run_md(system, positions, steps, temperature_k, work_dir, random_seed=random_seed)
    kT_kj = 8.314e-3 * temperature_k
    adhesion_kT = abs(md.potential_energy_kj_mol or 0) / max(kT_kj * n, 0.01)
    return md, adhesion_kT


