"""Simulation module definitions and workflow DAG."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from multiscale_core.schema.simulation import SimulationMode, estimate_wall_clock_min, format_runtime


class SimulationScale(str, Enum):
    ATOMISTIC = "atomistic"
    COARSE_GRAINED = "coarse_grained"
    MESOSCALE = "mesoscale"
    CONTINUUM = "continuum"


class ModuleName(str, Enum):
    ENCAPSULATION = "encapsulation"
    FORMATION = "formation"
    STABILITY = "stability"
    CORONA = "corona"
    CELL_INTERACTION = "cell_interaction"
    TRANSPORT = "transport"
    RELEASE = "release"


class ModuleSpec(BaseModel):
    """Metadata for a simulation module."""

    name: ModuleName
    label: str
    description: str
    question: str
    scale: SimulationScale
    engine: str
    estimated_runtime_min: int
    depends_on: list[ModuleName] = Field(default_factory=list)
    enabled_by_default: bool = True


MODULE_REGISTRY: dict[ModuleName, ModuleSpec] = {
    ModuleName.ENCAPSULATION: ModuleSpec(
        name=ModuleName.ENCAPSULATION,
        label="Drug Encapsulation",
        description="Simulate drug–lipid interactions and loading efficiency",
        question="How well does this nanocarrier physically accommodate the drug?",
        scale=SimulationScale.COARSE_GRAINED,
        engine="openmm",
        estimated_runtime_min=120,
        depends_on=[],
        enabled_by_default=True,
    ),
    ModuleName.FORMATION: ModuleSpec(
        name=ModuleName.FORMATION,
        label="Nanoparticle Formation",
        description="Coarse-grained self-assembly of the lipid nanoparticle",
        question="How does the nanoparticle actually form?",
        scale=SimulationScale.COARSE_GRAINED,
        engine="openmm",
        estimated_runtime_min=240,
        depends_on=[ModuleName.ENCAPSULATION],
        enabled_by_default=True,
    ),
    ModuleName.STABILITY: ModuleSpec(
        name=ModuleName.STABILITY,
        label="Environmental Stability",
        description="Test aggregation, degradation, and drug leakage under biological conditions",
        question="Will my nanocarrier remain stable?",
        scale=SimulationScale.COARSE_GRAINED,
        engine="openmm",
        estimated_runtime_min=360,
        depends_on=[ModuleName.FORMATION],
        enabled_by_default=True,
    ),
    ModuleName.CORONA: ModuleSpec(
        name=ModuleName.CORONA,
        label="Protein Corona",
        description="Predict protein adsorption in biological fluids",
        question="Which proteins bind, and does the corona change the particle's identity?",
        scale=SimulationScale.MESOSCALE,
        engine="openmm",
        estimated_runtime_min=180,
        depends_on=[ModuleName.FORMATION],
        enabled_by_default=False,
    ),
    ModuleName.CELL_INTERACTION: ModuleSpec(
        name=ModuleName.CELL_INTERACTION,
        label="Cell Interaction",
        description="Model membrane binding, uptake, and endosomal trafficking",
        question="What happens when the nanoparticle encounters a cell?",
        scale=SimulationScale.COARSE_GRAINED,
        engine="openmm",
        estimated_runtime_min=480,
        depends_on=[ModuleName.FORMATION],
        enabled_by_default=False,
    ),
    ModuleName.TRANSPORT: ModuleSpec(
        name=ModuleName.TRANSPORT,
        label="Tissue Transport",
        description="Continuum model of interstitial diffusion and penetration",
        question="How does the nanoparticle move through biological tissue?",
        scale=SimulationScale.CONTINUUM,
        engine="stokes-einstein",
        estimated_runtime_min=1,
        depends_on=[ModuleName.FORMATION],
        enabled_by_default=True,
    ),
    ModuleName.RELEASE: ModuleSpec(
        name=ModuleName.RELEASE,
        label="Drug Release",
        description="Predict time- and location-dependent drug release profiles",
        question="When and where does the drug actually leave the nanoparticle?",
        scale=SimulationScale.CONTINUUM,
        engine="stokes-einstein",
        estimated_runtime_min=1,
        depends_on=[ModuleName.STABILITY],
        enabled_by_default=True,
    ),
}


class WorkflowNode(BaseModel):
    module: ModuleName
    spec: ModuleSpec
    upstream: list[ModuleName]


class WorkflowPlan(BaseModel):
    """Ordered DAG of simulation modules for a given design."""

    modules: list[WorkflowNode]
    estimated_total_min: int
    estimated_display: str
    simulation_mode: SimulationMode

    def module_names(self) -> list[ModuleName]:
        return [node.module for node in self.modules]


def plan_lnp_workflow(
    enabled: list[ModuleName] | None = None,
    mode: SimulationMode = SimulationMode.STANDARD_MD,
) -> WorkflowPlan:
    """Build the default LNP simulation pipeline."""

    if enabled is None:
        enabled = [m for m, spec in MODULE_REGISTRY.items() if spec.enabled_by_default]

    # Topological sort respecting dependencies
    ordered: list[ModuleName] = []
    remaining = set(enabled)

    while remaining:
        ready = [
            m
            for m in remaining
            if all(dep in ordered or dep not in enabled for dep in MODULE_REGISTRY[m].depends_on)
        ]
        if not ready:
            raise ValueError(f"Circular or unsatisfiable dependencies: {remaining}")
        ready.sort(key=lambda m: (len(MODULE_REGISTRY[m].depends_on), m.value))
        ordered.extend(ready)
        remaining -= set(ready)

    nodes = [
        WorkflowNode(
            module=m,
            spec=MODULE_REGISTRY[m],
            upstream=[d for d in MODULE_REGISTRY[m].depends_on if d in enabled],
        )
        for m in ordered
    ]

    total = estimate_wall_clock_min(ordered, mode)
    return WorkflowPlan(
        modules=nodes,
        estimated_total_min=total,
        estimated_display=format_runtime(total),
        simulation_mode=mode,
    )
