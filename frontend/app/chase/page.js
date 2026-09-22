import Link from "next/link";
import {getJson} from "../lib/api";

const money=x=>x==null?"—":`${Math.round(x).toLocaleString("sv-SE")} kr`;

export default async function ChasePage({searchParams}){
  const sp=await searchParams;
  const q=sp?.q||"";
  const budget=sp?.budget||"";
  const qs=new URLSearchParams();
  if(q)qs.set("q",q);
  if(budget)qs.set("budget",budget);
  const data=await getJson(`/chase/search?${qs.toString()}`,{results:[],count:0});
  const best=q?await getJson(`/chase/best-boxes?player=${encodeURIComponent(q)}${budget?`&budget=${encodeURIComponent(budget)}`:""}`,{results:[],count:0}):{results:[],count:0};
  return <main className="chaseSearchPage">
    <section className="chaseSearchHero">
      <span className="kicker">CHASE FINDER</span>
      <h1>Vilket kort vill du dra?</h1>
      <p>Sök på spelaren. BoxFinder visar vilka verifierade produkter som faktiskt innehåller kortet och vad de kostar.</p>
      <form className="chaseSearchForm">
        <input name="q" defaultValue={q} placeholder="t.ex. Matthew Schaefer, Demidov, McDavid"/>
        <input name="budget" defaultValue={budget} inputMode="numeric" placeholder="Maxbudget kr"/>
        <button>SÖK BOXAR →</button>
      </form>
    </section>
    {q&&<section className="bestBoxSection">
      <div className="sectionHead"><div><span className="kicker">BÄSTA BOXEN FÖR SPELAREN</span><h2>Vad ska jag köpa?</h2></div><p>{best.count||0} verifierade alternativ</p></div>
      {(best.results||[]).length?<div className="bestBoxGrid">{best.results.slice(0,5).map((x,i)=><Link className={`bestBoxPick ${i===0?"winner":""}`} href={`/product/${x.variant_id}`} key={x.variant_id}>
        <span className="bestBoxRank">#{i+1}</span><div><small>{i===0?(x.opportunity_score!=null?"BÄST ODDSUNDERLAG":"BÄST KARTLAGD"):"ALTERNATIV"}</small><h3>{x.product}</h3><p>{x.why}</p><div className="bestChases">{x.cards.slice(0,4).map((c,j)=><span key={j}><b>{c.tier}</b> {c.card}{c.number?` #${c.number}`:""}{c.probability_per_box!=null?` · ~${c.probability_per_box}%/box`:""}</span>)}</div></div><aside><strong>{money(x.price)}</strong><small>{x.store||"Pris saknas"}</small><b>{x.opportunity_score!=null?`${x.opportunity_score}/100`:"ODDS SAKNAS"}</b><small>Coverage {x.coverage_score}/100</small>{x.opportunity_per_1000_sek!=null&&<small>{x.opportunity_per_1000_sek} opportunity/1000 kr</small>}</aside>
      </Link>)}</div>:<div className="chaseEmpty"><b>Ingen verifierad boxmatchning inom filtret.</b><span>BoxFinder gissar inte checklistinnehåll.</span></div>}
      <p className="discoveryDisclaimer">{best.note}</p>
    </section>}
    <section className="chaseSearchResults">
      <div className="sectionHead"><div><span className="kicker">VERIFIERADE KOPPLINGAR</span><h2>{q?`Boxar för ${q}`:"Utforska chase-kort"}</h2></div><p>{data.count||0} kortträffar</p></div>
      {(data.results||[]).length ? <div className="chaseResultGrid">{data.results.map(card=><article className="chaseResult" key={card.id}>
        <div className="chaseResultCard"><small>{card.rookie?"ROOKIE CHASE":"CHASE CARD"}</small><h3>{card.player}</h3><b>{card.card}{card.number?` #${card.number}`:""}</b></div>
        <div className="chaseProductList">{card.products.map(x=><Link href={`/product/${x.variant_id}`} key={x.variant_id}>
          <div><small>{x.tier}</small><strong>{x.product}</strong><span>{x.odds}</span></div>
          <b>{money(x.price)} →</b>
        </Link>)}</div>
      </article>)}</div> : <div className="chaseEmpty"><b>Ingen verifierad träff.</b><span>Det betyder inte att spelaren saknas i alla produkter — bara att BoxFinder ännu inte har en verifierad checklistkoppling.</span></div>}
      <p className="discoveryDisclaimer">{data.note}</p>
    </section>
  </main>
}