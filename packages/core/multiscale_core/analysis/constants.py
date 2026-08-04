"""Physical constants and literature-backed parameters — every value is traceable."""

from __future__ import annotations

# Water at 310 K (37 °C)
WATER_VISCOSITY_PA_S = 0.692e-3  # IAPWS reference
BOLTZMANN_J_K = 1.380649e-23
AVOGADRO = 6.02214076e23

# Tissue interstitial porosity (experimental ranges, used in Fickian transport)
# Sources: Netti et al. 2000 (tumor); Baxter & Jain 1989
TISSUE_POROSITY: dict[str, tuple[float, str]] = {
    "tumor": (0.35, "Netti et al., Cancer Res 2000 — interstitial porosity ~0.2–0.4"),
    "liver": (0.20, "Baxter & Jain, Microvasc Res 1989"),
    "muscle": (0.15, "Baxter & Jain, Microvasc Res 1989"),
    "brain": (0.05, "Syková & Nicholson, Physiol Rev 2008 — ECS volume fraction"),
    "skin": (0.25, "Rossi et al., J Controlled Release 2002"),
}

# Serum protein MW (Da) for coarse corona beads
SERUM_PROTEIN_MW: dict[str, float] = {
    "albumin": 66500,
    "ApoE": 34150,
    "fibrinogen": 340000,
    "IgG": 150000,
    "transferrin": 81000,
    "complement C3": 187000,
    "fetuin": 48000,
}

FLUID_PROTEINS: dict[str, list[str]] = {
    "serum": ["albumin", "ApoE", "fibrinogen", "IgG", "transferrin"],
    "plasma": ["albumin", "ApoE", "fibrinogen", "IgG", "complement C3"],
    "pbs": [],
    "cell_media": ["albumin", "fetuin"],
}
