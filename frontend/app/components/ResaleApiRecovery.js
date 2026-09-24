"use client";

import {useEffect, useRef, useState} from "react";
import ResaleResultCards from "./ResaleResultCards";

export default function ResaleApiRecovery({query}) {
  const [message, setMessage] = useState("Väcker analysmotorn…");
  const [result, setResult] = useState(null);
  const stopped = useRef(false);
  const attempt = useRef(0);

  useEffect(() => {
    stopped.current = false;
    let timer;

    async function recover() {
      const nextAttempt = attempt.current + 1;
      attempt.current = nextAttempt;
      setMessage(nextAttempt === 1 ? "Väcker analysmotorn…" : `Söker igen · försök ${nextAttempt}`);
      try {
        const response = await fetch(`/api/resale-recovery?${query}`, {cache: "no-store"});
        if (response.ok) {
          const data = await response.json();
          if (Array.isArray(data.items)) { setResult(data); return; }
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

  if (result) return <>
    <p className="resaleDisclaimer">Analysen är klar · {result.count ?? result.items.length} rankade produkter</p>
    {result.items.length ? <ResaleResultCards items={result.items}/> : <div className="chaseEmpty"><b>Inga produkter matchar sökningen.</b><span>Ta bort kategori eller höj maxpriset.</span></div>}
  </>;

  return <div className="chaseEmpty apiUnavailable" aria-live="polite">
    <b>BoxFinder startar analysmotorn.</b>
    <span>{message}</span>
    <div className="apiWakeProgress"><i/></div>
    <span>Sökningen fortsätter automatiskt tills resultaten är klara.</span>
  </div>;
}
