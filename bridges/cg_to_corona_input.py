"""Scale bridge: assembled LNP → corona simulation inputs."""

from __future__ import annotations

from multiscale_nano_core.schemas import BridgeArtifact, UncertainValue


def cg_to_corona_input(
    hydrodynamic_radius_nm: float,
    zeta_potential_mv: float,
    surface_area_nm2: float,
    source_run_id: str,
) -> BridgeArtifact:
    """Translate CG LNP structure into corona module surface model."""
    return BridgeArtifact(
        scale="corona_input",
        source_modules=["lnp_formation", "stability"],
        fields={
            "hydrodynamic_radius_nm": UncertainValue(value=hydrodynamic_radius_nm, uncertainty=5.0, unit="nm"),
            "zeta_potential_mv": UncertainValue(value=zeta_potential_mv, uncertainty=3.0, unit="mV"),
            "surface_area_nm2": UncertainValue(value=surface_area_nm2, uncertainty=10.0, unit="nm^2"),
        },
        translation_method="geometry_projection_v1",
        valid_for=["protein_corona"],
        metadata={"source_run_id": source_run_id},
    )
