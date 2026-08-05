import { NextResponse } from "next/server";

/** Render liveness probe — web server plus API process availability */
export async function GET() {
  const apiUrl = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";
  try {
    const res = await fetch(`${apiUrl}/health`, {
      signal: AbortSignal.timeout(5000),
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json(
        { status: "degraded", service: "multiscale", api: "unhealthy" },
        { status: 503 },
      );
    }
    return NextResponse.json({ status: "ok", service: "multiscale" });
  } catch {
    return NextResponse.json(
      { status: "degraded", service: "multiscale", api: "unreachable" },
      { status: 503 },
    );
  }
}
