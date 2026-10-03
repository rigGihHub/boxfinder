"use client";

import {useEffect, useRef, useState} from "react";
import ResaleResults, {loadResaleResult, saveResaleResult} from "./ResaleResults";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Both Render services can sleep. The browser must wake the API directly;
// proxy retries alone may return 503 without starting the sleeping API.
const MAX_ATTEMPTS = 30;
const MAX_RECOVERY_MS = 90000;
const RETRY_DELAY_MS = 3000;

export default function ResaleApiRecovery({query, refreshKey = 0, onLoadingChange, onStoresChange}) {
  const [message, setMessage] = useState("Väcker analysmotorn…");
  const [result, setResult] = useState(null);
  const [cachedResult, setCachedResult] = useState(null);
  const [failed, setFailed] = useState(false);
  const [retryKey, setRetryKey] = useState(0);
  const attempt = useRef(0);

  useEffect(() => {
    let cancelled = false;
    const startedAt = Date.now();
    attempt.current = 0;
    setResult(null);
    setFailed(false);
    const cached = loadResaleResult(query);
    setCachedResult(cached);
    if (cached?.data?.available_stores) onStoresChange?.(cached.data.available_stores);
    onLoadingChange?.(true);
    let timer;

    // This cross-origin no-cors request is intentionally fire-and-forget. Its
    // only job is to reach Render's public API hostname and start the service.
    void fetch(`${API}/health?wake=${Date.now()}`, {
      cache: "no-store",
      mode: "no-cors",
    }).catch(() => {});

    async function recover() {
      const nextAttempt = attempt.current + 1;
      attempt.current = nextAttempt;
      setMessage(nextAttempt === 1
        ? "Väcker analysmotorn…"
        : `Söker igen · ${Math.round((Date.now() - startedAt) / 1000)} sekunder`);
      try {
        const response = await fetch(`/api/resale-recovery?${query}`, {
          cache: "no-store",
          signal: AbortSignal.timeout(12000),
        });
        if (response.ok) {
          const data = await response.json();
          if (cancelled) return;
          if (Array.isArray(data.items) && !data.stale) {
            if (data.available_stores) onStoresChange?.(data.available_stores);
            saveResaleResult(query, data);
            setResult(data);
            onLoadingChange?.(false);
            return;
          }
          if (Array.isArray(data.items) && data.stale) {
            setCachedResult({data});
          }
        }
      } catch {
        // A sleeping Render service is expected to fail during its first wake-up.
      }
      if (!cancelled && nextAttempt < MAX_ATTEMPTS && Date.now() - startedAt < MAX_RECOVERY_MS) {
        timer = window.setTimeout(recover, RETRY_DELAY_MS);
      } else if (!cancelled) {
        setFailed(true);
        setMessage("API:t svarar inte just nu. Senast sparade ranking visas om den finns.");
        onLoadingChange?.(false);
      }
    }

    recover();
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [query, refreshKey, retryKey, onLoadingChange, onStoresChange]);

  if (result) return <ResaleResults query={query} data={result}/>;

  if (cachedResult) return <div aria-live="polite">
    <div className={`rankingRetry${failed ? " rankingRetryFailed" : ""}`}>
      <span>{failed ? message : `Hämtar en färsk ranking i bakgrunden · ${message}`}</span>
      {failed && <button onClick={() => setRetryKey(value => value + 1)}>FÖRSÖK IGEN</button>}
    </div>
    <ResaleResults query={query} data={cachedResult.data} cached updating={!failed}/>
  </div>;

  return <div className="chaseEmpty apiUnavailable" aria-live="polite">
    <b>BoxFinder startar analysmotorn.</b>
    <span>{message}</span>
    <div className="apiWakeProgress"><i/></div>
    <span>{failed ? "Den senast verifierade katalogen påverkas inte." : "En helt avstängd tjänst kan behöva drygt en minut för att starta."}</span>
    {failed && <button onClick={() => setRetryKey(value => value + 1)}>FÖRSÖK IGEN</button>}
  </div>;
}
