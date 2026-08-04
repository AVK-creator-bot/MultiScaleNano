"""Resolve drug structures from SMILES, sequences, PubChem, PDB for simulation."""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

from multiscale_core.schema.drug import (
    DrugPayload,
    PayloadType,
    ResolvedDrugStructure,
    StructureSourceType,
)

# Average molecular weights (Da) for nucleotides and amino acids
RNA_MW_PER_BASE = 330.0
DNA_MW_PER_BASE = 330.0
AA_MW_AVG = 110.0

PUBCHEM_SMILES_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/CanonicalSMILES,MolecularWeight/JSON"
RCSB_PDB_URL = "https://files.rcsb.org/download/{pdb_id}.pdb"


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "MultiscaleNano/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        import json

        return json.loads(resp.read().decode())


def _fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "MultiscaleNano/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode()


def _count_pdb_heavy_atoms(pdb_text: str) -> int:
    return sum(1 for line in pdb_text.splitlines() if line.startswith(("ATOM  ", "HETATM")))


def _estimate_beads(heavy_atoms: int, payload_type: PayloadType, seq_len: int | None) -> int:
    if payload_type in (PayloadType.MRNA, PayloadType.SIRNA) and seq_len:
        return max(3, seq_len // 3)  # one bead per codon / ~3 nt
    if payload_type == PayloadType.PEPTIDE and seq_len:
        return max(3, seq_len // 2)
    if payload_type == PayloadType.PROTEIN:
        return max(5, heavy_atoms // 10)
    return max(3, min(20, heavy_atoms // 2))


def resolve_drug_structure(drug: DrugPayload, work_dir: Path) -> ResolvedDrugStructure:
    """Resolve user input to a simulation-ready structure. Raises ValueError if invalid."""
    log: list[str] = []
    work_dir.mkdir(parents=True, exist_ok=True)

    src_type = drug.structure_source_type
    src_val = (drug.structure_value or drug.smiles or "").strip()
    if not src_val:
        raise ValueError(
            "Drug structure is required. Provide SMILES, sequence, PubChem CID, or PDB ID."
        )

    mw = drug.molecular_weight
    heavy_atoms = 0
    seq_len: int | None = None
    pdb_path: str | None = None
    smiles_canonical: str | None = None

    if src_type == StructureSourceType.PUBCHEM:
        cid = re.sub(r"[^0-9]", "", src_val)
        if not cid:
            raise ValueError(f"Invalid PubChem CID: {src_val}")
        log.append(f"Fetching PubChem CID {cid}")
        data = _fetch_json(PUBCHEM_SMILES_URL.format(cid=cid))
        props = data["PropertyTable"]["Properties"][0]
        smiles_canonical = (
            props.get("CanonicalSMILES")
            or props.get("IsomericSMILES")
            or props.get("ConnectivitySMILES")
        )
        if not smiles_canonical:
            raise ValueError(f"PubChem CID {cid} returned no SMILES")
        mw = float(props.get("MolecularWeight", 0))
        log.append(f"PubChem resolved: MW={mw:.1f} Da")
        src_val = smiles_canonical
        src_type = StructureSourceType.SMILES

    if src_type == StructureSourceType.PDB:
        pdb_id = src_val.upper().replace("PDB:", "").strip()[:4]
        log.append(f"Downloading PDB {pdb_id}")
        pdb_text = _fetch_text(RCSB_PDB_URL.format(pdb_id=pdb_id))
        pdb_file = work_dir / f"{pdb_id}.pdb"
        pdb_file.write_text(pdb_text, encoding="utf-8")
        pdb_path = str(pdb_file)
        heavy_atoms = _count_pdb_heavy_atoms(pdb_text)
        if mw is None:
            mw = heavy_atoms * 7.5  # rough Da per heavy atom
        log.append(f"PDB loaded: {heavy_atoms} atoms")

    elif src_type == StructureSourceType.URL:
        log.append(f"Fetching structure URL: {src_val}")
        content = _fetch_text(src_val)
        if "ATOM" in content or "HETATM" in content:
            pdb_file = work_dir / "structure.pdb"
            pdb_file.write_text(content, encoding="utf-8")
            pdb_path = str(pdb_file)
            heavy_atoms = _count_pdb_heavy_atoms(content)
            if mw is None:
                mw = heavy_atoms * 7.5
        else:
            raise ValueError("URL did not return a recognizable PDB structure")

    elif src_type == StructureSourceType.SEQUENCE:
        seq = re.sub(r"\s+", "", src_val.upper())
        if not re.match(r"^[ACGTUN]+$", seq) and drug.payload_type in (
            PayloadType.MRNA,
            PayloadType.SIRNA,
        ):
            raise ValueError("RNA/DNA sequence must contain only A,C,G,T,U,N")
        if not re.match(r"^[ACDEFGHIKLMNPQRSTVWYX*]+$", seq) and drug.payload_type in (
            PayloadType.PEPTIDE,
            PayloadType.PROTEIN,
        ):
            raise ValueError("Protein/peptide sequence must be valid amino acid letters")

        seq_len = len(seq)
        if drug.payload_type in (PayloadType.MRNA, PayloadType.SIRNA):
            mw = seq_len * RNA_MW_PER_BASE
        else:
            mw = seq_len * AA_MW_AVG
        heavy_atoms = seq_len * 2
        log.append(f"Sequence length {seq_len}, estimated MW={mw:.0f} Da")

    elif src_type == StructureSourceType.SMILES:
        smiles_canonical = src_val
        log.append("Parsing SMILES")
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors

            mol = Chem.MolFromSmiles(smiles_canonical)
            if mol is None:
                raise ValueError(f"Invalid SMILES: {smiles_canonical}")
            smiles_canonical = Chem.MolToSmiles(mol)
            mw = Descriptors.MolWt(mol)
            heavy_atoms = mol.GetNumHeavyAtoms()
            log.append(f"RDKit: MW={mw:.2f} Da, {heavy_atoms} heavy atoms")
        except ImportError:
            if mw is None:
                mw = max(100.0, len(smiles_canonical) * 8.0)
            heavy_atoms = max(5, len(re.findall(r"[A-Z]", smiles_canonical)))
            log.append("RDKit unavailable — using SMILES length estimate (install rdkit for accuracy)")

    if mw is None:
        raise ValueError("Could not determine molecular weight — provide MW or valid structure")

    bead_count = _estimate_beads(heavy_atoms, drug.payload_type, seq_len)

    return ResolvedDrugStructure(
        name=drug.name,
        payload_type=drug.payload_type,
        source_type=drug.structure_source_type,
        source_value=drug.structure_value,
        molecular_weight=mw,
        heavy_atom_count=heavy_atoms,
        bead_count=bead_count,
        sequence_length=seq_len,
        pdb_path=pdb_path,
        smiles_canonical=smiles_canonical,
        resolution_log=log,
    )
