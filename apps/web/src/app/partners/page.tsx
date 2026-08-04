import Link from "next/link";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export default function PartnersPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-3xl space-y-8 px-6 py-12">
        <div>
          <h1 className="text-3xl font-bold">University & lab partnerships</h1>
          <p className="mt-4 text-[var(--muted)]">
            MultiscaleNano is free for research and education. We are looking for university labs,
            courses, and student groups to use the platform, give feedback, and help validate it
            against experimental work.
          </p>
        </div>

        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-6">
          <h2 className="font-semibold">What we offer partners</h2>
          <ul className="mt-3 list-inside list-disc space-y-2 text-sm text-[var(--muted)]">
            <li>Free browser access — no install for students or PIs</li>
            <li>Full simulation pipeline with exportable JSON/CSV results</li>
            <li>Open source code for customization or local deployment</li>
            <li>Documented methods suitable for teaching and lab reports</li>
            <li>Co-authorship or acknowledgment for meaningful validation work</li>
          </ul>
        </section>

        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-6">
          <h2 className="font-semibold">Who we&apos;re looking for</h2>
          <ul className="mt-3 list-inside list-disc space-y-2 text-sm text-[var(--muted)]">
            <li>Drug delivery & nanomedicine research groups</li>
            <li>Pharmaceutics, bioengineering, or materials science courses</li>
            <li>Undergraduate or high-school research programs doing LNP work</li>
            <li>Labs willing to compare one formulation in silico vs in vitro</li>
          </ul>
        </section>

        <section className="rounded-xl border border-[var(--primary)]/30 bg-[var(--primary)]/10 p-6">
          <h2 className="font-semibold">Get in touch</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Email us for university partnerships, lab adoption, course use, or support. Include
            your institution, lab or course name, and how you&apos;d like to use MultiscaleNano.
          </p>
          <a
            href="mailto:Multiscalenano@outlook.com"
            className="mt-4 inline-block rounded-lg bg-[var(--primary)] px-5 py-2.5 text-sm font-medium text-white hover:bg-[var(--primary-hover)]"
          >
            Multiscalenano@outlook.com
          </a>
          <p className="mt-4 text-xs text-[var(--muted)]">
            You can also open a{" "}
            <a
              href="https://github.com/AVK-creator-bot/MultiScaleNano/issues/new"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--primary)] hover:underline"
            >
              GitHub issue
            </a>{" "}
            for technical feedback.
          </p>
        </section>

        <p className="text-sm text-[var(--muted)]">
          Ready to try it now?{" "}
          <Link href="/simulate" className="text-[var(--primary)] hover:underline">
            Open the simulator
          </Link>
        </p>
      </main>
      <SiteFooter />
    </div>
  );
}
