"""Literature-backed lipid parameters for coarse-grained LNP modeling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from multiscale_core.schema.drug import PayloadType
from multiscale_core.schema.nanocarrier import LipidComponent

if TYPE_CHECKING:
    from multiscale_core.schema.nanocarrier import NanocarrierDesign


@dataclass(frozen=True)
class LipidParams:
    name: str
    molecular_weight: float
    charge: int
    epsilon_kj_mol: float
    bead_mass_amu: float
    category: str


# Martini-inspired relative interaction strengths (coarse-grained mapping)
LIPID_LIBRARY: dict[str, LipidParams] = {
    "SM-102": LipidParams("SM-102", 710.0, 1, 2.6, 120.0, "ionizable"),
    "ALC-0315": LipidParams("ALC-0315", 766.0, 1, 2.6, 125.0, "ionizable"),
    "DLin-MC3-DMA": LipidParams("DLin-MC3-DMA", 642.0, 1, 2.5, 110.0, "ionizable"),
    "DSPC": LipidParams("DSPC", 790.0, 0, 1.9, 130.0, "phospholipid"),
    "DOPC": LipidParams("DOPC", 786.0, 0, 1.9, 130.0, "phospholipid"),
    "DOPE": LipidParams("DOPE", 744.0, 0, 1.8, 125.0, "phospholipid"),
    "Cholesterol": LipidParams("Cholesterol", 387.0, 0, 1.4, 65.0, "sterol"),
    "DSPE-PEG2000": LipidParams("DSPE-PEG2000", 2805.0, 0, 1.2, 200.0, "pegylated"),
    "DSPE-PEG5000": LipidParams("DSPE-PEG2000", 5000.0, 0, 1.0, 350.0, "pegylated"),
}

# Clinical / literature LNP formulations (mol fractions sum to 1.0)
LIPID_PRESETS: dict[str, list[LipidComponent]] = {
    "mrna_comirnaty_style": [
        LipidComponent(name="ALC-0315", ratio=0.43, charge=1),
        LipidComponent(name="DSPC", ratio=0.10, charge=0),
        LipidComponent(name="Cholesterol", ratio=0.435, charge=0),
        LipidComponent(name="DSPE-PEG2000", ratio=0.035, charge=0),
    ],
    "mrna_sm102": [
        LipidComponent(name="SM-102", ratio=0.50, charge=1),
        LipidComponent(name="DSPC", ratio=0.10, charge=0),
        LipidComponent(name="Cholesterol", ratio=0.385, charge=0),
        LipidComponent(name="DSPE-PEG2000", ratio=0.015, charge=0),
    ],
    "sirna_mcq": [
        LipidComponent(name="DLin-MC3-DMA", ratio=0.45, charge=1),
        LipidComponent(name="DSPC", ratio=0.10, charge=0),
        LipidComponent(name="Cholesterol", ratio=0.40, charge=0),
        LipidComponent(name="DSPE-PEG2000", ratio=0.05, charge=0),
    ],
    "small_molecule": [
        LipidComponent(name="DLin-MC3-DMA", ratio=0.45, charge=1),
        LipidComponent(name="DSPC", ratio=0.10, charge=0),
        LipidComponent(name="Cholesterol", ratio=0.40, charge=0),
        LipidComponent(name="DSPE-PEG2000", ratio=0.05, charge=0),
    ],
}


def lipid_params(name: str) -> LipidParams:
    if name in LIPID_LIBRARY:
        return LIPID_LIBRARY[name]
    return LipidParams(name, 700.0, 0, 1.8, 100.0, "unknown")


def validate_lipid_composition(lipids: list[LipidComponent]) -> tuple[bool, str]:
    if not lipids:
        return False, "At least one lipid component is required"
    total = sum(l.ratio for l in lipids)
    if abs(total - 1.0) > 0.02:
        return False, f"Lipid molar fractions must sum to 100% (currently {total * 100:.1f}%)"
    for l in lipids:
        if l.ratio < 0 or l.ratio > 1:
            return False, f"Invalid ratio for {l.name}"
    return True, ""


def preset_for_payload(payload_type: PayloadType) -> list[LipidComponent]:
    if payload_type in (PayloadType.MRNA,):
        return [LipidComponent(**c.model_dump()) for c in LIPID_PRESETS["mrna_sm102"]]
    if payload_type in (PayloadType.SIRNA,):
        return [LipidComponent(**c.model_dump()) for c in LIPID_PRESETS["sirna_mcq"]]
    return [LipidComponent(**c.model_dump()) for c in LIPID_PRESETS["small_molecule"]]


def lipid_bead_counts(design: NanocarrierDesign, total_lipid_beads: int = 40) -> list[tuple[str, int, LipidParams]]:
    """Allocate coarse-grained beads by molar ratio."""
    counts: list[tuple[str, int, LipidParams]] = []
    remaining = total_lipid_beads
    for i, lipid in enumerate(design.lipids):
        params = lipid_params(lipid.name)
        if i == len(design.lipids) - 1:
            n = max(1, remaining)
        else:
            n = max(1, int(round(total_lipid_beads * lipid.ratio)))
            remaining -= n
        counts.append((lipid.name, n, params))
    return counts


def drug_bead_count_from_loading(
    design: NanocarrierDesign,
    resolved_mw: float,
    resolved_min_beads: int,
    lipid_bead_total: int,
) -> int:
    """Map wt% loading to drug bead count using mass balance."""
    loading = design.drug.loading_pct / 100.0
    avg_lipid_mw = sum(lipid_params(l.name).molecular_weight * l.ratio for l in design.lipids)
    # mass_drug / mass_lipid = loading / (1 - loading)
    if loading <= 0:
        return max(2, resolved_min_beads)
    mass_ratio = loading / max(1e-6, 1.0 - loading)
    lipid_mass_beads = lipid_bead_total * avg_lipid_mw
    drug_mass = lipid_mass_beads * mass_ratio
    beads_from_loading = max(2, int(round(drug_mass / max(resolved_mw, 1.0) * 2)))
    return max(resolved_min_beads, beads_from_loading)
