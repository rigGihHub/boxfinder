"use client";

import {useEffect, useState} from "react";
import ResaleResultCards from "./ResaleResultCards";

const cacheKey = query => `boxfinder:resale:v8:${query}`;
const formatTime = value => value ? new Intl.DateTimeFormat("sv-SE", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Europe/Stockholm",
}).format(new Date(value)) : "nyss";

export function saveResaleResult(query, data) {
  try {
    window.localStorage.setItem(cacheKey(query), JSON.stringify({data, saved_at: new Date().toISOString()}));
  } catch {
    // Results still work when storage is disabled.
  }
}

export function loadResaleResult(query) {
  try {
    const cached = JSON.parse(window.localStorage.getItem(cacheKey(query)) || "null");
    if (cached?.data && Array.isArray(cached.data.items)) return cached;
  } catch {
    // Ignore malformed or unavailable browser storage.
  }
  return null;
}

export default function ResaleResults({query, data, cached = false, updating = false}) {
  const [displayed, setDisplayed] = useState(data.items);
  const [loadingMore, setLoadingMore] = useState(false);
  const [moreError, setMoreError] = useState(false);
  useEffect(() => { setDisplayed(data.items); setMoreError(false); }, [data, query]);
  useEffect(() => {
    if (!cached) saveResaleResult(query, data);
  }, [cached, data, query]);

  const now = Date.now();
  const items = displayed.filter(item => {
    const t = item.observed_at;
    const observed = t ? new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(t) ? t : `${t}Z`).getTime() : NaN;
    return Number.isFinite(observed) && observed <= now && now - observed <= 14 * 86400000;
  });

  async function loadMore() {
    setLoadingMore(true);
    setMoreError(false);
    try {
      const params = new URLSearchParams(query);
      params.set("offset", String(displayed.length));
      const response = await fetch(`/api/resale-recovery?${params}`, {cache: "no-store"});
      if (!response.ok) throw new Error("Ranking unavailable");
      const next = await response.json();
      if (next.stale || !Array.isArray(next.items) || !next.items.length) throw new Error("No current page");
      setDisplayed(current => [...current, ...next.items.filter(item => !current.some(existing => existing.id === item.id))]);
    } catch { setMoreError(true); }
    finally { setLoadingMore(false); }
  }

  return <>
    <p className="searchFreshness">
      {cached ? "Visar senast sparade sökning från " : "Sökning genomförd "}
      {formatTime(data.searched_at)}
      {cached
        ? (updating ? " · uppdaterar i bakgrunden" : " · uppdateringen misslyckades")
        : ` · ${data.count ?? data.items.length} rankade produkter`}
    </p>
    <p className="resultFreshness">Butiksuppgifter högst 14 dagar gamla. En ny sökning innebär inte en ny butikskontroll. Priser, budget och ranking är exklusive frakt.</p>
    {items.length
      ? <ResaleResultCards items={items}/>
      : <div className="chaseEmpty"><b>Inga aktuella köpalternativ matchar sökningen.</b><span>Ta bort butiks- eller kategorifiltret, eller höj maxpriset. Produkter med butiksuppgifter äldre än 14 dagar visas inte i rankningen.</span></div>}
    {!cached && displayed.length < data.count && <div className="rankingRetry">
      <span>{displayed.length} av {data.count} produkter visas{moreError ? " · kunde inte hämta fler, försök igen" : ""}</span>
      <button type="button" disabled={loadingMore} onClick={loadMore}>{loadingMore ? "HÄMTAR…" : "VISA FLER →"}</button>
    </div>}
  </>;
}
