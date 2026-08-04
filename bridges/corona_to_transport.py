"""Scale bridge: corona-modified NP → effective transport properties."""

from __future__ import annotations

from multiscale_nano_core.schemas import BridgeArtifact, UncertainValue


def corona_to_transport(
    effective_radius_nm: float,
    effective_charge_mv: float,
    ligand_accessible_fraction: float,
    leakage_rate_per_h: float,
    source_run_id: str,
) -> BridgeArtifact:
    """Translate corona state into continuum transport parameters."""
    # Stokes-Einstein diffusion estimate (water, 310K)
    radius_m = effective_radius_nm * 1e-9
    diffusion_m2_s = 1.38e-23 * 310 / (6 * 3.14159 * 1e-3 * radius_m)
    diffusion_um2_s = diffusion_m2_s * 1e12

    return BridgeArtifact(
        scale="continuum",
        source_modules=["protein_corona", "stability"],
        fields={
            "effective_radius_nm": UncertainValue(value=effective_radius_nm, uncertainty=8.0, unit="nm"),
            "effective_charge_mv": UncertainValue(value=effective_charge_mv, uncertainty=5.0, unit="mV"),
            "ligand_accessible_fraction": UncertainValue(value=ligand_accessible_fraction, uncertainty=0.1, unit=""),
            "diffusion_coefficient": UncertainValue(value=diffusion_um2_s, uncertainty=diffusion_um2_s * 0.15, unit="um^2/s"),
            "leakage_rate": UncertainValue(value=leakage_rate_per_h, uncertainty=leakage_rate_per_h * 0.2, unit="1/h"),
        },
        translation_method="corona_effective_v1",
        valid_for=["tissue_transport", "drug_release"],
        metadata={"source_run_id": source_run_id},
    )
