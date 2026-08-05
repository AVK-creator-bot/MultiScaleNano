import Link from "next/link";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export default function AboutPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-3xl space-y-8 px-6 py-12">
        <div>
          <p className="text-sm font-medium uppercase tracking-widest text-[var(--primary)]">
            Now public
          </p>
          <h1 className="mt-2 text-3xl font-bold">About MultiscaleNano</h1>
          <p className="mt-4 text-[var(--muted)]">
            MultiscaleNano is a free, open web platform for nanotechnology and drug-delivery
            research. Anyone with a browser can design lipid nanoparticles and run a full
            simulation pipeline — from drug structure through encapsulation, stability, transport,
            and release — powered by real OpenMM molecular dynamics.
          </p>
        </div>

        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-6">
          <h2 className="font-semibold">Mission</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Lower the barrier to in silico nanocarrier research. No HPC account, no command line,
            no proprietary lock-in. Built for students, labs, and independent researchers worldwide.
          </p>
        </section>

        <section>
          <h2 className="font-semibold">What makes it different</h2>
          <ul className="mt-3 list-inside list-disc space-y-2 text-sm text-[var(--muted)]">
            <li>
              <strong className="text-white">No-code wizard</strong> — mRNA, siRNA, and small-molecule
              examples with literature lipid presets
            </li>
            <li>
              <strong className="text-white">End-to-end pipeline</strong> — multiple modules in one
              session, not a single isolated calculation
            </li>
            <li>
              <strong className="text-white">Documented science</strong> — every result includes
              methodology, equations, and uncertainty from MD replicates
            </li>
            <li>
              <strong className="text-white">Open source</strong> — code on GitHub; extend, audit,
              and cite it
            </li>
          </ul>
        </section>

        <section className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-6">
          <h2 className="font-semibold text-amber-100">Important limitations</h2>
          <p className="mt-2 text-sm text-amber-100/90">
            Results use Martini 3 coarse-grained MD (OpenMM) when deployed with full force-field
            assets, aligned with nanoHUB-style lipid simulations. Predictions are for comparative
            screening and hypothesis generation — they should supplement experimental validation.
            should supplement, not replace, experimental validation. See{" "}
            <Link href="/methodology" className="underline">
              Methods
            </Link>{" "}
            for full details.
          </p>
        </section>

        <section>
          <h2 className="font-semibold">Open source</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Source code, architecture, and deployment configs are on{" "}
            <a
              href="https://github.com/AVK-creator-bot/MultiScaleNano"
              className="text-[var(--primary)] hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              GitHub
            </a>
            . Contributions and university collaborations welcome — see{" "}
            <Link href="/partners" className="text-[var(--primary)] hover:underline">
              Partners
            </Link>{" "}
            or email{" "}
            <a
              href="mailto:Multiscalenano@outlook.com"
              className="text-[var(--primary)] hover:underline"
            >
              Multiscalenano@outlook.com
            </a>
            .
          </p>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
