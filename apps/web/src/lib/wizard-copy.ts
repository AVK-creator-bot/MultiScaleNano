/** Plain-language copy for the simulation wizard */

export const WIZARD_STEPS = [
  {
    id: "drug",
    label: "Your drug",
    title: "What are you delivering?",
    subtitle:
      "Tell us about your drug or genetic payload. We'll verify the structure before any simulation runs.",
  },
  {
    id: "lnp",
    label: "Nanoparticle",
    title: "Design your lipid nanoparticle",
    subtitle:
      "Choose a proven formulation or adjust lipids and particle size. Presets match real mRNA and siRNA products.",
  },
  {
    id: "environment",
    label: "Environment",
    title: "Where will it go?",
    subtitle:
      "Set the biological conditions and target tissue. These feed into stability and transport models.",
  },
  {
    id: "pipeline",
    label: "Review",
    title: "Choose what to simulate",
    subtitle:
      "Each step runs real molecular dynamics with independent random seeds per run.",
  },
  {
    id: "run",
    label: "Results",
    title: "Your results",
    subtitle: "Watch progress below. You can leave this page open while simulations run.",
  },
] as const;

export const STATUS_LABELS: Record<string, string> = {
  queued: "Waiting",
  running: "Simulating…",
  completed: "Complete",
  failed: "Needs attention",
};

export const EXAMPLE_PAYLOADS = [
  {
    id: "mrna",
    name: "mRNA example",
    description: "Standard mRNA LNP — good starting point",
    drug: {
      name: "mRNA payload",
      payload_type: "mrna" as const,
      structure_source_type: "sequence" as const,
      structure_value: "AUGGCCUUGCCGCUCUGUUU",
      loading_pct: 2,
      encapsulation_mode: "core",
    },
    presetKey: "mrna_sm102",
  },
  {
    id: "paclitaxel",
    name: "Paclitaxel (small molecule)",
    description: "PubChem CID 36314 — cancer drug example",
    drug: {
      name: "Paclitaxel",
      payload_type: "small_molecule" as const,
      structure_source_type: "pubchem" as const,
      structure_value: "36314",
      molecular_weight: 853.9,
      loading_pct: 10,
      encapsulation_mode: "core",
    },
    presetKey: "small_molecule",
  },
  {
    id: "sirna",
    name: "siRNA example",
    description: "Onpattro-style MC3 LNP — RNAi delivery",
    drug: {
      name: "siRNA payload",
      payload_type: "sirna" as const,
      structure_source_type: "sequence" as const,
      structure_value: "UUGUUGUUGUUGUUGUUGUU",
      loading_pct: 3,
      encapsulation_mode: "core",
    },
    presetKey: "sirna_mcq",
  },
] as const;

export function friendlyError(message: string): string {
  if (message.includes("OpenMM")) {
    return "OpenMM is not loaded on the server. Restart with .\\scripts\\start-local.ps1 or docker compose up --build.";
  }
  if (
    message.includes("404") ||
    message.includes("not reachable") ||
    message.includes("connect") ||
    message.includes("unavailable")
  ) {
    return "We couldn't connect to the simulation service. Please refresh and try again.";
  }
  if (message.includes("structure") || message.includes("SMILES") || message.includes("PubChem")) {
    return message;
  }
  return message;
}
