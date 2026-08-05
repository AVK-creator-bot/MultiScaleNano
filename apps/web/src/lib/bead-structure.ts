export interface BeadStructure {
  available?: boolean;
  positions_nm?: number[][];
  bead_roles?: string[];
  pdb_file?: string;
  bead_count?: number;
}

const ROLE_COLORS: Record<string, string> = {
  lipid: "#60a5fa",
  drug: "#f97316",
  protein: "#a78bfa",
  np: "#60a5fa",
  bead: "#94a3b8",
  membrane: "#64748b",
};

const ROLE_RADIUS: Record<string, number> = {
  lipid: 6,
  drug: 5,
  protein: 5,
  np: 6,
  bead: 5,
  membrane: 4,
};

export function beadColor(role: string): string {
  return ROLE_COLORS[role] || ROLE_COLORS.bead;
}

export function beadRadius(role: string): number {
  return ROLE_RADIUS[role] || ROLE_RADIUS.bead;
}

/** Build minimal PDB text from bead coordinates (nm) for external tools. */
export function buildPdbFromBeads(positions_nm: number[][], bead_roles: string[]): string {
  const lines = ["TITLE     MultiscaleNano coarse-grained structure"];
  positions_nm.forEach((pos, idx) => {
    const role = bead_roles[idx] || "bead";
    const chain =
      role === "drug" ? "B" : role === "protein" ? "C" : role === "membrane" ? "D" : "A";
    const resname =
      role === "drug" ? "DRG" : role === "protein" ? "PRO" : role === "membrane" ? "MEM" : "LIP";
    const x = (pos[0] ?? 0) * 10;
    const y = (pos[1] ?? 0) * 10;
    const z = (pos[2] ?? 0) * 10;
    const serial = idx + 1;
    lines.push(
      `ATOM  ${serial.toString().padStart(5)}  CA  ${resname.padEnd(3)} ${chain}${"1".padStart(4)}    ` +
        `${x.toFixed(3).padStart(8)}${y.toFixed(3).padStart(8)}${z.toFixed(3).padStart(8)}` +
        `  1.00  0.00           C`
    );
  });
  lines.push("END");
  return lines.join("\n");
}

export function normalizeBeadStructure(
  structure: BeadStructure | undefined,
  positions?: number[][],
  roles?: string[]
): { positions: number[][]; roles: string[] } | null {
  const pos = structure?.positions_nm || positions;
  if (!pos?.length) return null;
  let r = structure?.bead_roles || roles || [];
  if (r.length !== pos.length) {
    r = pos.map(() => "bead");
  }
  return { positions: pos, roles: r };
}

type Point3 = { x: number; y: number; z: number; role: string; index: number };

function rotateY(p: Point3, angle: number): Point3 {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  return { ...p, x: p.x * cos + p.z * sin, z: -p.x * sin + p.z * cos };
}

function rotateX(p: Point3, angle: number): Point3 {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  return { ...p, y: p.y * cos - p.z * sin, z: p.y * sin + p.z * cos };
}

export function drawBeadStructure(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  positions: number[][],
  roles: string[],
  rotation: { x: number; y: number }
): void {
  ctx.clearRect(0, 0, width, height);

  const cx = width / 2;
  const cy = height / 2;
  const scale = Math.min(width, height) * 0.35;

  let points: Point3[] = positions.map((p, index) => ({
    x: p[0] ?? 0,
    y: p[1] ?? 0,
    z: p[2] ?? 0,
    role: roles[index] || "bead",
    index,
  }));

  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  let minZ = Infinity;
  let maxZ = -Infinity;
  for (const p of points) {
    minX = Math.min(minX, p.x);
    maxX = Math.max(maxX, p.x);
    minY = Math.min(minY, p.y);
    maxY = Math.max(maxY, p.y);
    minZ = Math.min(minZ, p.z);
    maxZ = Math.max(maxZ, p.z);
  }
  const mx = (minX + maxX) / 2;
  const my = (minY + maxY) / 2;
  const mz = (minZ + maxZ) / 2;
  const span = Math.max(maxX - minX, maxY - minY, maxZ - minZ, 0.5);

  points = points.map((p) => {
    let q = { ...p, x: p.x - mx, y: p.y - my, z: p.z - mz };
    q = rotateY(q, rotation.y);
    q = rotateX(q, rotation.x);
    return q;
  });

  points.sort((a, b) => a.z - b.z);

  for (const p of points) {
    const px = cx + (p.x / span) * scale;
    const py = cy - (p.y / span) * scale;
    const r = beadRadius(p.role) * (1 + p.z / (span * 4));
    ctx.beginPath();
    ctx.fillStyle = beadColor(p.role);
    ctx.globalAlpha = 0.85 + (p.z / span) * 0.1;
    ctx.arc(px, py, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.strokeStyle = "rgba(255,255,255,0.15)";
    ctx.lineWidth = 1;
    ctx.stroke();
  }
}
