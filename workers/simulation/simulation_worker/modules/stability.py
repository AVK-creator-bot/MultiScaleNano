"""Stability module — thermal perturbation MD from formation geometry."""

from __future__ import annotations

from uuid import UUID

from multiscale_core.analysis.methodology import STABILITY_METHODS, aggregate_replicates
from multiscale_core.paths import ARTIFACT_DIR
from multiscale_core.simulation.seeds import run_seed
from multiscale_core.schema.artifacts import ArtifactFile, ProvenanceRecord, ScaleArtifact, StabilityResult
from multiscale_core.schema.nanocarrier import NanocarrierDesign
from multiscale_core.schema.simulation import SimulationMode
from multiscale_core.schema.workflow import ModuleName, SimulationScale

from simulation_worker.analysis.artifact_meta import enrich_artifact_data
from simulation_worker.engine.md_dispatch import (
    force_field_from_engine,
    md_steps_for_mode,
    replicate_count_for_mode,
    run_replicated_md,
    run_thermal_stability_md,
)
from simulation_worker.modules.errors import SimulationAnalysisError
from simulation_worker.structure.export import export_md_structure


def run_stability(
    run_id: str,
    design: NanocarrierDesign,
    upstream: dict,
    *,
    mode: SimulationMode = SimulationMode.STANDARD_MD,
) -> ScaleArtifact:
    work_dir = ARTIFACT_DIR / run_id / "stability"
    work_dir.mkdir(parents=True, exist_ok=True)

    steps = md_steps_for_mode(mode.value)
    n_rep = replicate_count_for_mode(mode.value)
    if mode == SimulationMode.SCREENING or steps <= 0:
        raise SimulationAnalysisError("Stability requires MD simulation.")

    radius_nm = design.target_size_nm / 2
    n_beads = max(20, int(radius_nm * 4))
    if "formation" in upstream:
        radius_nm = upstream["formation"].data.get("hydrodynamic_radius_nm", radius_nm * 2) / 2
        n_beads = max(20, int(radius_nm * 4))

    def _one(replicate: int):
        return run_thermal_stability_md(
            work_dir / f"rep_{replicate}",
            n_beads=n_beads,
            radius_nm=radius_nm,
            steps=steps,
            temperature_k=design.environment.temperature_k,
            base_seed=run_seed(run_id, "stability", replicate),
            hot_seed=run_seed(run_id, "stability_hot", replicate),
            design=design,
        )

    rep_results = run_replicated_md(_one, n_rep)
    stability_scores = []
    leakage_rates = []
    base_md = None
    hot_md = None
    for md_base, md_hot, stability in rep_results:
        if not md_base.success or not md_hot.success:
            raise SimulationAnalysisError(f"Stability MD failed: {md_base.log or md_hot.log}")
        stability_scores.append(stability)
        base_md = md_base
        hot_md = md_hot
        energy_cv = (md_base.energy_std_kj_mol or 0) / max(abs(md_base.potential_energy_kj_mol or 1), 1)
        leakage_rates.append(min(0.2, max(0.001, energy_cv * 0.05)))

    stab_u = aggregate_replicates(stability_scores)
    stab_u.metric = "stability_score"
    leak_u = aggregate_replicates(leakage_rates)
    leak_u.metric = "drug_leakage_rate_per_hour"

    stability = stab_u.mean
    aggregation = max(0.05, 1.0 - stability)
    leakage = leak_u.mean

    ionizable = sum(l.ratio for l in design.lipids if l.charge != 0)
    ph_low, ph_high = (5.5, 7.4) if ionizable > 0.2 else (6.5, 8.0)

    result = StabilityResult(
        stability_score=round(stability, 3),
        aggregation_propensity=round(aggregation, 3),
        drug_leakage_rate_per_hour=round(leakage, 4),
        stable_ph_range=(ph_low, ph_high),
    )

    structure = {}
    if hot_md:
        structure = export_md_structure(
            work_dir,
            hot_md,
            ["lipid"] * len(hot_md.final_positions_nm or []),
            title=f"Thermal stress (+10 K) — {design.name}",
        )

    data = enrich_artifact_data(
        {
            **result.model_dump(),
            "simulation_mode": mode.value,
            "md_steps": steps,
            "n_replicates": n_rep,
            "thermal_perturbation_k": 10.0,
            "base_rg_nm": base_md.radius_of_gyration_nm if base_md else None,
            "energy_std_kj_mol": base_md.energy_std_kj_mol if base_md else None,
            "structure": structure,
        },
        STABILITY_METHODS,
        uncertainty={"stability_score": stab_u, "drug_leakage_rate_per_hour": leak_u},
    )

    artifact = ScaleArtifact(
        run_id=UUID(run_id),
        module=ModuleName.STABILITY,
        scale=SimulationScale.COARSE_GRAINED,
        data=data,
        uncertainty={"stability_score": stab_u.model_dump(), "drug_leakage_rate_per_hour": leak_u.model_dump()},
        provenance=ProvenanceRecord(
            upstream_artifacts=[upstream["formation"].id] if "formation" in upstream else [],
            force_field=force_field_from_engine(base_md.engine if base_md else None),
            engine_version=base_md.engine if base_md else "openmm",
            translation_method="thermal_perturbation_md",
        ),
        files=(
            [ArtifactFile(path="structure.pdb", file_type="pdb", description="Final MD bead coordinates after +10 K")]
            if structure.get("available")
            else []
        ),
    )

    (work_dir / "artifact.json").write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    return artifact
