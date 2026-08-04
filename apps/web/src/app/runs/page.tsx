"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { listRuns, type SimulationRun } from "@/lib/api";
import { STATUS_LABELS } from "@/lib/wizard-copy";

export default function RunsPage() {
  const [runs, setRuns] = useState<SimulationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listRuns()
      .then(setRuns)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load runs"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen pb-16">
      <header className="border-b border-[var(--border)] px-6 py-4">
        <div className="mx-auto flex max-w-4xl items-center gap-3">
          <Link href="/" className="text-[var(--muted)] hover:text-white" aria-label="Home">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <h1 className="text-lg font-semibold">Simulation history</h1>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-8">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-[var(--muted)]">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading runs…
          </div>
        ) : error ? (
          <p className="text-sm text-red-400">{error}</p>
        ) : runs.length === 0 ? (
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center">
            <p className="text-[var(--muted)]">No simulations yet.</p>
            <Link
              href="/simulate"
              className="mt-4 inline-block text-sm text-[var(--primary)] hover:underline"
            >
              Start your first simulation
            </Link>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-[var(--border)]">
            <table className="w-full text-sm">
              <thead className="bg-[var(--surface-elevated)] text-left text-xs text-[var(--muted)]">
                <tr>
                  <th className="px-4 py-3">Run ID</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Modules</th>
                  <th className="px-4 py-3">Started</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id} className="border-t border-[var(--border)] hover:bg-[var(--surface-elevated)]/50">
                    <td className="px-4 py-3">
                      <Link href={`/runs/${run.id}`} className="font-mono text-xs text-[var(--primary)] hover:underline">
                        {run.id.slice(0, 8)}…
                      </Link>
                    </td>
                    <td className="px-4 py-3">{STATUS_LABELS[run.status] || run.status}</td>
                    <td className="px-4 py-3 text-[var(--muted)]">
                      {run.modules.filter((m) => m.status === "completed").length}/{run.modules.length}
                    </td>
                    <td className="px-4 py-3 text-[var(--muted)]">
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
