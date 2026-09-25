"use client";

import Link from "next/link";
import {useRouter, useSearchParams} from "next/navigation";
import {useState} from "react";
import ResaleApiRecovery from "./ResaleApiRecovery";

const strategies = [
  ["balanced", "Bäst helhet"],
  ["jackpot", "Högsta möjliga träff"],
  ["frequent", "Bra träff oftare"],
];

export default function ResalePageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [refreshKey, setRefreshKey] = useState(0);
  const [ranking, setRanking] = useState(false);
  const strategy = searchParams.get("strategy") || "balanced";
  const category = searchParams.get("category") || "";
  const maxPrice = searchParams.get("max_price") || "";
  const qs = new URLSearchParams({strategy});
  if (category) qs.set("category", category);
  if (maxPrice) qs.set("max_price", maxPrice);
  qs.set("limit", "40");
  const query = qs.toString();

  function runRanking(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const next = new URLSearchParams({strategy: String(form.get("strategy") || "balanced")});
    const nextCategory = String(form.get("category") || "");
    const nextMaxPrice = String(form.get("max_price") || "");
    if (nextCategory) next.set("category", nextCategory);
    if (nextMaxPrice) next.set("max_price", nextMaxPrice);

    setRanking(true);
    const current = new URLSearchParams({strategy});
    if (category) current.set("category", category);
    if (maxPrice) current.set("max_price", maxPrice);
    if (next.toString() === current.toString()) {
      setRefreshKey(value => value + 1);
    } else {
      router.push(`/resale?${next.toString()}`);
    }
    document.getElementById("resale-ranking")?.scrollIntoView({behavior: "smooth", block: "start"});
  }

  return <main className="resalePage">
    <header className="productNav">
      <Link className="brand" href="/"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></Link>
      <Link className="backLink" href="/">← STARTSIDAN</Link>
      <span className="version">v0.47.6</span>
    </header>

    <section className="resaleHero">
      <span className="kicker">ALLA KATEGORIER · SAMMA MÅL</span>
      <h1>Bästa boxen att öppna<br/><em>för säljbar träff.</em></h1>
      <p>Hockey, fotboll, Pokémon, One Piece, Marvel och andra kategorier tävlar på samma lista. BoxFinder väger dokumenterade chase-kort, träfffrekvens, tak, pris och bevisstyrka.</p>
      <div className="resaleModes">{strategies.map(([value,label])=><Link className={strategy===value?"active":""} href={`?strategy=${value}${category?`&category=${encodeURIComponent(category)}`:""}${maxPrice?`&max_price=${maxPrice}`:""}`} key={value}>{label}</Link>)}</div>
      <form className="resaleFilters" onSubmit={runRanking} aria-busy={ranking}>
        <input type="hidden" name="strategy" value={strategy}/>
        <label><span>KATEGORI · VALFRITT</span><select name="category" defaultValue={category}><option value="">Alla kategorier</option><option>Hockey</option><option>Fotboll</option><option>Basket</option><option>NFL</option><option>Baseboll</option><option>F1</option><option>Racing</option><option>Golf</option><option>UFC</option><option>WWE</option><option>Pokémon</option><option>One Piece</option><option>Magic</option><option>Disney</option><option>Marvel</option><option>Star Wars</option></select></label>
        <label><span>MAXPRIS · VALFRITT</span><select name="max_price" defaultValue={maxPrice}><option value="">Ingen gräns</option><option value="100">100 kr</option><option value="250">250 kr</option><option value="500">500 kr</option><option value="1000">1 000 kr</option><option value="2000">2 000 kr</option><option value="5000">5 000 kr</option><option value="10000">10 000 kr</option></select></label>
        <button type="submit" disabled={ranking}>{ranking ? "RANKAR…" : "RANKA ALLT →"}</button>
      </form>
    </section>

    <section className="resaleRanking" id="resale-ranking">
      <div className="sectionHead"><div><span className="kicker">ÖPPNINGSRANKING</span><h2>Bäst säljpotential just nu</h2></div><p>Senaste resultat visas direkt och uppdateras i bakgrunden</p></div>
      <ResaleApiRecovery query={query} refreshKey={refreshKey} onLoadingChange={setRanking}/>
    </section>
  </main>;
}
