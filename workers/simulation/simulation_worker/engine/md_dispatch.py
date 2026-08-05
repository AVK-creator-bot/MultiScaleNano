"""Route MD jobs to Martini 3 or LJ backend — no silent fallbacks."""

from __future__ import annotations

from pathlib import Path

from multiscale_core.schema.nanocarrier import NanocarrierDesign

from simulation_worker.engine import openmm_md as lj
from simulation_worker.engine.openmm_md import MDResult
from simulation_worker.modules.errors import SimulationAnalysisError

MARTINI_AVAILABLE = False
try:
    from simulation_worker.engine import martini_md as martini

    MARTINI_AVAILABLE = martini.MARTINI_AVAILABLE
except ImportError:
    martini = None  # type: ignore


def use_martini3() -> bool:
    from multiscale_core.simulation.force_field import prefer_martini3

    return prefer_martini3() and MARTINI_AVAILABLE and martini is not None


def active_force_field() -> str:
    from multiscale_core.simulation.force_field import provenance_force_field

    return provenance_force_field(use_martini3())


def force_field_from_engine(engine: str | None) -> str:
    if engine and engine.startswith("martini"):
        return "martini3"
    return "lj_coarse_grained"


def md_steps_for_mode(mode: str) -> int:
    if use_martini3() and martini is not None:
        return martini.md_steps_for_martini(mode)
    return lj.md_steps_for_mode(mode)


def replicate_count_for_mode(mode: str) -> int:
    if use_martini3() and martini is not None:
        return martini.replicate_count_for_martini(mode)
    return lj.replicate_count_for_mode(mode)


def _fail_if_unsuccessful(result: MDResult, context: str) -> MDResult:
    if not result.success:
        raise SimulationAnalysisError(f"{context} failed: {result.log}")
    return result


def run_formation_md(
    work_dir: Path,
    n_beads: int,
    radius_nm: float,
    steps: int,
    temperature_k: float,
    random_seed: int = 42,
    lipid_bead_specs=None,
    design: NanocarrierDesign | None = None,
) -> MDResult:
    if use_martini3() and design is not None and martini is not None:
        return _fail_if_unsuccessful(
            martini.run_martini_formation_md(
                work_dir, design, steps, temperature_k, random_seed=random_seed
            ),
            "Martini formation MD",
        )
    return _fail_if_unsuccessful(
        lj.run_formation_md(
            work_dir,
            n_beads,
            radius_nm,
            steps,
            temperature_k,
            random_seed=random_seed,
            lipid_bead_specs=lipid_bead_specs,
        ),
        "Formation MD",
    )


def run_encapsulation_md(
    work_dir: Path,
    lipid_bead_count: int,
    drug_bead_count: int,
    steps: int,
    temperature_k: float,
    target_radius_nm: float,
    random_seed: int = 42,
    lipid_bead_specs=None,
    design: NanocarrierDesign | None = None,
) -> MDResult:
    """Encapsulation always uses LJ MD with explicit drug beads (Martini lacks drug topology)."""
    _ = design  # reserved for future Martini drug support
    return _fail_if_unsuccessful(
        lj.run_encapsulation_md(
            work_dir=work_dir,
            lipid_bead_count=lipid_bead_count,
            drug_bead_count=drug_bead_count,
            steps=steps,
            temperature_k=temperature_k,
            target_radius_nm=target_radius_nm,
            random_seed=random_seed,
            lipid_bead_specs=lipid_bead_specs,
        ),
        "Encapsulation MD",
    )


def run_thermal_stability_md(
    work_dir: Path,
    n_beads: int,
    radius_nm: float,
    steps: int,
    temperature_k: float,
    *,
    base_seed: int,
    hot_seed: int,
    design: NanocarrierDesign | None = None,
):
    if use_martini3() and design is not None and martini is not None:
        md_base = _fail_if_unsuccessful(
            martini.run_martini_formation_md(
                work_dir / "base", design, steps, temperature_k, random_seed=base_seed
            ),
            "Martini stability (base) MD",
        )
        md_hot = _fail_if_unsuccessful(
            martini.run_martini_formation_md(
                work_dir / "perturbed",
                design,
                steps,
                temperature_k + 10.0,
                random_seed=hot_seed,
            ),
            "Martini stability (perturbed) MD",
        )
        rg_base = md_base.radius_of_gyration_nm
        rg_hot = md_hot.radius_of_gyration_nm
        if rg_base is None or rg_hot is None:
            raise SimulationAnalysisError("Stability MD missing radius of gyration")
        stability = max(0.0, min(1.0, 1.0 - abs(rg_hot - rg_base) / max(rg_base, 0.01)))
        return md_base, md_hot, stability

    md_base, md_hot, stability = lj.run_thermal_stability_md(
        work_dir, n_beads, radius_nm, steps, temperature_k, base_seed=base_seed, hot_seed=hot_seed
    )
    if not md_base.success or not md_hot.success:
        raise SimulationAnalysisError(
            f"Stability MD failed: {md_base.log or md_hot.log}"
        )
    return md_base, md_hot, stability


def run_corona_adsorption_md(*args, **kwargs):
    return lj.run_corona_adsorption_md(*args, **kwargs)


def run_membrane_approach_md(*args, **kwargs):
    return lj.run_membrane_approach_md(*args, **kwargs)


def run_replicated_md(run_fn, n_replicates: int = 3):
    return lj.run_replicated_md(run_fn, n_replicates)


OPENMM_AVAILABLE = lj.OPENMM_AVAILABLE
