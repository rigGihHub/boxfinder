"use client";

import Link from "next/link";
import {useSearchParams} from "next/navigation";
import ResaleApiRecovery from "./ResaleApiRecovery";

const strategies = [
  ["balanced", "Bäst helhet"],
  ["jackpot", "Högsta möjliga träff"],
  ["frequent", "Bra träff oftare"],
];

export default function ResalePageClient() {
  const searchParams = useSearchParams();
  const strategy = searchParams.get("strategy") || "balanced";
  const category = searchParams.get("category") || "";
  const maxPrice = searchParams.get("max_price") || "";
  const qs = new URLSearchParams({strategy});
  if (category) qs.set("category", category);
  if (maxPrice) qs.set("max_price", maxPrice);
  qs.set("limit", "40");
  const query = qs.toString();

  return <main className="resalePage">
    <header className="productNav">
      <Link className="brand" href="/"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></Link>
      <Link className="backLink" href="/">← STARTSIDAN</Link>
      <span className="version">v0.48.0</span>
    </header>

    <section className="resaleHero">
      <span className="kicker">ALLA KATEGORIER · SAMMA MÅL</span>
      <h1>Bästa boxen att öppna<br/><em>för säljbar träff.</em></h1>
      <p>Hockey, fotboll, Pokémon, One Piece, Marvel och andra kategorier tävlar på samma lista. BoxFinder väger dokumenterade chase-kort, träfffrekvens, tak, pris och bevisstyrka.</p>
      <div className="resaleModes">{strategies.map(([value,label])=><Link className={strategy===value?"active":""} href={`?strategy=${value}${category?`&category=${encodeURIComponent(category)}`:""}${maxPrice?`&max_price=${maxPrice}`:""}`} key={value}>{label}</Link>)}</div>
      <form className="resaleFilters">
        <input type="hidden" name="strategy" value={strategy}/>
        <label><span>KATEGORI · VALFRITT</span><select name="category" defaultValue={category}><option value="">Alla kategorier</option><option>Hockey</option><option>Fotboll</option><option>Basket</option><option>NFL</option><option>Baseboll</option><option>F1</option><option>Pokémon</option><option>One Piece</option><option>Marvel</option><option>Disney</option><option>Magic</option><option>Lorcana</option></select></label>
        <label><span>MAXPRIS · VALFRITT</span><select name="max_price" defaultValue={maxPrice}><option value="">Ingen gräns</option><option value="100">100 kr</option><option value="250">250 kr</option><option value="500">500 kr</option><option value="1000">1 000 kr</option><option value="2000">2 000 kr</option><option value="5000">5 000 kr</option><option value="10000">10 000 kr</option></select></label>
        <button>RANKA ALLT →</button>
      </form>
    </section>

    <section className="resaleRanking">
      <div className="sectionHead"><div><span className="kicker">ÖPPNINGSRANKING</span><h2>Bäst säljpotential just nu</h2></div><p>Senaste resultat visas direkt och uppdateras i bakgrunden</p></div>
      <ResaleApiRecovery query={query}/>
    </section>
  </main>;
}
