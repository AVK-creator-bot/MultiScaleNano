"""Analysis metrics computed exclusively from MD simulation output."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class MDAnalysisResult:
    potential_energy_kj_mol: float
    radius_of_gyration_nm: float
    energy_std_kj_mol: float
    compactness: float
    drug_core_fraction: float
    steps: int
    temperature_k: float


@dataclass
class EncapsulationAnalysis:
    drug_retention_free_energy_kcal_mol: float
    encapsulation_efficiency_estimate: float
    drug_bead_coupling: float
    drug_location: str
    core_fraction: float
    md_analysis: MDAnalysisResult


def encapsulation_from_md(
    md: "MDResult",
    drug_bead_count: int,
    total_beads: int,
    drug_location: str,
) -> EncapsulationAnalysis:
    """Derive encapsulation metrics strictly from MD trajectory statistics."""

    pe_kcal = (md.potential_energy_kj_mol or 0) / 4.184
    retention_fe = pe_kcal / max(total_beads, 1)

    core_frac = md.drug_core_fraction if md.drug_core_fraction is not None else 0.0
    compactness = md.compactness or 0.0
    drug_fraction = drug_bead_count / max(total_beads, 1)

    efficiency = min(0.99, max(0.01, core_frac * compactness * (0.5 + 0.5 * drug_fraction)))
    bead_coupling = min(0.99, max(0.01, core_frac))

    md_analysis = MDAnalysisResult(
        potential_energy_kj_mol=md.potential_energy_kj_mol or 0,
        radius_of_gyration_nm=md.radius_of_gyration_nm or 0,
        energy_std_kj_mol=md.energy_std_kj_mol or 0,
        compactness=compactness,
        drug_core_fraction=core_frac,
        steps=md.steps,
        temperature_k=0,  # set by caller
    )

    return EncapsulationAnalysis(
        drug_retention_free_energy_kcal_mol=round(retention_fe, 2),
        encapsulation_efficiency_estimate=round(efficiency, 3),
        drug_bead_coupling=round(bead_coupling, 3),
        drug_location=drug_location,
        core_fraction=round(core_frac, 3),
        md_analysis=md_analysis,
    )
