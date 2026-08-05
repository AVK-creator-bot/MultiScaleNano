"""Route MD jobs to Martini 3 or legacy LJ backend."""

from __future__ import annotations

from pathlib import Path

from multiscale_core.schema.nanocarrier import NanocarrierDesign
from multiscale_core.simulation.force_field import prefer_martini3, provenance_force_field

from simulation_worker.engine import openmm_md as lj
from simulation_worker.engine.openmm_md import MDResult

MARTINI_AVAILABLE = False
try:
    from simulation_worker.engine import martini_md as martini

    MARTINI_AVAILABLE = martini.MARTINI_AVAILABLE
except ImportError:
    martini = None  # type: ignore


def use_martini3() -> bool:
    return prefer_martini3() and MARTINI_AVAILABLE and martini is not None


def active_force_field() -> str:
    return provenance_force_field(use_martini3())


def force_field_from_engine(engine: str | None) -> str:
    if engine and engine.startswith("martini"):
        return "martini3"
    return "lj_coarse_grained"


def md_steps_for_mode(mode: str) -> int:
    if use_martini3() and martini is not None:
        return martini.md_steps_for_martini(mode)
    return lj.md_steps_for_mode(mode)


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
        try:
            return martini.run_martini_formation_md(
                work_dir, design, steps, temperature_k, random_seed=random_seed
            )
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(
                "Martini formation MD failed, using LJ fallback: %s", exc
            )
    return lj.run_formation_md(
        work_dir, n_beads, radius_nm, steps, temperature_k,
        random_seed=random_seed, lipid_bead_specs=lipid_bead_specs,
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
    if use_martini3() and design is not None and martini is not None:
        try:
            return martini.run_martini_encapsulation_md(
                work_dir, design, steps, temperature_k, random_seed=random_seed
            )
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(
                "Martini encapsulation MD failed, using LJ fallback: %s", exc
            )
    return lj.run_encapsulation_md(
        work_dir=work_dir,
        lipid_bead_count=lipid_bead_count,
        drug_bead_count=drug_bead_count,
        steps=steps,
        temperature_k=temperature_k,
        target_radius_nm=target_radius_nm,
        random_seed=random_seed,
        lipid_bead_specs=lipid_bead_specs,
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
        try:
            md_base = martini.run_martini_formation_md(
                work_dir / "base", design, steps, temperature_k, random_seed=base_seed
            )
            md_hot = martini.run_martini_formation_md(
                work_dir / "perturbed", design, steps, temperature_k + 10.0, random_seed=hot_seed
            )
            if md_base.success and md_hot.success:
                rg_base = md_base.radius_of_gyration_nm or 1.0
                rg_hot = md_hot.radius_of_gyration_nm or rg_base
                stability = max(0.0, min(1.0, 1.0 - abs(rg_hot - rg_base) / max(rg_base, 0.01)))
                return md_base, md_hot, stability
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(
                "Martini stability MD failed, using LJ fallback: %s", exc
            )
    return lj.run_thermal_stability_md(
        work_dir, n_beads, radius_nm, steps, temperature_k,
        base_seed=base_seed, hot_seed=hot_seed,
    )


def run_corona_adsorption_md(*args, **kwargs):
    return lj.run_corona_adsorption_md(*args, **kwargs)


def run_membrane_approach_md(*args, **kwargs):
    return lj.run_membrane_approach_md(*args, **kwargs)


def run_replicated_md(run_fn, n_replicates: int = 3):
    return lj.run_replicated_md(run_fn, n_replicates)


replicate_count_for_mode = lj.replicate_count_for_mode
OPENMM_AVAILABLE = lj.OPENMM_AVAILABLE
