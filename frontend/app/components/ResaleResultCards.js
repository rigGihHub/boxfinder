"use client";

import Link from "next/link";

const money = value => value == null ? "—" : `${Math.round(value).toLocaleString("sv-SE")} kr`;

export default function ResaleResultCards({items}) {
  return <div className="resaleGrid">{items.map((x,i)=><article className={`resaleCard ${i===0?"resaleWinner":""}`} key={x.id}>
    <div className="resaleCardHead"><span>#{String(i+1).padStart(2,"0")}</span><div><small>{x.category} · {x.format}</small><h2>{x.name}</h2></div><aside><small>SÄLJPOTENTIAL</small><b>{x.resale_score}</b><span>/100</span></aside></div>
    <div className="resaleProof"><strong>{x.evidence_grade}</strong><span>Säkerhet {x.resale_confidence}/100</span><p>{x.ranking_basis}</p></div>
    <div className="resaleNumbers"><span><small>PRIS</small><b>{money(x.price)}</b></span><span><small>BRA TRÄFFAR OFTA</small><b>{x.opening_profile?.repeatable ?? "—"}/100</b></span><span><small>MAXTAK</small><b>{x.opening_profile?.ceiling ?? "—"}/100</b></span></div>
    <div className="resaleChases"><small>DET HÄR KAN DU SÄLJA VID TRÄFF</small>{x.sellable_chases?.slice(0,4).map((c,j)=><span key={j}><b>{c.tier}</b>{c.card}<em>{c.odds || "Exakt odds saknas"}</em></span>)}</div>
    <div className="resaleReasons">{x.resale_reasons?.map((r,j)=><span key={j}>✓ {r}</span>)}</div>
    <p className="resaleWarning">{x.resale_warning}</p>
    <div className="resaleActions"><Link href={`/product/${x.id}`}>SE HELA ANALYSEN →</Link>{x.chase_profile?.key_names?.[0]&&<Link href={`/chase?q=${encodeURIComponent(x.chase_profile.key_names[0].replace(/\s+#.*$/, ""))}`}>SÖK {x.chase_profile.key_names[0]} →</Link>}</div>
  </article>)}</div>;
}
