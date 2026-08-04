import { NextRequest, NextResponse } from "next/server";

function apiBase(): string {
  return (
    process.env.API_INTERNAL_URL ||
    process.env.MULTISCALE_API_URL ||
    "http://127.0.0.1:8000"
  );
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  const base = apiBase();
  const url = `${base}/health/${path.join("/")}${request.nextUrl.search}`;
  const res = await fetch(url, { cache: "no-store" });
  const body = await res.text();
  return new NextResponse(body, {
    status: res.status,
    headers: { "content-type": res.headers.get("content-type") || "application/json" },
  });
}
