import { NextResponse } from "next/server";

/** Render liveness probe — must return 200 as soon as the web server is up */
export async function GET() {
  return NextResponse.json({ status: "ok", service: "multiscale" });
}
