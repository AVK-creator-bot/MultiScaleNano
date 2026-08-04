import Link from "next/link";
import { ArrowRight, Atom } from "lucide-react";

export function SiteHeader() {
  return (
    <header className="border-b border-[var(--border)] px-6 py-4">
      <div className="mx-auto flex max-w-6xl items-center justify-between">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--primary)]">
            <Atom className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-semibold tracking-tight">MultiscaleNano</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/about" className="hidden text-[var(--muted)] hover:text-white sm:inline">
            About
          </Link>
          <Link href="/runs" className="hidden text-[var(--muted)] hover:text-white sm:inline">
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
  );
}
