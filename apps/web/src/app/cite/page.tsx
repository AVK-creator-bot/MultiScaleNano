import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export default function CitePage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-3xl space-y-8 px-6 py-12">
        <div>
          <h1 className="text-3xl font-bold">How to cite MultiscaleNano</h1>
          <p className="mt-4 text-[var(--muted)]">
            If you use this platform in research, teaching, or a publication, please cite the
            software and note the coarse-grained model limitations in your methods section.
          </p>
        </div>

        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-6">
          <h2 className="font-semibold">Software citation</h2>
          <pre className="mt-4 overflow-x-auto rounded-lg bg-[var(--surface)] p-4 text-xs leading-relaxed text-white">
{`MultiscaleNano (2026). Open web platform for lipid nanoparticle
simulation with OpenMM molecular dynamics.
https://github.com/AVK-creator-bot/MultiScaleNano
Accessed: [date].`}
          </pre>
        </section>

        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-6">
          <h2 className="font-semibold">Suggested methods text</h2>
          <pre className="mt-4 overflow-x-auto rounded-lg bg-[var(--surface)] p-4 text-xs leading-relaxed text-[var(--muted)]">
{`LNP formulations were evaluated in silico using MultiscaleNano, an
open coarse-grained molecular dynamics platform (OpenMM). Simulations
included [modules run] in standard MD mode with 3 independent
replicates. Reported metrics include 95% confidence intervals derived
from replicate ensembles. Computational predictions were treated as
comparative screening and validated by [experimental method].`}
          </pre>
        </section>

        <section>
          <h2 className="font-semibold">Export your data</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            After each simulation, download <strong className="text-white">JSON</strong> or{" "}
            <strong className="text-white">CSV</strong> from the results page. Files include module
            metrics, uncertainty records, and methodology metadata for supplementary materials.
          </p>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
