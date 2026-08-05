"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Download, Loader2 } from "lucide-react";
import { ResultsPanel } from "@/components/ResultsPanel";
import { StructurePanel } from "@/components/StructurePanel";
import {
  exportRunUrl,
  getRun,
  getRunResults,
  type RunResults,
  type SimulationRun,
} from "@/lib/api";
import { STATUS_LABELS } from "@/lib/wizard-copy";

export default function RunDetailPage() {
  const params = useParams();
  const runId = params.id as string;
  const [run, setRun] = useState<SimulationRun | null>(null);
  const [results, setResults] = useState<RunResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const r = await getRun(runId);
        setRun(r);
        if (r.status === "completed" || r.status === "failed") {
          const res = await getRunResults(runId);
          setResults(res);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load run");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [runId]);

  useEffect(() => {
    if (!run || run.status === "completed" || run.status === "failed") return;
    const interval = setInterval(async () => {
      try {
        const updated = await getRun(runId);
        setRun(updated);
        if (updated.status === "completed") {
          const res = await getRunResults(runId);
          setResults(res);
        }
      } catch {
        /* polling retry on next tick */
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [run, runId]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center gap-2 text-sm text-[var(--muted)]">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading run…
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
        <p className="text-red-400">{error || "Run not found"}</p>
        <Link href="/runs" className="text-sm text-[var(--primary)] hover:underline">
          Back to Run History
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-16">
      <header className="border-b border-[var(--border)] px-6 py-4">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/runs" className="text-[var(--muted)] hover:text-white" aria-label="Run History">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="font-semibold">Run results</h1>
              <p className="font-mono text-xs text-[var(--muted)]">{run.id}</p>
            </div>
          </div>
          <span className="text-sm">{STATUS_LABELS[run.status] || run.status}</span>
        </div>
      </header>

      <main className="mx-auto max-w-3xl space-y-6 px-6 py-8">
        <div className="flex flex-wrap gap-2">
          <a
            href={exportRunUrl(runId, "json")}
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-xs hover:bg-[var(--surface-elevated)]"
          >
            <Download className="h-3.5 w-3.5" />
            Download JSON
          </a>
          <a
            href={exportRunUrl(runId, "csv")}
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-xs hover:bg-[var(--surface-elevated)]"
          >
            <Download className="h-3.5 w-3.5" />
            Download CSV
          </a>
        </div>

        <div className="space-y-2">
          {run.modules.map((mod) => (
            <div
              key={mod.module}
              className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface-elevated)] px-4 py-2 text-sm"
            >
              <span className="capitalize">{mod.module.replace(/_/g, " ")}</span>
              <span className="text-xs text-[var(--muted)]">
                {STATUS_LABELS[mod.status] || mod.status}
              </span>
            </div>
          ))}
        </div>

        {results?.modules && Object.keys(results.modules).length > 0 ? (
          <>
            <StructurePanel runId={runId} modules={results.modules} />
            <div>
              <h2 className="mb-3 font-semibold">Metrics & methodology</h2>
              <ResultsPanel modules={results.modules} />
            </div>
          </>
        ) : run.status === "running" || run.status === "queued" ? (
          <p className="text-sm text-[var(--muted)]">Simulation in progress…</p>
        ) : null}
      </main>
    </div>
  );
}
