const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getJson(path, fallback = null) {
  try {
    const response = await fetch(`${API}${path}`, { cache: "no-store" });
    if (!response.ok) return fallback;
    return await response.json();
  } catch {
    return fallback;
  }
}

export { API };
