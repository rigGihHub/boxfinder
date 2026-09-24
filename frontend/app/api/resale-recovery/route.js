import {NextResponse} from "next/server";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const dynamic = "force-dynamic";

const responseCache = globalThis.__boxfinderResaleResponseCache || new Map();
globalThis.__boxfinderResaleResponseCache = responseCache;

export async function GET(request) {
  const url = new URL(request.url);
  const cacheKey = url.search;
  try {
    const response = await fetch(`${API}/rankings/resale${url.search}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) {
      return NextResponse.json({ready: false}, {status: 503});
    }
    const data = await response.json();
    responseCache.set(cacheKey, data);
    return NextResponse.json(data, {headers: {"Cache-Control": "private, max-age=0"}});
  } catch {
    const cached = responseCache.get(cacheKey);
    if (cached) return NextResponse.json({...cached, stale: true});
    return NextResponse.json({ready: false}, {status: 503});
  }
}
