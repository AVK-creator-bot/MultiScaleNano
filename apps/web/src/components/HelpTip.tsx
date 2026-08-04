import { Info } from "lucide-react";

export function HelpTip({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-3 rounded-lg border border-[var(--primary)]/20 bg-[var(--primary)]/5 px-4 py-3 text-sm text-[var(--muted)]">
      <Info className="mt-0.5 h-4 w-4 shrink-0 text-[var(--primary)]" />
      <div>{children}</div>
    </div>
  );
}

export function StepHeader({
  title,
  subtitle,
}: {
  title: string;
  subtitle: string;
}) {
  return (
    <div className="mb-6">
      <h2 className="text-xl font-semibold text-white">{title}</h2>
      <p className="mt-1 text-sm text-[var(--muted)]">{subtitle}</p>
    </div>
  );
}
