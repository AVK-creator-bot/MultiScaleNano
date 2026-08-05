const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export type PayloadType =
  | "small_molecule"
  | "mrna"
  | "sirna"
  | "peptide"
  | "protein";

export type StructureSourceType =
  | "smiles"
  | "sequence"
  | "pubchem"
  | "pdb"
  | "url";

export interface DrugPayload {
  name: string;
  payload_type: PayloadType;
  structure_source_type: StructureSourceType;
  structure_value: string;
  smiles?: string;
  molecular_weight?: number | null;
  loading_pct: number;
  encapsulation_mode: string;
}

export interface LipidComponent {
  name: string;
  ratio: number;
  charge: number;
}

export interface NanocarrierDesign {
  id?: string;
  name: string;
  carrier_type: string;
  drug: DrugPayload;
  lipids: LipidComponent[];
  pegylation: { enabled: boolean; mol_pct: number; peg_length: number };
  ligands: { name: string; density_pct: number; target: string }[];
  target_size_nm: number;
  shape: string;
  environment: {
    ph: number;
    temperature_k: number;
    ionic_strength_m: number;
    fluid: string;
  };
  target: {
    cell_type: string | null;
    tissue: string | null;
    goal: string;
  };
}

export interface ResolvedDrug {
  molecular_weight: number;
  heavy_atom_count: number;
  bead_count: number;
  sequence_length: number | null;
  smiles_canonical: string | null;
  resolution_log: string[];
}

export interface ModuleSpec {
  name: string;
  label: string;
  description: string;
  question: string;
  engine: string;
  estimated_runtime_min: number;
  enabled_by_default: boolean;
}

export interface SimulationRun {
  id: string;
  design_id: string;
  status: string;
  modules: {
    module: string;
    status: string;
    error?: string | null;
    started_at: string | null;
    completed_at: string | null;
  }[];
  created_at: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  openmm_available: boolean;
  openmm_version: string | null;
  simulations_ready: boolean;
  message: string;
}

export const LOADING_LIMITS: Record<PayloadType, number> = {
  small_molecule: 50,
  peptide: 25,
  mrna: 15,
  sirna: 12,
  protein: 10,
};

export const LIPID_PRESET_LABELS: Record<string, string> = {
  mrna_sm102: "mRNA LNP (SM-102, Moderna-style)",
  mrna_comirnaty_style: "mRNA LNP (ALC-0315, Pfizer-style)",
  sirna_mcq: "siRNA LNP (MC3, Onpattro-style)",
  small_molecule: "Small molecule LNP (MC3)",
};

export const STRUCTURE_HINTS: Record<StructureSourceType, string> = {
  smiles: "e.g. CC(=O)Oc1ccccc1C(=O)O (aspirin)",
  sequence: "e.g. AUGGCCUUGCCGCUCUGUUU (RNA) or MKTAYIAK (peptide)",
  pubchem: "e.g. 36314 (Paclitaxel CID)",
  pdb: "e.g. 1BNA or 6VSB",
  url: "https://files.rcsb.org/download/1BNA.pdb",
};

async function parseApiError(res: Response): Promise<string> {
  if (res.status === 404 || res.status === 502 || res.status === 503) {
    return "The simulation service is unavailable right now. Please try again in a moment.";
  }
  try {
    const err = await res.json();
    const detail = err.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join("; ");
    }
    return err.message || res.statusText || "Request failed";
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  return fetch(url, init);
}

export async function checkHealth(): Promise<HealthStatus> {
  const readyRes = await apiFetch("/health/ready");
  if (readyRes.ok) {
    return readyRes.json();
  }

  // Degraded but API reachable — parse body when OpenMM is unavailable (503)
  if (readyRes.status === 503) {
    try {
      return await readyRes.json();
    } catch {
      /* fall through */
    }
  }

  const liveRes = await apiFetch("/health");
  if (!liveRes.ok) {
    throw new Error(await parseApiError(readyRes));
  }

  return {
    status: "degraded",
    service: "multiscale-api",
    openmm_available: false,
    openmm_version: null,
    simulations_ready: false,
    message: "API is online but simulation readiness could not be confirmed.",
  };
}

export async function fetchTemplates(): Promise<
  { id: string; name: string; design: NanocarrierDesign }[]
