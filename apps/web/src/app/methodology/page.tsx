import Link from "next/link";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

const MODULES = [
  {
    name: "Encapsulation",
    engine: "OpenMM coarse-grained LJ",
    metrics: [
      "Potential energy from Langevin MD trajectory",
      "Encapsulation efficiency from core bead fraction × compactness",
      "Drug retention ΔG from mean potential energy per bead",
    ],
    replicates: "3 (standard) / 5 (production)",
  },
  {
    name: "Formation",
    engine: "OpenMM self-assembly MD",
    metrics: [
      "Hydrodynamic radius R_H ≈ 2 × R_g from final configuration",
      "Morphology classification (core-shell vs compact-sphere)",
      "Polydispersity from replicate spread",
    ],
    replicates: "3 / 5",
  },
  {
    name: "Stability",
    engine: "OpenMM thermal perturbation (+10 K)",
    metrics: [
      "Stability score from R_g change under heat stress",
      "Drug leakage rate from energy fluctuation proxy",
    ],
    replicates: "3 / 5",
  },
  {
    name: "Transport",
    engine: "Stokes–Einstein continuum bridge",
    metrics: [
      "Effective diffusion D = k_B T / (6πηR_H)",
      "Penetration depth x ≈ √(2Dεt) in porous tissue",
    ],
    replicates: "Deterministic from formation MD",
  },
  {
    name: "Release",
    engine: "Slab diffusion with MD-derived D_eff",
    metrics: [
      "Half-life t_½ = R_H² / (2D_eff)",
      "Release profile from exponential cumulative model",
    ],
    replicates: "Deterministic from stability + formation",
  },
  {
    name: "Protein corona",
    engine: "OpenMM competitive adsorption MD",
    metrics: ["Adsorbed protein count within 1.2 nm of particle surface"],
    replicates: "3 / 5",
  },
  {
    name: "Cell interaction",
    engine: "OpenMM NP–membrane approach MD",
    metrics: [
      "Membrane adhesion energy (kT)",
      "Uptake and endosomal escape probabilities from adhesion",
    ],
    replicates: "3 / 5",
  },
];

export default function MethodologyPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-3xl space-y-8 px-6 py-8">
        <h1 className="text-3xl font-bold">Simulation methodology</h1>
        <section className="text-sm text-[var(--muted)]">
          <p>
            MultiscaleNano runs real molecular dynamics (OpenMM) for coarse-grained modules and
            applies documented physical bridges for continuum transport and release. Every completed
            run includes per-metric equations, references, and 95% confidence intervals from
            independent MD replicates where applicable.
          </p>
        </section>

        <section>
          <h2 className="mb-3 font-semibold">Simulation modes</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-4 text-sm">
              <p className="font-medium">Standard MD</p>
              <p className="mt-1 text-[var(--muted)]">5,000 MD steps · 3 replicates · ~30–45 min</p>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-4 text-sm">
              <p className="font-medium">Production MD</p>
              <p className="mt-1 text-[var(--muted)]">25,000 MD steps · 5 replicates · hours</p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="mb-3 font-semibold">Pipeline modules</h2>
          <div className="space-y-4">
            {MODULES.map((mod) => (
              <div
                key={mod.name}
                className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-4"
              >
                <h3 className="font-medium">{mod.name}</h3>
                <p className="mt-1 text-xs text-[var(--primary)]">{mod.engine}</p>
                <ul className="mt-2 list-inside list-disc text-sm text-[var(--muted)]">
                  {mod.metrics.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
                <p className="mt-2 text-xs text-[var(--muted)]">Replicates: {mod.replicates}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-4 text-sm text-[var(--muted)]">
          <p className="font-medium text-white">Limitations</p>
          <p className="mt-2">
            Results are computational predictions from simplified coarse-grained models. They
            should supplement — not replace — experimental validation. Screening mode is disabled;
            all reported metrics require MD simulation.
          </p>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
