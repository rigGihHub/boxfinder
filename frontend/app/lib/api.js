const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getJson(path, fallback = null) {
  // Render's free API can take more than ten seconds to wake. Retry because the
  // first request may fail while it is still starting.
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await fetch(`${API}${path}`, {
        cache: "no-store",
        signal: AbortSignal.timeout(25000),
      });
      if (response.ok) return await response.json();
      if (response.status < 500) return fallback;
    } catch {
      // The next attempt normally succeeds after the API has woken up.
    }
    if (attempt < 2) await new Promise(resolve => setTimeout(resolve, 900 * (attempt + 1)));
  }
  return fallback;
}

export { API };
