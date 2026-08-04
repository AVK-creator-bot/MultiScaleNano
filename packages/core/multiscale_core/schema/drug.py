"""Drug payload types and structure identifiers."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PayloadType(str, Enum):
    SMALL_MOLECULE = "small_molecule"
    MRNA = "mrna"
    SIRNA = "sirna"
    PEPTIDE = "peptide"
    PROTEIN = "protein"


class StructureSourceType(str, Enum):
    SMILES = "smiles"
    SEQUENCE = "sequence"
    PUBCHEM = "pubchem"
    PDB = "pdb"
    URL = "url"


class DrugPayload(BaseModel):
    """Drug cargo — requires a resolvable structure for simulation."""

    name: str
    payload_type: PayloadType = PayloadType.SMALL_MOLECULE
    structure_source_type: StructureSourceType = StructureSourceType.SMILES
    structure_value: str = Field(
        description="SMILES, nucleotide/protein sequence, PubChem CID, PDB ID, or structure URL",
    )
    molecular_weight: float | None = None
    loading_pct: float = Field(default=5, ge=0, le=50, description="Drug wt% of total NP")
    encapsulation_mode: Literal["core", "membrane", "surface"] = "core"

    # Legacy fields kept for backward compatibility
    smiles: str = ""

    @model_validator(mode="after")
    def sync_legacy_smiles(self) -> DrugPayload:
        if self.structure_source_type == StructureSourceType.SMILES and self.structure_value:
            object.__setattr__(self, "smiles", self.structure_value)
        elif self.smiles and not self.structure_value:
            object.__setattr__(self, "structure_value", self.smiles)
            object.__setattr__(self, "structure_source_type", StructureSourceType.SMILES)
        cap = self.max_loading_pct()
        if self.loading_pct > cap:
            raise ValueError(
                f"Drug loading {self.loading_pct}% exceeds maximum {cap}% for {self.payload_type.value}"
            )
        if not (self.structure_value or self.smiles):
            raise ValueError("structure_value is required (SMILES, sequence, PubChem CID, or PDB ID)")
        return self

    def max_loading_pct(self) -> float:
        limits = {
            PayloadType.SMALL_MOLECULE: 50.0,
            PayloadType.PEPTIDE: 25.0,
            PayloadType.MRNA: 15.0,
            PayloadType.SIRNA: 12.0,
            PayloadType.PROTEIN: 10.0,
        }
        return limits.get(self.payload_type, 50.0)


class ResolvedDrugStructure(BaseModel):
    """Output of structure resolution — feeds MD engines."""

    name: str
    payload_type: PayloadType
    source_type: StructureSourceType
    source_value: str
    molecular_weight: float
    heavy_atom_count: int
    bead_count: int
    sequence_length: int | None = None
    pdb_path: str | None = None
    smiles_canonical: str | None = None
    resolution_log: list[str] = Field(default_factory=list)
