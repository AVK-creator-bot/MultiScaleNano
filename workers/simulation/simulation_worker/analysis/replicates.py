"""Run replicated MD and aggregate with uncertainty."""

from __future__ import annotations

from dataclasses import dataclass

from multiscale_core.analysis.methodology import UncertaintyRecord, aggregate_replicates

from simulation_worker.engine.openmm_md import MDResult


@dataclass
class ReplicatedMDAnalysis:
    results: list[MDResult]
    potential_energy: UncertaintyRecord
    radius_of_gyration_nm: UncertaintyRecord
    energy_std: UncertaintyRecord
    compactness: UncertaintyRecord

    @property
    def primary(self) -> MDResult:
        return self.results[0]

    @property
    def all_success(self) -> bool:
        return all(r.success for r in self.results)


def analyze_replicates(results: list[MDResult]) -> ReplicatedMDAnalysis:
    pes = [r.potential_energy_kj_mol for r in results if r.potential_energy_kj_mol is not None]
    rgs = [r.radius_of_gyration_nm for r in results if r.radius_of_gyration_nm is not None]
    stds = [r.energy_std_kj_mol for r in results if r.energy_std_kj_mol is not None]
    comps = [r.compactness for r in results if r.compactness is not None]

    pe_u = aggregate_replicates(pes)
    pe_u.metric = "potential_energy_kj_mol"
    rg_u = aggregate_replicates(rgs)
    rg_u.metric = "radius_of_gyration_nm"
    std_u = aggregate_replicates(stds)
    std_u.metric = "energy_std_kj_mol"
    comp_u = aggregate_replicates(comps)
    comp_u.metric = "compactness"

    return ReplicatedMDAnalysis(
        results=results,
        potential_energy=pe_u,
        radius_of_gyration_nm=rg_u,
        energy_std=std_u,
        compactness=comp_u,
    )
