import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--surface)]">
      <div className="mx-auto grid max-w-6xl gap-8 px-6 py-10 sm:grid-cols-2 md:grid-cols-4">
        <div className="sm:col-span-2">
          <p className="font-semibold text-white">MultiscaleNano</p>
          <p className="mt-2 max-w-sm text-sm text-[var(--muted)]">
            Free, open nanotechnology simulation for researchers. Real OpenMM molecular dynamics
            in your browser — no install required.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
            Platform
          </p>
          <ul className="mt-3 space-y-2 text-sm">
            <li>
              <Link href="/simulate" className="hover:text-white">
                Simulator
              </Link>
            </li>
            <li>
              <Link href="/methodology" className="hover:text-white">
                Methods
              </Link>
            </li>
            <li>
              <Link href="/runs" className="hover:text-white">
                Run History
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
            Project
          </p>
          <ul className="mt-3 space-y-2 text-sm">
            <li>
              <Link href="/about" className="hover:text-white">
                About
              </Link>
            </li>
            <li>
              <Link href="/cite" className="hover:text-white">
                Cite
              </Link>
            </li>
            <li>
              <Link href="/partners" className="hover:text-white">
                Partners
              </Link>
            </li>
            <li>
              <a href="mailto:Multiscalenano@outlook.com" className="hover:text-white">
                Support
              </a>
            </li>
            <li>
              <a
                href="https://github.com/AVK-creator-bot/MultiScaleNano"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-white"
              >
                GitHub
              </a>
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-[var(--border)] py-4 text-center text-xs text-[var(--muted)]">
        Open source · Free for research and education ·{" "}
        <a href="mailto:Multiscalenano@outlook.com" className="hover:text-white">
          Multiscalenano@outlook.com
        </a>
      </div>
    </footer>
  );
}
