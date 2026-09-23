import UpdatePanel from "./UpdatePanel";
const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getJson(path, fallback=[]) {
  try {
    const res = await fetch(`${API}${path}`, { cache: 'no-store' });
    return res.ok ? res.json() : fallback;
  } catch { return fallback; }
}

function statusLabel(s) {
  if (s === 'allowed') return ['AUTOMATIK TILLÅTEN','ok'];
  if (s === 'manual_only') return ['ENDAST MANUELL','warn'];
  return ['VÄNTAR PÅ GRANSKNING','blocked'];
}

export default async function SourceHub() {
  const [sources, quality, catalog, coverage] = await Promise.all([
    getJson('/admin/source-hub', []),
    getJson('/admin/data-quality', {}),
    getJson('/admin/catalog-candidates/stats', {}),
    getJson('/admin/catalog-coverage', {summary:{},stores:[],categories:[],next_actions:[]}),
  ]);
  const p1 = sources.filter(s=>s.priority===1).length;
  const allowed = sources.filter(s=>s.automation_status==='allowed').length;
  const successes = sources.filter(s=>s.last_success_at).length;

  return <main className="sourcePage">
    <header className="nav sourceNav">
      <a className="brand" href="/"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></a>
      <nav><a href="/">Startsida</a><a href="/admin/source-hub">Datakällor</a><a href="/admin/catalog">Produktkö</a><a href="/admin/intake">Koppla butik</a><a href="/admin/intake/batch">Batch</a><a href="/admin/activation">Aktiveringskö</a></nav>
      <span className="version">v0.45.0</span>
    </header>

    <section className="sourceHero">
      <div>
        <span className="kicker">SOURCE HUB · DATA CENTRAL</span>
        <h1>Butikerna bakom<br/><em>BoxFinder.</em></h1>
        <p>Här ser du vilka svenska butiker vi vill använda, vad de täcker och om automatisk insamling är tillåten. En publik webbsida betyder inte automatiskt att vi får crawla den.</p>
      </div>
      <div className="sourceStats">
        <article><small>KÄLLOR</small><b>{sources.length}</b></article>
        <article><small>PRIORITET 1</small><b>{p1}</b></article>
        <article><small>AUTOMATIK TILLÅTEN</small><b>{allowed}</b></article>
        <article><small>LYCKADE KÖRNINGAR</small><b>{successes}</b></article>
      </div>
    </section>

    <UpdatePanel api={API} />

    <section className="catalogPulse">
      <div><span className="kicker">SEALED CATALOG ENGINE</span><h2>Nya produkter upptäcks före de rankas.</h2><p>Om en butik innehåller en produkt vi ännu inte känner igen läggs den i granskningskön. Format, kategori, språk och säsong klassas automatiskt. Tillbehör filtreras bort och case blandas aldrig ihop med box.</p></div>
      <div className="catalogPulseGrid">
        <article><small>SEALED-KANDIDATER</small><b>{catalog.sealed_candidates ?? 0}</b></article>
        <article><small>RANDOMISERADE</small><b>{catalog.randomized ?? 0}</b></article>
        <article><small>NYA FÖR GRANSKNING</small><b>{catalog.new_for_review ?? 0}</b></article>
        <article><small>TILLBEHÖR BORTFILTRERADE</small><b>{catalog.accessories_excluded ?? 0}</b></article>
      </div>
    </section>

    <section className="coverageTower">
      <div className="sectionHead"><div><span className="kicker">CATALOG COVERAGE CONTROL TOWER</span><h2>Var saknas riktig data?</h2></div><p>Färskt betyder högst {coverage.freshness_days ?? 14} dagar gammalt, i lager och säkert matchat.</p></div>
      <div className="coverageSummary">
        <article><small>P1-BUTIKER REDO</small><b>{coverage.summary?.priority_1_ready ?? 0}/{coverage.summary?.priority_1_stores ?? 0}</b></article>
        <article><small>FÄRSKA LIVE-ERBJUDANDEN</small><b>{coverage.summary?.fresh_in_stock_offers ?? 0}</b></article>
        <article><small>SÄKERT MATCHADE</small><b>{coverage.summary?.trusted_offers ?? 0}</b></article>
        <article><small>SVAGA KATEGORIER</small><b>{coverage.summary?.weak_categories ?? 0}</b></article>
      </div>

      <div className="coverageGrid">
        <div className="coveragePanel">
          <div className="miniHead"><div><span className="kicker">NÄSTA DATAÅTGÄRDER</span><h3>Vad bör göras först?</h3></div></div>
          {(coverage.next_actions||[]).length ? <div className="coverageActions">{coverage.next_actions.map((x,i)=><div key={`${x.store_id}-${i}`}>
            <span className="priority">P{x.priority}</span>
            <div><b>{x.store}</b><small>{x.action}</small></div>
            <strong>{x.readiness_score}/100</strong>
          </div>)}</div> : <div className="candidateEmpty"><b>Inga blockerande dataåtgärder.</b></div>}
        </div>

        <div className="coveragePanel">
          <div className="miniHead"><div><span className="kicker">KATEGORIER</span><h3>Källtäckning</h3></div></div>
          <div className="categoryCoverage">{(coverage.categories||[]).slice(0,12).map(x=><div key={x.category}>
            <span>{x.category}</span>
            <div className="coverageBar"><i style={{width:`${Math.min(100,x.source_coverage_pct||0)}%`}}/></div>
            <b>{x.source_coverage_pct}%</b>
            <small>{x.active_source_count}/{x.expected_source_count} källor · {x.fresh_variant_count} produkter</small>
          </div>)}</div>
        </div>
      </div>
    </section>

    <section className="sourceFlow">
      <div><span>01</span><b>Butik / feed</b><small>Pris + lager</small></div><i>→</i>
      <div><span>02</span><b>Matchning</b><small>Rätt produktvariant</small></div><i>→</i>
      <div><span>03</span><b>Historik</b><small>Pris över tid</small></div><i>→</i>
      <div><span>04</span><b>Readiness</b><small>Får den rankas?</small></div>
    </section>

    <section className="sourceSection">
      <div className="sectionHead"><div><span className="kicker">SVENSKA MVP-KÄLLOR</span><h2>Prioriterade butiker</h2></div><p>CSV/feed prioriteras före crawling.</p></div>
      <div className="sourceGrid">
        {sources.map(s=>{
          const [label, cls]=statusLabel(s.automation_status);
          return <article className={`sourceCard priority-${s.priority}`} key={s.id}>
            <div className="sourceTop"><span className="priority">P{s.priority}</span><span className={`sourceStatus ${cls}`}>{label}</span></div>
            <h3>{s.name}</h3>
            <p>{s.strength}</p>
            <div className="coverageTags">{(s.coverage||[]).map(x=><span key={x}>{x}</span>)}</div>
            <dl>
              <div><dt>Insamling nu</dt><dd>{s.collection_method}</dd></div>
              <div><dt>Policy</dt><dd>{s.policy_status}</dd></div>
              <div><dt>Rekommendation</dt><dd>{s.recommended_ingest}</dd></div>
              <div><dt>Senast lyckad</dt><dd>{s.last_success_at ? new Date(s.last_success_at).toLocaleString('sv-SE') : 'Inte körd'}</dd></div>
            </dl>
            {s.last_error && <div className="sourceError">{s.last_error}</div>}
            {s.homepage_url ? <a href={s.homepage_url} target="_blank" rel="noreferrer">ÖPPNA BUTIK ↗</a> : <span className="sourcePending">WEBBADRESS EJ VERIFIERAD</span>}
          </article>
        })}
      </div>
    </section>

    <section className="dataStatus">
      <div><span className="kicker">DATABAS JUST NU</span><h2>Vad finns faktiskt inne?</h2></div>
      <div className="dataStatusGrid">
        <article><small>PRODUKTER</small><b>{quality.products ?? 0}</b></article>
        <article><small>LIVE-ERBJUDANDEN</small><b>{quality.verified_live_offers ?? 0}</b></article>
        <article><small>CHECKLISTOR</small><b>{quality.verified_checklists ?? 0}</b></article>
        <article><small>RAW MARKNADSVÄRDEN</small><b>{quality.raw_market_values ?? 0}</b></article>
      </div>
      <p className="sourceNote">Nästa datasteg är att börja mata in verifierade erbjudanden. Source Hub visar därför hellre “inte körd” än att ge sken av att butikskällorna redan är live.</p>
    </section>
  </main>
}
