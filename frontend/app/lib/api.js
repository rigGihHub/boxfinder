const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getJson(path, fallback = null) {
  // Keep server rendering below the web request timeout. If the free API is
  // still asleep, client-side recovery keeps waking it without blocking the
  // whole page.
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const response = await fetch(`${API}${path}`, {
        cache: "no-store",
        signal: AbortSignal.timeout(10000),
      });
      if (response.ok) return await response.json();
      if (response.status < 500) return fallback;
    } catch {
      // The next attempt normally succeeds after the API has woken up.
    }
    if (attempt < 1) await new Promise(resolve => setTimeout(resolve, 750));
  }
  return fallback;
}

export { API };
