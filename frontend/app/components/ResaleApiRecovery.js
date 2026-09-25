"use client";

import {useEffect, useRef, useState} from "react";
import ResaleResults, {loadResaleResult, saveResaleResult} from "./ResaleResults";

// Render's free service can need close to a minute to wake. Keep the verified
// local result visible while retrying long enough for a real cold start.
const MAX_ATTEMPTS = 6;
const RETRY_DELAY_MS = 1500;

export default function ResaleApiRecovery({query, refreshKey = 0, onLoadingChange}) {
  const [message, setMessage] = useState("Väcker analysmotorn…");
  const [result, setResult] = useState(null);
  const [cachedResult, setCachedResult] = useState(null);
  const [failed, setFailed] = useState(false);
  const [retryKey, setRetryKey] = useState(0);
  const stopped = useRef(false);
  const attempt = useRef(0);

  useEffect(() => {
    stopped.current = false;
    attempt.current = 0;
    setResult(null);
    setFailed(false);
    setCachedResult(loadResaleResult(query));
    onLoadingChange?.(true);
    let timer;

    async function recover() {
      const nextAttempt = attempt.current + 1;
      attempt.current = nextAttempt;
      setMessage(nextAttempt === 1
        ? "Väcker analysmotorn…"
        : `Söker igen · försök ${nextAttempt} av ${MAX_ATTEMPTS}`);
      try {
        const response = await fetch(`/api/resale-recovery?${query}`, {cache: "no-store"});
        if (response.ok) {
          const data = await response.json();
          if (Array.isArray(data.items)) {
            saveResaleResult(query, data);
            setResult(data);
            onLoadingChange?.(false);
            return;
          }
        }
      } catch {
        // A sleeping Render service is expected to fail during its first wake-up.
      }
      if (!stopped.current && nextAttempt < MAX_ATTEMPTS) {
        timer = window.setTimeout(recover, RETRY_DELAY_MS);
      } else if (!stopped.current) {
        setFailed(true);
        setMessage("API:t svarar inte just nu. Senast sparade ranking visas om den finns.");
        onLoadingChange?.(false);
      }
    }

    recover();
    return () => {
      stopped.current = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [query, refreshKey, retryKey, onLoadingChange]);

  if (result) return <ResaleResults query={query} data={result}/>;

  if (cachedResult) return <div aria-live="polite">
    <div className={`rankingRetry${failed ? " rankingRetryFailed" : ""}`}>
      <span>{failed ? message : `Hämtar en färsk ranking i bakgrunden · ${message}`}</span>
      {failed && <button onClick={() => setRetryKey(value => value + 1)}>FÖRSÖK IGEN</button>}
    </div>
    <ResaleResults query={query} data={cachedResult.data} cached/>
  </div>;

  return <div className="chaseEmpty apiUnavailable" aria-live="polite">
    <b>BoxFinder startar analysmotorn.</b>
    <span>{message}</span>
    <div className="apiWakeProgress"><i/></div>
    <span>{failed ? "Den senast verifierade katalogen påverkas inte." : "En helt avstängd tjänst kan behöva upp till ungefär en minut för att starta."}</span>
    {failed && <button onClick={() => setRetryKey(value => value + 1)}>FÖRSÖK IGEN</button>}
  </div>;
}
