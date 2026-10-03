"use client";

import {useEffect} from "react";
import ResaleResultCards from "./ResaleResultCards";

const cacheKey = query => `boxfinder:resale:v3:${query}`;
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
  useEffect(() => {
    if (!cached) saveResaleResult(query, data);
  }, [cached, data, query]);

  const now = Date.now();
  const items = data.items.filter(item => {
    const t = item.observed_at;
    const observed = t ? new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(t) ? t : `${t}Z`).getTime() : NaN;
    return Number.isFinite(observed) && observed <= now && now - observed <= 14 * 86400000;
  });

  return <>
    <p className="searchFreshness">
      {cached ? "Visar senast sparade sökning från " : "Sökning genomförd "}
      {formatTime(data.searched_at)}
      {cached
        ? (updating ? " · uppdaterar i bakgrunden" : " · uppdateringen misslyckades")
        : ` · ${data.count ?? data.items.length} rankade produkter`}
    </p>
    <p className="resultFreshness">Butiksuppgifter högst 14 dagar gamla. En ny sökning innebär inte en ny butikskontroll. Frakt ingår inte i prisjämförelsen.</p>
    {items.length
      ? <ResaleResultCards items={items}/>
      : <div className="chaseEmpty"><b>Inga aktuella köpalternativ matchar sökningen.</b><span>Ta bort kategori eller höj maxpriset. Produkter med butiksuppgifter äldre än 14 dagar visas inte i rankningen.</span></div>}
  </>;
}
