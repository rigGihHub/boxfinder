"use client";

import Link from "next/link";

const money = value => value == null ? "—" : `${Math.round(value).toLocaleString("sv-SE")} kr`;
const checked = value => value ? new Intl.DateTimeFormat("sv-SE", {dateStyle:"short", timeStyle:"short", timeZone:"Europe/Stockholm"}).format(new Date(value)) : "tid saknas";

export default function ResaleResultCards({items}) {
  return <div className="resaleGrid">{items.map((x,i)=><article className={`resaleCard ${i===0?"resaleWinner":""}`} key={x.id}>
    <div className="resaleCardHead"><span>#{String(i+1).padStart(2,"0")}</span><div><small>{x.category} · {x.format}</small><h2>{x.name}</h2></div><aside><small>{x.score_label || "ÖPPNINGSPOTENTIAL"}</small><b>{x.resale_score}</b><span>/100</span></aside></div>
    <div className="resaleProof"><strong>{x.evidence_grade}</strong><span>Underlag {x.resale_confidence}/100</span><p>{x.ranking_basis}</p></div>
    <div className="resaleNumbers"><span><small>PRIS EXKL. FRAKT</small><b>{money(x.price)}</b></span><span><small>ÅTERKOMMANDE INNEHÅLL</small><b>{x.opening_profile?.repeatable ?? "—"}/100</b></span><span><small>MAXTAK</small><b>{x.opening_profile?.ceiling ?? "—"}/100</b></span></div>
    {x.frequency_basis && <p className="frequencyBasis">{x.frequency_basis}</p>}
    {x.format_hits?.length > 0 && <div className="packageContents">
      <strong>UPPGIVET INNEHÅLL I DENNA FÖRPACKNING</strong>
      <ul>{x.format_hits.map((fact,j)=><li key={j}>{fact.basis === "guaranteed" ? "Garanterat" : "I genomsnitt"}: {fact.count.toLocaleString("sv-SE")} {fact.family}.</li>)}</ul>
      <p>Genomsnitt är ingen garanti för en enskild öppning. Uppgifter för en hel box gäller inte ett löspaket. Korttyp eller raritet säger inte vad kortet är värt.</p>
      {x.chase_profile?.source_url && <a href={x.chase_profile.source_url} target="_blank" rel="noreferrer">Källa: {x.chase_profile.source_name || "innehållsuppgift"} ↗</a>}
    </div>}
    <div className="resaleChases"><small>MÖJLIGA TOPPTRÄFFAR</small>{x.sellable_chases?.slice(0,4).map((c,j)=><span key={j}><b>{c.tier}</b>{c.card}<em>{c.odds || "Exakt odds saknas"}</em></span>)}</div>
    <div className="resaleReasons">{x.resale_reasons?.map((r,j)=><span key={j}>✓ {r}</span>)}</div>
    <p className="resaleWarning">{x.resale_warning}</p>
    <p className="resultFreshness">Butiksuppgift kontrollerad {checked(x.observed_at)}</p>
    <div className="resaleActions">{x.url&&<a className="buyDirect" href={x.url} target="_blank" rel="noreferrer">KÖP HOS {x.store?.toUpperCase()} ↗</a>}<Link href={`/product/${x.id}`}>SE HELA ANALYSEN →</Link>{x.chase_profile?.key_names?.[0]&&<Link href={`/chase?q=${encodeURIComponent(x.chase_profile.key_names[0].replace(/\s+#.*$/, ""))}`}>SÖK {x.chase_profile.key_names[0]} →</Link>}</div>
  </article>)}</div>;
}
