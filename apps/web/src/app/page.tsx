import Link from "next/link";
import { ArrowRight, Atom, CheckCircle2, FlaskConical, Layers, Play, Zap } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--border)] px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--primary)]">
              <Atom className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-semibold tracking-tight">MultiscaleNano</span>
          </div>
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/runs" className="text-[var(--muted)] hover:text-white">
              History
            </Link>
            <Link href="/methodology" className="text-[var(--muted)] hover:text-white">
              Methods
            </Link>
            <Link
              href="/simulate"
              className="inline-flex items-center gap-2 rounded-lg bg-[var(--primary)] px-4 py-2 text-white hover:bg-[var(--primary-hover)] transition-colors"
            >
              Open Simulator
              <ArrowRight className="h-4 w-4" />
            </Link>
          </nav>
        </div>
      </header>

      <main>
        <section className="mx-auto max-w-6xl px-6 py-20 text-center">
          <p className="mb-4 text-sm font-medium uppercase tracking-widest text-[var(--primary)]">
            Lipid nanoparticle simulator
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
            Design and simulate drug-loaded nanoparticles — no coding required
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-[var(--muted)]">
            A guided wizard walks you from drug structure to encapsulation, stability, and tissue
            delivery predictions — powered by real molecular dynamics.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/simulate"
              className="inline-flex items-center gap-2 rounded-lg bg-[var(--primary)] px-8 py-3 font-medium text-white hover:bg-[var(--primary-hover)] transition-colors"
            >
              <Play className="h-4 w-4" />
              Start a simulation
            </Link>
            <p className="text-sm text-[var(--muted)]">Free to use · No install · Real molecular dynamics</p>
          </div>
        </section>

        <section className="border-y border-[var(--border)] bg-[var(--surface)] py-16">
          <div className="mx-auto max-w-4xl px-6">
            <h2 className="text-center text-2xl font-bold">How it works</h2>
            <p className="mt-2 text-center text-[var(--muted)]">Three steps — we handle the science</p>
            <div className="mt-12 grid gap-8 md:grid-cols-3">
              <HowStep
                step={1}
                title="Describe your drug"
                description="Pick an example (mRNA or Paclitaxel) or paste a PubChem ID, SMILES, or sequence. We verify it before simulating."
              />
              <HowStep
                step={2}
                title="Design your LNP"
                description="Choose a literature-based lipid recipe, set loading and particle size, and pick your target tissue."
              />
              <HowStep
                step={3}
                title="Run & review"
                description="Real OpenMM simulations compute encapsulation, stability, transport, and release — with uncertainty estimates."
              />
            </div>
          </div>
        </section>

        <section className="py-16">
          <div className="mx-auto grid max-w-6xl gap-8 px-6 md:grid-cols-3">
            <FeatureCard
              icon={<FlaskConical className="h-6 w-6" />}
              title="Guided wizard"
              description="No input files or command lines. Every field has examples and validation built in."
            />
            <FeatureCard
              icon={<Layers className="h-6 w-6" />}
              title="Full pipeline"
              description="Encapsulation through release in one workflow, with results linked step to step."
            />
            <FeatureCard
              icon={<Zap className="h-6 w-6" />}
              title="Real physics"
              description="OpenMM molecular dynamics — not instant guesses. Every metric shows how it was calculated."
            />
          </div>
        </section>
      </main>

      <footer className="border-t border-[var(--border)] py-8 text-center text-sm text-[var(--muted)]">
        MultiscaleNano — Nanomedicine simulation for researchers
      </footer>
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
