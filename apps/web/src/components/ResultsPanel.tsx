"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { ReleaseChart } from "@/components/ReleaseChart";
import {
  formatMetricValue,
  formatUncertainty,
  getMethodology,
  MODULE_METRICS,
  type ModuleArtifact,
} from "@/lib/results-metrics";

interface ResultsPanelProps {
  modules: Record<string, ModuleArtifact>;
}

export function ResultsPanel({ modules }: ResultsPanelProps) {
  const moduleNames = Object.keys(modules).sort();

  if (!moduleNames.length) {
    return (
      <p className="text-sm text-[var(--muted)]">No result artifacts available yet.</p>
    );
  }

  return (
    <div className="space-y-4">
      {moduleNames.map((name) => (
        <ModuleResults key={name} name={name} artifact={modules[name]} />
      ))}
    </div>
  );
}

function ModuleResults({ name, artifact }: { name: string; artifact: ModuleArtifact }) {
  const [expanded, setExpanded] = useState(false);
  const defs = MODULE_METRICS[name] || [];
  const data = artifact.data || {};
  const methodology = getMethodology(data);
  const releaseProfile = data.release_profile as
    | { time_hours: number; fraction_released: number }[]
    | undefined;

  const visible = defs.filter((d) => data[d.key] != null);
  if (!visible.length && !methodology.length) return null;

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)]">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="font-medium capitalize">{name.replace(/_/g, " ")}</span>
        {expanded ? (
          <ChevronDown className="h-4 w-4 text-[var(--muted)]" />
        ) : (
          <ChevronRight className="h-4 w-4 text-[var(--muted)]" />
        )}
      </button>

      <div className="grid gap-3 border-t border-[var(--border)] px-4 py-3 sm:grid-cols-2">
        {visible.map((def) => {
          const unc = artifact.uncertainty?.[def.key];
          const uncText = formatUncertainty(unc);
          return (
            <div key={def.key}>
              <p className="text-xs text-[var(--muted)]">
                {def.label}
                {def.unit ? ` (${def.unit})` : ""}
              </p>
              <p className="mt-0.5 text-lg font-semibold">
                {formatMetricValue(def, data[def.key])}
              </p>
              {uncText && <p className="text-xs text-[var(--muted)]">{uncText}</p>}
            </div>
          );
        })}
      </div>

      {name === "release" && releaseProfile?.length ? (
        <div className="border-t border-[var(--border)] px-4 py-3">
          <ReleaseChart profile={releaseProfile} />
        </div>
      ) : null}

      {expanded && methodology.length > 0 && (
        <div className="border-t border-[var(--border)] px-4 py-3">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
            Methodology
          </h4>
          <div className="space-y-2">
            {methodology.map((m) => (
              <div key={m.metric} className="rounded-lg bg-[var(--surface)] p-3 text-xs">
                <p className="font-medium text-white">{m.metric.replace(/_/g, " ")}</p>
                <p className="mt-1 font-mono text-[var(--muted)]">{m.equation}</p>
                <p className="mt-1 text-[var(--muted)]">{m.reference}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
