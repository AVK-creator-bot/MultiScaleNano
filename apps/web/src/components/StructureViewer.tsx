"use client";

import { useEffect, useRef } from "react";

const CHAIN_STYLES: Record<string, { color: string; radius: number; opacity?: number }> = {
  A: { color: "#60a5fa", radius: 1.2 },
  B: { color: "#f97316", radius: 1.0 },
  C: { color: "#a78bfa", radius: 1.0 },
  D: { color: "#64748b", radius: 0.8, opacity: 0.45 },
};

interface StructureViewerProps {
  pdbUrl: string;
  height?: number;
}

export function StructureViewer({ pdbUrl, height = 420 }: StructureViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let cancelled = false;
    let viewer: import("3dmol").Viewer | null = null;

    (async () => {
      try {
        const res = await fetch(pdbUrl);
        if (!res.ok) throw new Error("Structure file not found");
        const pdb = await res.text();
        if (cancelled) return;

        const $3Dmol = (await import("3dmol")).default;
        if (cancelled || !containerRef.current) return;

        container.innerHTML = "";
        viewer = $3Dmol.createViewer(container, { backgroundColor: "#0f1419" });
        viewer.addModel(pdb, "pdb");

        for (const [chain, style] of Object.entries(CHAIN_STYLES)) {
          viewer.setStyle({ chain }, { sphere: style });
        }

        viewer.zoomTo();
        viewer.render();
      } catch {
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML =
            '<p class="flex h-full items-center justify-center px-4 text-center text-sm text-[var(--muted)]">Structure preview unavailable for this run.</p>';
        }
      }
    })();

    return () => {
      cancelled = true;
      viewer?.clear?.();
    };
  }, [pdbUrl]);

  return (
    <div
      ref={containerRef}
      className="relative w-full overflow-hidden rounded-xl border border-[var(--border)] bg-[#0f1419]"
      style={{ height }}
      role="img"
      aria-label="3D molecular structure viewer"
    />
  );
}
