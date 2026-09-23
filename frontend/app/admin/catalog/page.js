const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getJson(path, fallback) {
  try {
    const r = await fetch(`${API}${path}`, { cache:"no-store" });
    return r.ok ? await r.json() : fallback;
  } catch { return fallback; }
}

function money(v) {
  if (v == null) return "Pris saknas";
  return new Intl.NumberFormat("sv-SE", { style:"currency", currency:"SEK", maximumFractionDigits:0 }).format(v);
}

export default async function CatalogAdmin() {
  const [items, stats, clusters] = await Promise.all([
    getJson("/admin/catalog-candidates?sealed_only=true&limit=250", []),
    getJson("/admin/catalog-candidates/stats", {}),
    getJson("/admin/catalog-clusters?status=new", []),
  ]);
  const multiStore = clusters.filter(x=>x.multi_store);

  return <main className="catalogAdmin">
    <header className="nav sourceNav">
      <a className="brand" href="/"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></a>
      <nav><a href="/">Startsida</a><a href="/admin/source-hub">Datakällor</a><a href="/admin/catalog">Produktkö</a><a href="/admin/intake">Koppla butik</a><a href="/admin/intake/batch">Batch</a></nav>
      <span className="version">v0.40.0</span>
    </header>

    <section className="catalogHero">
      <span className="kicker">SWEDISH SEALED DISCOVERY</span>
      <h1>Nya produkter<br/><em>utan gissningar.</em></h1>
      <p>När en butik eller feed innehåller en produkt som BoxFinder inte säkert kan matcha hamnar den här. Produkten får finnas i upptäcktskön innan den får påverka ranking eller prisjämförelser.</p>
    </section>

    <section className="catalogStats">
      <article><small>ALLA KANDIDATER</small><b>{stats.total ?? 0}</b></article>
      <article><small>SEALED</small><b>{stats.sealed_candidates ?? 0}</b></article>
      <article><small>RANDOMISERADE</small><b>{stats.randomized ?? 0}</b></article>
      <article><small>NYA ATT GRANSKA</small><b>{stats.new_for_review ?? 0}</b></article>
    </section>

    <section className="catalogRules">
      <b>Så fungerar spärren</b>
      <span>CASE ≠ BOX</span><span>BOX ≠ PACK</span><span>ETB ≠ BOOSTER BOX</span><span>TILLBEHÖR ≠ SEALED PRODUKT</span>
    </section>

    <section className="dedupSection">
      <div className="sectionHead"><div><span className="kicker">AUTO-DEDUP</span><h2>Samma produkt hos flera butiker</h2></div><p>{multiStore.length} grupper hittade</p></div>
      {multiStore.length === 0 ? <div className="candidateEmpty"><b>Inga flerbutiksgrupper ännu.</b><p>När samma okända sealed-produkt hittas hos flera butiker grupperas den här innan en gemensam BoxFinder-produkt skapas.</p></div> :
      <div className="dedupGrid">
        {multiStore.slice(0,50).map(x=><article className="dedupCard" key={x.fingerprint}>
          <div className="dedupTop"><span>{x.store_count} BUTIKER</span><span>{x.candidate_count} TRÄFFAR</span></div>
          <h3>{x.titles[0]}</h3>
          <div className="candidateTags">
            {x.category_hint && <span>{x.category_hint}</span>}
            {x.format && <span>{x.format}</span>}
            {x.year_season && <span>{x.year_season}</span>}
            {x.language && <span>{x.language}</span>}
          </div>
          <p className="dedupPrice">{x.min_price_sek != null ? money(x.min_price_sek) : "Pris saknas"}{x.max_price_sek && x.max_price_sek !== x.min_price_sek ? ` – ${money(x.max_price_sek)}` : ""}</p>
          {x.titles.length > 1 && <details><summary>Visa butikernas namnvarianter</summary>{x.titles.map(v=><small key={v}>{v}</small>)}</details>}
        </article>)}
      </div>}
    </section>

    <section className="candidateSection">
      <div className="sectionHead"><div><span className="kicker">UPPTÄCKTSKÖ</span><h2>Produkter som behöver identitet</h2></div><p>{items.length} visas</p></div>
      {items.length === 0 ? <div className="candidateEmpty">
        <b>Ingen sealed-kandidat ännu.</b>
        <p>När en godkänd feed eller CSV-import hittar en ny produkt visas den här automatiskt.</p>
      </div> :
      <div className="candidateGrid">
        {items.map(x=><article className="candidateCard" key={x.id}>
          <div className="candidateMeta"><span>{x.store_name}</span><span>{x.review_status}</span></div>
          <h3>{x.source_title}</h3>
          <strong>{money(x.price_sek)}</strong>
          <div className="candidateTags">
            {x.category_hint && <span>{x.category_hint}</span>}
            {x.detected_format && <span>{x.detected_format}</span>}
            {x.year_season_hint && <span>{x.year_season_hint}</span>}
            {x.language_hint && <span>{x.language_hint}</span>}
          </div>
          <dl>
            <div><dt>Lager</dt><dd>{x.stock_status}</dd></div>
            <div><dt>Randomiserad</dt><dd>{x.randomized ? "Ja" : "Nej / okänt"}</dd></div>
          </dl>
          {x.url ? <a href={x.url} target="_blank" rel="noreferrer">ÖPPNA KÄLLPRODUKT ↗</a> : <small>Ingen käll-URL</small>}
        </article>)}
      </div>}
    </section>
  </main>
}
