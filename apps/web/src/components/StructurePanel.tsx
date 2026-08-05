"use client";

import { useMemo, useState } from "react";
import { Download } from "lucide-react";
import { StructureViewer } from "@/components/StructureViewer";
import { runStructureUrl, type ModuleArtifact } from "@/lib/api";

const MODULE_LABELS: Record<string, string> = {
  encapsulation: "Encapsulation",
  formation: "Formation",
  stability: "Stability (+10 K)",
  corona: "Protein corona",
  cell_interaction: "Membrane approach",
};

const MODULE_ORDER = [
  "encapsulation",
  "formation",
  "stability",
  "corona",
  "cell_interaction",
];

interface StructurePanelProps {
  runId: string;
  modules: Record<string, ModuleArtifact | { data?: Record<string, unknown> }>;
}

function moduleHasStructure(mod: ModuleArtifact | { data?: Record<string, unknown> }): boolean {
  const structure = mod.data?.structure as { available?: boolean } | undefined;
  return Boolean(structure?.available);
}

export function StructurePanel({ runId, modules }: StructurePanelProps) {
  const available = useMemo(
    () =>
      MODULE_ORDER.filter((name) => modules[name] && moduleHasStructure(modules[name])).map(
        (name) => ({
          name,
          label: MODULE_LABELS[name] || name.replace(/_/g, " "),
        })
      ),
    [modules]
  );

  const [active, setActive] = useState<string | null>(null);
  const selected = active && available.some((m) => m.name === active) ? active : available[0]?.name;

  if (!available.length) {
    return null;
  }

  const pdbUrl = selected ? runStructureUrl(runId, selected) : "";

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold">3D structure</h2>
        {selected && (
          <a
            href={pdbUrl}
            download
            className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-[var(--surface-elevated)]"
          >
            <Download className="h-3.5 w-3.5" />
            Download PDB
          </a>
        )}
      </div>

      {available.length > 1 && (
        <div className="flex flex-wrap gap-2">
          {available.map(({ name, label }) => (
            <button
              key={name}
              type="button"
              onClick={() => setActive(name)}
              className={`rounded-lg px-3 py-1.5 text-xs ${
                selected === name
                  ? "bg-[var(--primary)] text-white"
                  : "border border-[var(--border)] text-[var(--muted)] hover:text-white"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      <StructureViewer key={selected} pdbUrl={pdbUrl} />

      <div className="flex flex-wrap gap-4 text-xs text-[var(--muted)]">
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[#60a5fa]" />
          Lipid / NP beads
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[#f97316]" />
          Drug core
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[#a78bfa]" />
          Protein
        </span>
      </div>
      <p className="text-xs text-[var(--muted)]">
        Final coarse-grained MD coordinates from replicate 1. Drag to rotate; scroll to zoom.
      </p>
    </section>
  );
}
