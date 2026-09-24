"use client";

import {useEffect, useRef, useState} from "react";

export default function ResaleApiRecovery({query}) {
  const [message, setMessage] = useState("Väcker analysmotorn…");
  const stopped = useRef(false);
  const attempt = useRef(0);

  useEffect(() => {
    stopped.current = false;
    let timer;

    async function recover() {
      const nextAttempt = attempt.current + 1;
      attempt.current = nextAttempt;
      setMessage(nextAttempt === 1 ? "Väcker analysmotorn…" : `Kontrollerar igen · försök ${nextAttempt}`);
      try {
        const response = await fetch(`/api/resale-recovery?${query}`, {cache: "no-store"});
        if (response.ok) {
          const data = await response.json();
          if (Array.isArray(data.items)) {
            setMessage(`Analysmotorn är klar · ${data.count ?? data.items.length} produkter hittades`);
            window.location.reload();
            return;
          }
        }
      } catch {
        // A sleeping Render service is expected to fail during its first wake-up.
      }
      if (!stopped.current) timer = window.setTimeout(recover, 2000);
    }

    recover();
    return () => {
      stopped.current = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [query]);

  return <div className="chaseEmpty apiUnavailable" aria-live="polite">
    <b>BoxFinder startar analysmotorn.</b>
    <span>{message}</span>
    <div className="apiWakeProgress"><i/></div>
    <button type="button" onClick={() => window.location.reload()}>LADDA OM NU →</button>
  </div>;
}
