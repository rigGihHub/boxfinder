"use client";

import {useEffect, useRef, useState} from "react";
import ResaleResults, {loadResaleResult, saveResaleResult} from "./ResaleResults";

export default function ResaleApiRecovery({query}) {
  const [message, setMessage] = useState("Väcker analysmotorn…");
  const [result, setResult] = useState(null);
  const [cachedResult, setCachedResult] = useState(null);
  const stopped = useRef(false);
  const attempt = useRef(0);

  useEffect(() => {
    stopped.current = false;
    setCachedResult(loadResaleResult(query));
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
            return;
          }
        }
      } catch {
        // A sleeping Render service is expected to fail during its first wake-up.
      }
      if (!stopped.current) timer = window.setTimeout(recover, 2500);
    }

    recover();
    return () => {
      stopped.current = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [query]);

  if (result) return <ResaleResults query={query} data={result}/>;

  if (cachedResult) return <div aria-live="polite">
    <ResaleResults query={query} data={cachedResult.data} cached/>
  </div>;

  return <div className="chaseEmpty apiUnavailable" aria-live="polite">
    <b>BoxFinder startar analysmotorn.</b>
    <span>{message}</span>
    <div className="apiWakeProgress"><i/></div>
    <span>Sökningen fortsätter automatiskt tills resultaten är klara.</span>
  </div>;
}
