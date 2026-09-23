import Link from "next/link";
import {getJson} from "../lib/api";

const money = value => value == null ? "—" : `${Math.round(value).toLocaleString("sv-SE")} kr`;

const strategies = [
  ["balanced", "Bäst helhet"],
  ["jackpot", "Högsta möjliga träff"],
  ["frequent", "Bra träff oftare"],
];

export default async function ResalePage({searchParams}){
  const sp = await searchParams;
  const strategy = sp?.strategy || "balanced";
  const category = sp?.category || "";
  const maxPrice = sp?.max_price || "";
  const qs = new URLSearchParams({strategy});
  if(category) qs.set("category", category);
  if(maxPrice) qs.set("max_price", maxPrice);
  qs.set("limit", "40");
  const data = await getJson(`/rankings/resale?${qs.toString()}`, {items:[], count:0, disclaimer:""});
  const items = data.items || [];

  return <main className="resalePage">
    <header className="productNav">
      <Link className="brand" href="/"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></Link>
      <Link className="backLink" href="/">← STARTSIDAN</Link>
      <span className="version">v0.45.0</span>
    </header>

    <section className="resaleHero">
      <span className="kicker">ALLA KATEGORIER · SAMMA MÅL</span>
      <h1>Bästa boxen att öppna<br/><em>för säljbar träff.</em></h1>
      <p>Hockey, fotboll, Pokémon, One Piece, Marvel och andra kategorier tävlar på samma lista. BoxFinder väger dokumenterade chase-kort, träfffrekvens, tak, pris och bevisstyrka.</p>
      <div className="resaleModes">{strategies.map(([value,label])=><Link className={strategy===value?"active":""} href={`?strategy=${value}${category?`&category=${encodeURIComponent(category)}`:""}${maxPrice?`&max_price=${maxPrice}`:""}`} key={value}>{label}</Link>)}</div>
      <form className="resaleFilters">
        <input type="hidden" name="strategy" value={strategy}/>
        <label><span>KATEGORI · VALFRITT</span><select name="category" defaultValue={category}><option value="">Alla kategorier</option><option>Hockey</option><option>Fotboll</option><option>Basket</option><option>NFL</option><option>Baseboll</option><option>F1</option><option>Pokémon</option><option>One Piece</option><option>Marvel</option><option>Magic</option><option>Lorcana</option></select></label>
        <label><span>MAXPRIS · VALFRITT</span><select name="max_price" defaultValue={maxPrice}><option value="">Ingen gräns</option><option value="250">250 kr</option><option value="500">500 kr</option><option value="1000">1 000 kr</option><option value="2000">2 000 kr</option><option value="5000">5 000 kr</option><option value="10000">10 000 kr</option></select></label>
        <button>RANKA ALLT →</button>
      </form>
    </section>

    <section className="resaleRanking">
      <div className="sectionHead"><div><span className="kicker">ÖPPNINGSRANKING</span><h2>Bäst säljpotential just nu</h2></div><p>{data.count || 0} produkter med verifierad chase-profil</p></div>
      {items.length ? <div className="resaleGrid">{items.map((x,i)=><article className={`resaleCard ${i===0?"resaleWinner":""}`} key={x.id}>
        <div className="resaleCardHead"><span>#{String(i+1).padStart(2,"0")}</span><div><small>{x.category} · {x.format}</small><h2>{x.name}</h2></div><aside><small>SÄLJPOTENTIAL</small><b>{x.resale_score}</b><span>/100</span></aside></div>
        <div className="resaleProof"><strong>{x.evidence_grade}</strong><span>Säkerhet {x.resale_confidence}/100</span><p>{x.ranking_basis}</p></div>
        <div className="resaleNumbers"><span><small>PRIS</small><b>{money(x.price)}</b></span><span><small>BRA TRÄFFAR OFTA</small><b>{x.opening_profile?.repeatable ?? "—"}/100</b></span><span><small>MAXTAK</small><b>{x.opening_profile?.ceiling ?? "—"}/100</b></span></div>
        <div className="resaleChases"><small>DET HÄR KAN DU SÄLJA VID TRÄFF</small>{x.sellable_chases?.slice(0,4).map((c,j)=><span key={j}><b>{c.tier}</b>{c.card}<em>{c.odds || "Exakt odds saknas"}</em></span>)}</div>
        <div className="resaleReasons">{x.resale_reasons?.map((r,j)=><span key={j}>✓ {r}</span>)}</div>
        <p className="resaleWarning">{x.resale_warning}</p>
        <div className="resaleActions"><Link href={`/product/${x.id}`}>SE HELA ANALYSEN →</Link>{x.chase_profile?.key_names?.[0]&&<Link href={`/chase?q=${encodeURIComponent(x.chase_profile.key_names[0].replace(/\s+#.*$/, ""))}`}>SÖK {x.chase_profile.key_names[0]} →</Link>}</div>
      </article>)}</div> : <div className="chaseEmpty"><b>Ingen produkt kan rankas med de här filtren.</b><span>Ta bort kategori eller höj maxpriset. BoxFinder visar inte produkter utan verifierad chase-profil.</span></div>}
      <p className="resaleDisclaimer">{data.disclaimer}</p>
    </section>
  </main>
}
