"use client";

import {useEffect} from "react";
import ResaleResultCards from "./ResaleResultCards";

const cacheKey = query => `boxfinder:resale:${query}`;
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

export default function ResaleResults({query, data, cached = false}) {
  useEffect(() => {
    if (!cached) saveResaleResult(query, data);
  }, [cached, data, query]);

  return <>
    <p className="searchFreshness">
      {cached ? "Visar senast sparade sökning från " : "Sökning genomförd "}
      {formatTime(data.searched_at)}
      {cached ? " · uppdaterar i bakgrunden" : ` · ${data.count ?? data.items.length} rankade produkter`}
    </p>
    {data.items.length
      ? <ResaleResultCards items={data.items}/>
      : <div className="chaseEmpty"><b>Inga produkter matchar sökningen.</b><span>Ta bort kategori eller höj maxpriset.</span></div>}
  </>;
}
