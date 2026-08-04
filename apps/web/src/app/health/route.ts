import { NextResponse } from "next/server";

function apiBase(): string {
  return (
    process.env.API_INTERNAL_URL ||
    process.env.MULTISCALE_API_URL ||
    "http://127.0.0.1:8000"
  );
}

/** Render health check hits /health on the web service */
export async function GET() {
  try {
    const res = await fetch(`${apiBase()}/health`, { cache: "no-store" });
    const body = await res.text();
    return new NextResponse(body, {
      status: res.status,
      headers: { "content-type": "application/json" },
    });
  } catch {
    return NextResponse.json({ status: "degraded", service: "multiscale-web" }, { status: 503 });
  }
}
