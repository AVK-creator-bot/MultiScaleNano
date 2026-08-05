"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  drawBeadStructure,
  normalizeBeadStructure,
  type BeadStructure,
} from "@/lib/bead-structure";

interface BeadStructureViewerProps {
  structure?: BeadStructure;
  pdbUrl?: string;
  height?: number;
}

export function BeadStructureViewer({
  structure,
  pdbUrl,
  height = 420,
}: BeadStructureViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [rotation, setRotation] = useState({ x: 0.35, y: 0.6 });
  const [beads, setBeads] = useState<{ positions: number[][]; roles: string[] } | null>(
    () => normalizeBeadStructure(structure)
  );
  const [error, setError] = useState<string | null>(null);
  const dragging = useRef(false);
  const lastPointer = useRef({ x: 0, y: 0 });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const inline = normalizeBeadStructure(structure);
      if (inline) {
        setBeads(inline);
        setError(null);
        return;
      }

      if (!pdbUrl) {
        setBeads(null);
        setError("No structure coordinates for this run. Start a new simulation after the latest deploy.");
        return;
      }

      try {
        const res = await fetch(pdbUrl);
        if (!res.ok) throw new Error("PDB not found");
        const text = await res.text();
        const parsed = parsePdb(text);
        if (cancelled) return;
        if (!parsed) throw new Error("Invalid PDB");
        setBeads(parsed);
        setError(null);
      } catch {
        if (!cancelled) {
          setBeads(null);
          setError(
            "Structure coordinates are missing for this run. Run a new simulation to generate a 3D preview."
          );
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [structure, pdbUrl]);

  const paint = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !beads) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    drawBeadStructure(ctx, canvas.width, canvas.height, beads.positions, beads.roles, rotation);
  }, [beads, rotation]);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      const w = container.clientWidth;
      canvas.width = w * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${height}px`;
      const ctx = canvas.getContext("2d");
      if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      paint();
    };

    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [height, paint]);

  useEffect(() => {
    paint();
  }, [paint]);

  const onPointerDown = (e: React.PointerEvent) => {
    dragging.current = true;
    lastPointer.current = { x: e.clientX, y: e.clientY };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  };

  const onPointerMove = (e: React.PointerEvent) => {
    if (!dragging.current) return;
    const dx = e.clientX - lastPointer.current.x;
    const dy = e.clientY - lastPointer.current.y;
    lastPointer.current = { x: e.clientX, y: e.clientY };
    setRotation((r) => ({ x: r.x + dy * 0.01, y: r.y + dx * 0.01 }));
  };

  const onPointerUp = () => {
    dragging.current = false;
  };

  if (error) {
    return (
      <div
        className="flex items-center justify-center rounded-xl border border-[var(--border)] bg-[#0f1419] px-4 text-center text-sm text-[var(--muted)]"
        style={{ height }}
      >
        {error}
      </div>
    );
  }

  if (!beads) {
    return (
      <div
        className="flex items-center justify-center rounded-xl border border-[var(--border)] bg-[#0f1419] text-sm text-[var(--muted)]"
        style={{ height }}
      >
        Loading structure…
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="relative w-full cursor-grab overflow-hidden rounded-xl border border-[var(--border)] bg-[#0f1419] active:cursor-grabbing"
      style={{ height }}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={onPointerUp}
      role="img"
      aria-label="3D coarse-grained structure viewer"
    >
      <canvas ref={canvasRef} className="block touch-none" />
    </div>
  );
}

function parsePdb(text: string): { positions: number[][]; roles: string[] } | null {
  const positions: number[][] = [];
  const roles: string[] = [];
  for (const line of text.split("\n")) {
    if (!line.startsWith("ATOM")) continue;
    const x = parseFloat(line.slice(30, 38));
    const y = parseFloat(line.slice(38, 46));
    const z = parseFloat(line.slice(46, 54));
    if (Number.isNaN(x) || Number.isNaN(y) || Number.isNaN(z)) continue;
    positions.push([x / 10, y / 10, z / 10]);
    const resname = line.slice(17, 20).trim();
    const chain = line[21]?.trim();
    let role = "bead";
    if (resname === "DRG" || chain === "B") role = "drug";
    else if (resname === "PRO" || chain === "C") role = "protein";
    else if (resname === "MEM" || chain === "D") role = "membrane";
    else role = "lipid";
    roles.push(role);
  }
  if (!positions.length) return null;
  return { positions, roles };
}