> {
  const res = await apiFetch("/api/designs/templates");
  if (!res.ok) throw new Error(await parseApiError(res));
  const data = await res.json();
  return data.templates;
}

export async function fetchLipidPresets(): Promise<
  Record<string, LipidComponent[]>
> {
  const res = await apiFetch("/api/lipids/presets");
  if (!res.ok) throw new Error(await parseApiError(res));
  const data = await res.json();
  return data;
}

export async function resolveDrug(drug: DrugPayload): Promise<{
  valid: boolean;
  resolved: ResolvedDrug;
}> {
  const res = await apiFetch("/api/drug/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ drug }),
  });
  if (!res.ok) throw new Error(await parseApiError(res));
  return res.json();
}

export async function createDesign(
  design: NanocarrierDesign
): Promise<NanocarrierDesign> {
  const res = await apiFetch("/api/designs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ design }),
  });
  if (!res.ok) throw new Error(await parseApiError(res));
  return res.json();
}

export async function fetchModules(): Promise<ModuleSpec[]> {
  const res = await apiFetch("/api/workflow/modules");
  if (!res.ok) throw new Error(await parseApiError(res));
  return res.json();
}

export async function planWorkflow(
  enabledModules?: string[],
  simulationMode = "standard_md"
): Promise<{
  modules: { module: string; spec: ModuleSpec }[];
  estimated_total_min: number;
  estimated_display: string;
  simulation_mode: string;
}> {
  const res = await apiFetch("/api/workflow/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      enabled_modules: enabledModules,
      simulation_mode: simulationMode,
    }),
  });
  if (!res.ok) throw new Error(await parseApiError(res));
  return res.json();
}

export async function startRun(
  designId: string,
  enabledModules?: string[],
  simulationMode = "standard_md"
): Promise<SimulationRun> {
  const res = await apiFetch("/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      design_id: designId,
      enabled_modules: enabledModules,
      simulation_mode: simulationMode,
    }),
  });
  if (!res.ok) throw new Error(await parseApiError(res));
  return res.json();
}

export async function getRun(runId: string): Promise<SimulationRun> {
  const res = await apiFetch(`/api/runs/${runId}`);
  if (!res.ok) throw new Error(await parseApiError(res));
  return res.json();
}

export interface UncertaintyRecord {
  n_replicates?: number;
  metric?: string;
  mean?: number;
  std?: number;
  ci_95_low?: number;
  ci_95_high?: number;
}

export interface ModuleArtifact {
  module?: string;
  data: Record<string, unknown>;
  uncertainty?: Record<string, UncertaintyRecord>;
  provenance?: Record<string, unknown>;
}

export interface RunResults {
  run_id: string;
  status: string;
  modules: Record<string, ModuleArtifact>;
}

export async function getRunResults(runId: string): Promise<RunResults> {
  const res = await apiFetch(`/api/runs/${runId}/results`);
  if (!res.ok) throw new Error(await parseApiError(res));
  return res.json();
}

export async function listRuns(): Promise<SimulationRun[]> {
  const res = await apiFetch("/api/runs");
  if (!res.ok) throw new Error(await parseApiError(res));
  return res.json();
}

export function exportRunUrl(runId: string, format: "json" | "csv" = "json"): string {
  const base = API_BASE || "";
  return `${base}/api/runs/${runId}/export?format=${format}`;
}

export function runStructureUrl(runId: string, moduleName: string): string {
  const base = API_BASE || "";
  return `${base}/api/runs/${runId}/structure/${moduleName}`;
}

export async function fetchDesign(designId: string): Promise<NanocarrierDesign> {
  const res = await apiFetch(`/api/designs/${designId}`);
  if (!res.ok) throw new Error(await parseApiError(res));
  return res.json();
}

export function lipidTotalPct(lipids: LipidComponent[]): number {
  return lipids.reduce((s, l) => s + l.ratio, 0) * 100;
}

export function normalizeLipids(lipids: LipidComponent[]): LipidComponent[] {
  const total = lipids.reduce((s, l) => s + l.ratio, 0);
  if (total <= 0) return lipids;
  return lipids.map((l) => ({ ...l, ratio: l.ratio / total }));
}
