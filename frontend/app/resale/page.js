import Link from "next/link";
import ResaleApiRecovery from "../components/ResaleApiRecovery";
import ResaleResultCards from "../components/ResaleResultCards";

const money = value => value == null ? "—" : `${Math.round(value).toLocaleString("sv-SE")} kr`;
const searched = value => value ? new Intl.DateTimeFormat("sv-SE", {dateStyle:"medium", timeStyle:"short", timeZone:"Europe/Stockholm"}).format(new Date(value)) : null;

const strategies = [
  ["balanced", "Bäst helhet"],
  ["jackpot", "Högsta möjliga träff"],
  ["frequent", "Bra träff oftare"],
];

async function getInitialRankings(path) {
  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  try {
    const response = await fetch(`${API}${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    if (response.ok) return await response.json();
  } catch {
    // Return the page immediately; the client recovery component wakes the API.
  }
  return {items: [], count: 0, disclaimer: "", unavailable: true};
}

export default async function ResalePage({searchParams}){
  const sp = await searchParams;
  const strategy = sp?.strategy || "balanced";
  const category = sp?.category || "";
  const maxPrice = sp?.max_price || "";
  const qs = new URLSearchParams({strategy});
  if(category) qs.set("category", category);
  if(maxPrice) qs.set("max_price", maxPrice);
  qs.set("limit", "40");
  const data = await getInitialRankings(`/rankings/resale?${qs.toString()}`);
  const items = data.items || [];

  return <main className="resalePage">
    <header className="productNav">
      <Link className="brand" href="/"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></Link>
      <Link className="backLink" href="/">← STARTSIDAN</Link>
      <span className="version">v0.46.1</span>
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
      <div className="sectionHead"><div><span className="kicker">ÖPPNINGSRANKING</span><h2>Bäst säljpotential just nu</h2></div><p>{data.count || 0} produkter med verifierad chase-profil</p></div>
      {data.searched_at&&<p className="searchFreshness">Sökning genomförd {searched(data.searched_at)}</p>}
      {items.length ? <ResaleResultCards items={items}/> : data.unavailable ? <ResaleApiRecovery query={qs.toString()}/> : <div className="chaseEmpty"><b>Ingen produkt kan rankas med de här filtren.</b><span>Ta bort kategori eller höj maxpriset. BoxFinder visar inte produkter utan verifierad chase-profil.</span></div>}
      <p className="resaleDisclaimer">{data.disclaimer}</p>
    </section>
  </main>
}
