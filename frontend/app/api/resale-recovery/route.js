import {NextResponse} from "next/server";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const dynamic = "force-dynamic";

export async function GET(request) {
  const url = new URL(request.url);
  try {
    const response = await fetch(`${API}/rankings/resale${url.search}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(25000),
    });
    if (!response.ok) {
      return NextResponse.json({ready: false}, {status: 503});
    }
    const data = await response.json();
    return NextResponse.json(data, {headers: {"Cache-Control": "no-store"}});
  } catch {
    return NextResponse.json({ready: false}, {status: 503});
  }
}
