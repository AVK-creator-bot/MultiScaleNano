import Link from "next/link";
import { ArrowRight, FlaskConical, Globe, Layers, Play, Zap } from "lucide-react";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />

      <div className="border-b border-[var(--primary)]/30 bg-[var(--primary)]/10 px-6 py-3 text-center text-sm">
        <span className="font-medium text-[var(--primary)]">Now live & free</span>
        <span className="mx-2 text-[var(--muted)]">·</span>
        Open to all nanotechnology researchers — no account required
      </div>

      <main>
        <section className="mx-auto max-w-6xl px-6 py-20 text-center">
          <p className="mb-4 text-sm font-medium uppercase tracking-widest text-[var(--primary)]">
            Nanotechnology simulation platform
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
            Design and simulate nanoparticle drug delivery — free, in your browser
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-[var(--muted)]">
            MultiscaleNano is an open research tool for the nanotechnology community. Run real
            OpenMM molecular dynamics from drug structure through encapsulation, stability, and
            release — no coding, no HPC account.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/simulate"
              className="inline-flex items-center gap-2 rounded-lg bg-[var(--primary)] px-8 py-3 font-medium text-white hover:bg-[var(--primary-hover)] transition-colors"
            >
              <Play className="h-4 w-4" />
              Start a simulation
            </Link>
            <Link
              href="/about"
              className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-6 py-3 text-sm hover:bg-[var(--surface-elevated)]"
            >
              Learn more
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <p className="mt-4 text-sm text-[var(--muted)]">
            Free · Open source · Export JSON/CSV ·{" "}
            <Link href="/partners" className="text-[var(--primary)] hover:underline">
              Partner with us
            </Link>
          </p>
        </section>

        <section className="border-y border-[var(--border)] bg-[var(--surface)] py-16">
          <div className="mx-auto max-w-4xl px-6">
            <h2 className="text-center text-2xl font-bold">How it works</h2>
            <p className="mt-2 text-center text-[var(--muted)]">
              Three steps — built for researchers, students, and labs
            </p>
            <div className="mt-12 grid gap-8 md:grid-cols-3">
              <HowStep
                step={1}
                title="Describe your payload"
                description="mRNA, siRNA, or small molecule — paste a sequence, PubChem ID, or SMILES. Structure is verified before simulation."
              />
              <HowStep
                step={2}
                title="Design your nanocarrier"
                description="Literature lipid presets (SM-102, ALC-0315, MC3), loading, size, temperature, and target tissue."
              />
              <HowStep
                step={3}
                title="Run & export"
                description="OpenMM MD across the full pipeline. Download results with methodology and uncertainty bands."
              />
            </div>
          </div>
        </section>

        <section className="py-16">
          <div className="mx-auto grid max-w-6xl gap-8 px-6 md:grid-cols-3">
            <FeatureCard
              icon={<Globe className="h-6 w-6" />}
              title="Free & accessible"
              description="Public web platform. No paywall. Open source on GitHub for anyone in nanotech research."
            />
            <FeatureCard
              icon={<Layers className="h-6 w-6" />}
              title="Full pipeline"
              description="Encapsulation through release in one workflow — not isolated calculators."
            />
            <FeatureCard
              icon={<Zap className="h-6 w-6" />}
              title="Real physics"
              description="OpenMM molecular dynamics with documented methods — not black-box guesses."
            />
          </div>
        </section>

        <section className="border-t border-[var(--border)] bg-[var(--surface)] py-14">
          <div className="mx-auto max-w-2xl px-6 text-center">
            <FlaskConical className="mx-auto h-8 w-8 text-[var(--primary)]" />
            <h2 className="mt-4 text-xl font-bold">For universities & labs</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Adopt MultiscaleNano in courses, compare formulations with your lab data, or co-develop
              validation studies. Always free for research and education.
            </p>
            <Link
              href="/partners"
              className="mt-6 inline-block text-sm font-medium text-[var(--primary)] hover:underline"
            >
              Partnership information →
            </Link>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}

function HowStep({
  step,
  title,
  description,
}: {
  step: number;
  title: string;
  description: string;
}) {
  return (
    <div className="text-center">
      <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-[var(--primary)] text-sm font-bold text-white">
        {step}
      </div>
      <h3 className="mt-4 font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-[var(--muted)]">{description}</p>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-6">
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--primary)]/10 text-[var(--primary)]">
        {icon}
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-[var(--muted)]">{description}</p>
    </div>
  );
}
