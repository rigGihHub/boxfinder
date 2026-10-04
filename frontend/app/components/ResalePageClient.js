"use client";

import Link from "next/link";
import {useRouter, useSearchParams} from "next/navigation";
import {useState} from "react";
import ResaleApiRecovery from "./ResaleApiRecovery";
import knownStores from "../data/ranking-stores.json";

const strategies = [
  ["value", "Mest för pengarna"],
  ["balanced", "Öppningspotential"],
  ["jackpot", "Högsta möjliga träff"],
  ["frequent", "Bra träff oftare"],
];

export default function ResalePageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [refreshKey, setRefreshKey] = useState(0);
  const [ranking, setRanking] = useState(false);
  const [stores, setStores] = useState(() => knownStores.map(name => ({name})));
  const [coverage, setCoverage] = useState(null);
  const strategy = searchParams.get("strategy") || "value";
  const category = searchParams.get("category") || "";
  const storeId = searchParams.get("store_id") || "";
  const storeName = searchParams.get("store_name") || "";
  const storeValue = storeName || (storeId ? `id:${storeId}` : "");
  const maxPrice = searchParams.get("max_price") || "";
  const qs = new URLSearchParams({strategy});
  if (storeName) qs.set("store_name", storeName);
  if (!storeName && storeId) qs.set("store_id", storeId);
  if (category) qs.set("category", category);
  if (maxPrice) qs.set("max_price", maxPrice);
  qs.set("limit", storeValue ? "100" : "40");
  const query = qs.toString();

  function runRanking(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const next = new URLSearchParams({strategy: String(form.get("strategy") || "value")});
    const nextCategory = String(form.get("category") || "");
    const nextMaxPrice = String(form.get("max_price") || "");
    const nextStore = String(form.get("store") || "");
    if (nextStore.startsWith("id:")) next.set("store_id", nextStore.slice(3));
    else if (nextStore) next.set("store_name", nextStore);
    if (nextCategory) next.set("category", nextCategory);
    if (nextMaxPrice) next.set("max_price", nextMaxPrice);

    setRanking(true);
    const current = new URLSearchParams({strategy});
    if (storeName) current.set("store_name", storeName);
    else if (storeId) current.set("store_id", storeId);
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
      <Link className="brand" href="/" prefetch={false}><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></Link>
      <Link className="backLink" href="/" prefetch={false}>← STARTSIDAN</Link>
      <span className="version">v0.59.0</span>
    </header>

    <section className="resaleHero">
      <span className="kicker">ALLA KATEGORIER · SAMMA MÅL</span>
      <h1>Mest för pengarna<br/><em>när du öppnar kort.</em></h1>
      <p>Vi jämför inköpspriset med möjliga kort och uppgivet innehåll i den förpackning du köper. Antal paket ger inga egna poäng. Betyget är en bedömning av innehåll för pengarna, inte förväntad vinst.</p>
      <div className="resaleModes">{strategies.map(([value,label])=><Link className={strategy===value?"active":""} href={`?strategy=${value}${storeName?`&store_name=${encodeURIComponent(storeName)}`:storeId?`&store_id=${encodeURIComponent(storeId)}`:""}${category?`&category=${encodeURIComponent(category)}`:""}${maxPrice?`&max_price=${maxPrice}`:""}`} key={value}>{label}</Link>)}</div>
      <form key={`${category}:${maxPrice}:${storeValue}`} className="resaleFilters" onSubmit={runRanking} aria-busy={ranking}>
        <input type="hidden" name="strategy" value={strategy}/>
        <label><span>BUTIK · VALFRITT</span><select name="store" defaultValue={storeValue}>
          <option value="">Alla butiker</option>
          {storeId && !storeName && <option value={`id:${storeId}`}>{stores.find(store => String(store.id) === storeId)?.name || "Vald butik"}</option>}
          {storeName && !stores.some(store => store.name === storeName) && <option value={storeName}>{storeName}</option>}
          {stores.map(store => <option value={store.name} key={store.name}>{store.name}</option>)}
        </select></label>
        <label><span>KATEGORI · VALFRITT</span><select name="category" defaultValue={category}><option value="">Alla kategorier</option><option>Hockey</option><option>Fotboll</option><option>Basket</option><option>NFL</option><option>Baseboll</option><option>Tennis</option><option>F1</option><option>Racing</option><option>Golf</option><option>UFC</option><option>WWE</option><option>Pokémon</option><option>One Piece</option><option>Magic</option><option>Lorcana</option><option>Disney</option><option>Marvel</option><option>Star Wars</option><option>Yu-Gi-Oh</option><option>Star Wars Unlimited</option><option>Dragon Ball</option><option>Digimon</option><option>Riftbound</option><option>Final Fantasy</option><option>Naruto</option><option>Universus</option><option>Gundam</option></select></label>
        <label><span>MAXPRIS EXKL. FRAKT · VALFRITT</span><select name="max_price" defaultValue={maxPrice}><option value="">Ingen gräns</option><option value="100">100 kr</option><option value="250">250 kr</option><option value="500">500 kr</option><option value="1000">1 000 kr</option><option value="2000">2 000 kr</option><option value="5000">5 000 kr</option><option value="10000">10 000 kr</option></select></label>
        <button type="submit">RANKA ALLT →</button>
      </form>
      <p className="costBasisHelp">Alla priser, budgetgränser och rankingpoäng är exklusive frakt.</p>
      {coverage && <details className="storeCoverage">
        <summary>Butikstäckning · {coverage.rankable_products} rankbara produkter · {coverage.current_store_offers} köpbara erbjudanden · {coverage.stores} butiker</summary>
        <p>Hela den rankbara katalogen, oavsett valda filter. Samma produkt kan finnas hos flera butiker. Produkter skiljs åt efter format och språk. Endast erbjudanden med verifierad direktlänk, lagerstatus och pris kontrollerat under de senaste 14 dagarna räknas. Katalogen täcker ännu inte butikernas hela sortiment.</p>
        <div className="storeCoverageTable"><table>
          <thead><tr><th scope="col">Butik</th><th scope="col">Produkter</th><th scope="col">Erbjudanden</th></tr></thead>
          <tbody>{stores.map(store => <tr key={store.id}><th scope="row">{store.name}</th><td>{store.product_count}</td><td>{store.offer_count}</td></tr>)}</tbody>
        </table></div>
      </details>}
    </section>

    <section className="resaleRanking" id="resale-ranking">
      <div className="sectionHead"><div><span className="kicker">BOXFINDERS RANKING</span><h2>{strategy === "value" ? "Mest innehåll för pengarna" : "Bäst öppningspotential just nu"}</h2></div><p>Senaste resultat visas direkt och uppdateras i bakgrunden</p></div>
      <ResaleApiRecovery query={query} refreshKey={refreshKey} onLoadingChange={setRanking} onStoresChange={setStores} onCoverageChange={setCoverage}/>
    </section>
  </main>;
}
