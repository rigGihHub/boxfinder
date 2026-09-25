"use client";

import {useEffect, useRef, useState} from "react";
import ResaleResults, {loadResaleResult, saveResaleResult} from "./ResaleResults";

const MAX_ATTEMPTS = 2;

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
      setMessage(nextAttempt === 1 ? "Väcker analysmotorn…" : `Söker igen · försök ${nextAttempt}`);
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
        timer = window.setTimeout(recover, 2500);
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
    <ResaleResults query={query} data={cachedResult.data} cached/>
    {failed && <div className="rankingRetry"><span>{message}</span><button onClick={() => setRetryKey(value => value + 1)}>FÖRSÖK IGEN</button></div>}
  </div>;

  return <div className="chaseEmpty apiUnavailable" aria-live="polite">
    <b>BoxFinder startar analysmotorn.</b>
    <span>{message}</span>
    <div className="apiWakeProgress"><i/></div>
    <span>{failed ? "Den senast verifierade katalogen påverkas inte." : "Sökningen gör högst två försök innan du får ett tydligt felmeddelande."}</span>
    {failed && <button onClick={() => setRetryKey(value => value + 1)}>FÖRSÖK IGEN</button>}
  </div>;
}
