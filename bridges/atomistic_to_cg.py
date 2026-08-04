"""Scale bridge: atomistic encapsulation results → coarse-grained LNP parameters."""

from __future__ import annotations

from multiscale_nano_core.schemas import BridgeArtifact, UncertainValue


def atomistic_to_cg(
    encapsulation_energy_kcal: float,
    residence_time_ns: float,
    source_run_id: str,
) -> BridgeArtifact:
    """Translate atomistic drug–LNP interaction into CG bead coupling parameters."""
    drug_bead_coupling = -0.8 * encapsulation_energy_kcal  # heuristic mapping
    return BridgeArtifact(
        scale="coarse_grained",
        source_modules=["drug_encapsulation"],
        fields={
            "drug_bead_coupling": UncertainValue(value=drug_bead_coupling, uncertainty=0.5, unit="kJ/mol"),
            "drug_retention_kcal_mol": UncertainValue(value=encapsulation_energy_kcal, uncertainty=1.0, unit="kcal/mol"),
            "residence_time_ns": UncertainValue(value=residence_time_ns, uncertainty=residence_time_ns * 0.2, unit="ns"),
        },
        translation_method="pmf_reweight_v1",
        valid_for=["lnp_formation", "stability"],
        metadata={"source_run_id": source_run_id},
    )
