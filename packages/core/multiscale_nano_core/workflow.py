"""Workflow DAG definitions — which modules run, in what order."""

from __future__ import annotations

from multiscale_nano_core.schemas import PipelineModule


LNP_MVP_PIPELINE: list[dict] = [
    {
        "id": "drug_encapsulation",
        "name": "Drug Encapsulation",
        "description": "How well does the drug physically fit inside this LNP?",
        "engine": "gromacs",
        "depends_on": [],
    },
    {
        "id": "lnp_formation",
        "name": "LNP Self-Assembly",
        "description": "Simulate lipid self-assembly and drug incorporation.",
        "engine": "gromacs_martini",
        "depends_on": ["drug_encapsulation"],
    },
    {
        "id": "stability",
        "name": "Environmental Stability",
        "description": "Predict aggregation, leakage, and structural changes under biological conditions.",
        "engine": "gromacs_martini",
        "depends_on": ["lnp_formation"],
    },
    {
        "id": "protein_corona",
        "name": "Protein Corona",
        "description": "Which proteins bind, and how does the corona alter the particle?",
        "engine": "corona_kmc",
        "depends_on": ["stability"],
    },
    {
        "id": "membrane_interaction",
        "name": "Cell Membrane Interaction",
        "description": "Membrane binding, uptake, and endosomal trafficking.",
        "engine": "gromacs_martini",
        "depends_on": ["protein_corona"],
    },
    {
        "id": "tissue_transport",
        "name": "Tissue Transport",
        "description": "Diffusion and penetration through target tissue.",
        "engine": "continuum",
        "depends_on": ["membrane_interaction"],
    },
    {
        "id": "drug_release",
        "name": "Drug Release",
        "description": "When and where does the drug leave the carrier?",
        "engine": "hybrid",
        "depends_on": ["stability", "tissue_transport"],
    },
]


def build_pipeline(module_defs: list[dict] | None = None) -> list[PipelineModule]:
    """Instantiate pipeline modules from definitions."""
    defs = module_defs or LNP_MVP_PIPELINE
    return [PipelineModule(**d) for d in defs]


def get_ready_modules(modules: list[PipelineModule]) -> list[PipelineModule]:
    """Return modules whose dependencies are all completed."""
    completed = {m.id for m in modules if m.status.value == "completed"}
    ready = []
    for mod in modules:
        if mod.status.value != "pending":
            continue
        if all(dep in completed for dep in mod.depends_on):
            ready.append(mod)
    return ready
