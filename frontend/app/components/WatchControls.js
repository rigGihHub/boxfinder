"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function WatchControls({ variantId, currentPrice }) {
  const [threshold, setThreshold] = useState(currentPrice ? Math.max(1, Math.floor(currentPrice * 0.9)) : "");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  async function addRule(triggerType) {
    setBusy(true);
    setStatus("");
    const body = { variant_id: variantId, trigger_type: triggerType };
    if (triggerType === "price_below") {
      const value = Number(threshold);
      if (!value || value <= 0) {
        setStatus("Ange en giltig prisgräns.");
        setBusy(false);
        return;
      }
      body.threshold_sek = value;
    }
    try {
      const res = await fetch(`${API}/watchlist/rules`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Kunde inte skapa bevakning.");
      setStatus(data.triggered_immediately ? "Bevakning skapad – prisgränsen är redan nådd." : "Bevakning skapad.");
    } catch (err) {
      setStatus(err.message || "Kunde inte skapa bevakning.");
    } finally {
      setBusy(false);
    }
  }

  return <div className="watchControls">
    <div className="watchThreshold">
      <label>MEDDELA MIG UNDER</label>
      <div><input type="number" min="1" step="1" value={threshold} onChange={e=>setThreshold(e.target.value)} /><span>kr</span><button disabled={busy} onClick={()=>addRule("price_below")}>BEVAKA PRIS</button></div>
    </div>
    <div className="watchQuick">
      <button disabled={busy} onClick={()=>addRule("back_in_stock")}>ÅTER I LAGER</button>
      <button disabled={busy} onClick={()=>addRule("new_90d_low")}>NYTT 90D-LÄGSTA</button>
      <button disabled={busy} onClick={()=>addRule("price_drop")}>NÄSTA PRISFALL</button>
    </div>
    {status && <p className="watchStatus">{status}</p>}
  </div>;
}
