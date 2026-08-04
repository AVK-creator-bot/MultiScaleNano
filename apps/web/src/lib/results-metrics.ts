/** Display definitions for simulation module outputs. */

export interface UncertaintyRecord {
  n_replicates?: number;
  metric?: string;
  mean?: number;
  std?: number;
  ci_95_low?: number;
  ci_95_high?: number;
}

export interface AnalysisMethod {
  metric: string;
  equation: string;
  reference: string;
}

export interface ModuleArtifact {
  module?: string;
  data: Record<string, unknown>;
  uncertainty?: Record<string, UncertaintyRecord>;
  provenance?: Record<string, unknown>;
}

export interface MetricDef {
  key: string;
  label: string;
  unit?: string;
  format?: (v: unknown) => string;
}

const pct = (v: unknown) => `${((v as number) * 100).toFixed(1)}%`;
const num = (d: number) => (v: unknown) => (v as number).toFixed(d);
const nm = (v: unknown) => `${v} nm`;
const um = (v: unknown) => `${v} µm`;
const hrs = (v: unknown) => `${v} hrs`;
const kT = (v: unknown) => `${(v as number).toFixed(2)} kT`;

export const MODULE_METRICS: Record<string, MetricDef[]> = {
  encapsulation: [
    { key: "encapsulation_efficiency_estimate", label: "Encapsulation efficiency", format: pct },
    { key: "drug_retention_free_energy_kcal_mol", label: "Drug retention ΔG", unit: "kcal/mol", format: num(2) },
    { key: "potential_energy_kj_mol", label: "Potential energy", unit: "kJ/mol", format: num(1) },
    { key: "radius_of_gyration_nm", label: "Radius of gyration", format: nm },
  ],
  formation: [
    { key: "hydrodynamic_radius_nm", label: "Hydrodynamic radius", format: nm },
    { key: "morphology", label: "Morphology" },
    { key: "polydispersity", label: "Polydispersity", format: num(3) },
    { key: "drug_core_fraction", label: "Drug core fraction", format: pct },
  ],
  stability: [
    { key: "stability_score", label: "Stability score", format: pct },
    { key: "drug_leakage_rate_per_hour", label: "Drug leakage rate", unit: "/hr", format: num(4) },
    { key: "aggregation_propensity", label: "Aggregation propensity", format: pct },
  ],
  corona: [
    { key: "adsorbed_protein_count", label: "Adsorbed proteins", format: num(0) },
    { key: "effective_radius_nm", label: "Effective radius", format: nm },
    { key: "ligand_accessible_fraction", label: "Ligand accessibility", format: pct },
    { key: "surface_charge_delta_mv", label: "Surface charge shift", unit: "mV", format: num(1) },
  ],
  cell_interaction: [
    { key: "membrane_adhesion_energy_kT", label: "Membrane adhesion", format: kT },
    { key: "uptake_probability", label: "Uptake probability", format: pct },
    { key: "endosomal_escape_probability", label: "Endosomal escape", format: pct },
    { key: "intracellular_release_fraction", label: "Intracellular release", format: pct },
    { key: "primary_pathway", label: "Primary pathway" },
  ],
  transport: [
    { key: "penetration_depth_um", label: "Penetration depth (1 hr)", format: um },
    { key: "effective_diffusion_coefficient_m2_s", label: "Effective diffusion", unit: "m²/s", format: (v) => (v as number).toExponential(2) },
    { key: "tissue", label: "Tissue model" },
  ],
  release: [
    { key: "half_life_hours", label: "Release half-life", format: hrs },
    { key: "trigger_mechanism", label: "Release mechanism" },
  ],
};

export function formatMetricValue(def: MetricDef, value: unknown): string {
  if (value == null) return "—";
  if (def.format) return def.format(value);
  return String(value);
}

export function formatUncertainty(unc: UncertaintyRecord | undefined): string | null {
  if (!unc || unc.ci_95_low == null || unc.ci_95_high == null) return null;
  const n = unc.n_replicates ? ` (n=${unc.n_replicates})` : "";
  return `95% CI: ${unc.ci_95_low.toFixed(3)} – ${unc.ci_95_high.toFixed(3)}${n}`;
}

export function getMethodology(data: Record<string, unknown>): AnalysisMethod[] {
  const raw = data.methodology;
  if (!Array.isArray(raw)) return [];
  return raw as AnalysisMethod[];
}
