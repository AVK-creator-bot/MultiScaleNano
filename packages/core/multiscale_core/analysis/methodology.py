"""Documented analysis methodology attached to every simulation artifact."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalysisMethod(BaseModel):
    metric: str
    equation: str
    reference: str
    input_artifacts: list[str] = Field(default_factory=list)


class UncertaintyRecord(BaseModel):
    n_replicates: int
    metric: str
    mean: float
    std: float
    ci_95_low: float
    ci_95_high: float


def aggregate_replicates(values: list[float]) -> UncertaintyRecord:
    import numpy as np

    arr = np.array(values, dtype=float)
    n = len(arr)
    mean = float(arr.mean())
    std = float(arr.std(ddof=1)) if n > 1 else 0.0
    se = std / (n**0.5) if n > 1 else 0.0
    return UncertaintyRecord(
        n_replicates=n,
        metric="",
        mean=mean,
        std=std,
        ci_95_low=mean - 1.96 * se,
        ci_95_high=mean + 1.96 * se,
    )


ENCAPSULATION_METHODS = [
    AnalysisMethod(
        metric="potential_energy_kj_mol",
        equation="U = sum(LJ(r_ij)) + sum(harmonic bonds); sampled every 100 MD steps",
        reference="OpenMM LangevinMiddleIntegrator, coarse-grained LJ bead model",
        input_artifacts=[],
    ),
    AnalysisMethod(
        metric="encapsulation_efficiency_estimate",
        equation="eta = f_core * C; f_core = fraction drug beads within 0.6*Rg of COM; C = compactness",
        reference="Derived from final MD configuration geometry",
        input_artifacts=["encapsulation"],
    ),
    AnalysisMethod(
        metric="drug_retention_free_energy_kcal_mol",
        equation="delta_G approx mean(U) / N_beads converted kJ/mol to kcal/mol",
        reference="Mean potential energy per bead from production trajectory",
        input_artifacts=["encapsulation"],
    ),
]

FORMATION_METHODS = [
    AnalysisMethod(
        metric="hydrodynamic_radius_nm",
        equation="R_H approx 2 x R_g; R_g = sqrt(mean(|r_i - r_COM|^2))",
        reference="Radius of gyration from final MD configuration",
        input_artifacts=["formation"],
    ),
]

STABILITY_METHODS = [
    AnalysisMethod(
        metric="stability_score",
        equation="S = 1 - abs(R_g(T) - R_g(T+dT)) / R_g(T)",
        reference="Thermal perturbation MD — structural response to +10 K",
        input_artifacts=["formation", "stability"],
    ),
]

TRANSPORT_METHODS = [
    AnalysisMethod(
        metric="effective_diffusion_coefficient_m2_s",
        equation="D = k_B T / (6 pi eta R_H); eta = 0.692 mPa*s at 310 K",
        reference="Stokes-Einstein, Einstein 1905; R_H from formation MD",
        input_artifacts=["formation"],
    ),
    AnalysisMethod(
        metric="penetration_depth_um",
        equation="x approx sqrt(2 D epsilon t); epsilon = tissue porosity, t = 3600 s",
        reference="Fickian scaling in porous media, Baxter & Jain 1989",
        input_artifacts=["formation", "transport"],
    ),
]

RELEASE_METHODS = [
    AnalysisMethod(
        metric="half_life_hours",
        equation="t_1/2 = R_H^2 / (2 D_eff); D_eff proportional to sigma_E^2 (energy fluctuation)",
        reference="Slab diffusion model; D_eff from stability MD energy variance",
        input_artifacts=["formation", "stability", "release"],
    ),
]

CORONA_METHODS = [
    AnalysisMethod(
        metric="adsorbed_protein_count",
        equation="N_ads = count(beads with r < R_NP + 1.2 nm)",
        reference="OpenMM competitive adsorption MD in periodic box",
        input_artifacts=["formation", "corona"],
    ),
]

CELL_METHODS = [
    AnalysisMethod(
        metric="membrane_adhesion_energy_kT",
        equation="delta_G_ads = mean(U_min) / (k_B T); U from NP-membrane wall approach MD",
        reference="Harmonic membrane wall + LJ NP cluster; minimum energy approach",
        input_artifacts=["formation", "cell_interaction"],
    ),
]
