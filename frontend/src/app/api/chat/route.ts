import { NextResponse } from "next/server";

/** FastAPI base URL (no trailing slash). */
const BACKEND = (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
/** RAG + local LLM can take minutes on cold start; Next’s rewrite proxy times out much sooner. */
const CHAT_TIMEOUT_MS = Number(process.env.CHAT_PROXY_TIMEOUT_MS ?? 300_000);

export const dynamic = "force-dynamic";
export const maxDuration = 300;

export async function POST(request: Request) {
  let body: string;
  try {
    body = await request.text();
  } catch {
    return NextResponse.json({ detail: "Invalid request body" }, { status: 400 });
  }

  const url = `${BACKEND}/api/chat`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), CHAT_TIMEOUT_MS);

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timeout);

    const text = await res.text();
    const ct = res.headers.get("content-type") ?? "application/json";
    return new NextResponse(text, { status: res.status, headers: { "Content-Type": ct } });
  } catch (e: unknown) {
    clearTimeout(timeout);
    const name = e instanceof Error ? e.name : "";
    const msg = e instanceof Error ? e.message : String(e);
    const aborted = name === "AbortError" || /aborted/i.test(msg);

    return NextResponse.json(
      {
        detail: aborted
          ? `Chat request timed out after ${CHAT_TIMEOUT_MS / 1000}s. Try again—first load often downloads models and opens the vector DB.`
          : `Cannot reach the API at ${BACKEND}. In a separate terminal run:\n\`cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000\`\n(${msg})`,
      },
      { status: 503 },
    );
  }
}
