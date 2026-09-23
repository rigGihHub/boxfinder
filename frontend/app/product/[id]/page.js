import WatchControls from "../../components/WatchControls";
const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getProduct(id) {
  const res = await fetch(`${API}/products/${id}`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

function pct(v){ return v == null ? '—' : `${Math.round(v*100)}%`; }
function money(v){ return v == null ? '—' : `${Math.round(v).toLocaleString('sv-SE')} kr`; }
function Outcome({ title, data }){
  return <article className="outcomeCard"><span>{title}</span><b>{data?.count_in_top_list ?? 0} exempel</b><div>{(data?.examples || []).slice(0,3).map(c=><small key={c.card_id}>{c.subject}{c.parallel ? ` · ${c.parallel}` : ''}</small>)}</div></article>
}

export default async function ProductPage({ params }) {
  const p = await getProduct(params.id);
  if (!p) return <main className="productPage"><a className="backLink" href="/">← Till BoxFinder</a><h1>Produkten kunde inte hämtas.</h1></main>;
  const h90 = p.price_history?.windows?.['90d'] || {};
  const a = p.analysis || {};
  const ev = p.ev_coverage || {};
  return <main className="productPage">
    <header className="productNav"><a className="brand" href="/"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></a><a className="backLink" href="/">← TILL TOPPLISTAN</a><span className="version">v0.46.0</span></header>

    <section className="productHero">
      <div className="productHeroCopy"><span className="kicker">{p.category} · {p.manufacturer} · {p.format}</span><h1>{p.name}</h1><p>{p.summary}</p><div className="heroPrice"><span><small>BÄSTA PRIS</small><b>{money(p.price)}</b><em>{p.store}</em></span><span><small>BOX VALUE</small><b>{p.box_value_score ?? '—'}<i>/100</i></b><em>Data {p.data_quality}/100</em></span><span><small>RISK</small><b>{p.risk}</b><em>{p.source_kind === 'demo' ? 'Demo-underlag' : 'Verifierbart underlag'}</em></span></div></div>
      <div className="detailPack"><div className="detailFoil"/><small>{p.manufacturer}</small><strong>{p.category}</strong><b>BOX<br/>FINDER</b><span>{p.format}</span><footer>{p.packs ?? '—'} PACKS · {p.cards_per_pack ?? '—'} / PACK</footer></div>
    </section>

    {p.source_kind === 'demo' && <div className="warningBand"><b>DEMO-DATA</b><span>Den här produkten används för att testa gränssnitt och logik. Köpbeslut ska inte baseras på siffrorna innan datakällorna är verifierade.</span></div>}

    <section className="chaseHeroSection">
      <div className="sectionHead"><div><span className="kicker">CHASE & CONTENT</span><h2>Hur bra kort kan du faktiskt dra?</h2></div><p>{p.content_rating?.score!=null?`Innehåll ${p.content_rating.score}/100 · ${p.content_rating.label} · ${p.content_rating.style}`:"Chase-innehållet är ännu inte verifierat."}</p></div>
      {p.pull_profile?.repeatable!=null&&<div className="pullProfile">
        <div><small>BRA SAKER OFTA</small><strong>{p.pull_profile.repeatable}/100</strong></div>
        <div><small>HUR HÖGT ÄR TAKET?</small><strong>{p.pull_profile.ceiling}/100</strong></div>
        <div><small>VARIANS</small><strong>{p.pull_profile.variance}/100</strong></div>
        <b>{p.pull_profile.label}</b>
      </div>}
      {p.chase_profile ? <>
        <div className="chaseNames"><small>VIKTIGA NAMN ATT JAGA</small>{p.chase_profile.key_names?.map(x=><span key={x}>{x}</span>)}</div>
        {p.chase_ladder?.length>0&&<div className="headlineChases"><div className="headlineChaseHead"><small>EXAKTA KORT ATT JAGA</small><span>{p.chase_ladder.length} verifierade chase-punkter</span></div>{p.chase_ladder.map((x,i)=><article key={`${x.card}-${i}`}><b className={`chaseTag chaseTag${(x.tier||"").replace(" ","")}`}>{x.tier}</b><div><strong>{x.card}</strong><span>{x.why}</span><small>{x.odds}</small></div></article>)}</div>}
        <div className="chaseTierGrid">{["everyday","good","big","jackpot"].map((key,i)=>{const x=p.chase_profile.tiers?.[key];return x?<article className={`chaseTier chaseTier${i}`} key={key}><small>{x.label}</small><strong>{x.score}/100</strong>{x.items?.map((item,j)=><span key={j}>★ {item}</span>)}</article>:null})}</div>
        <div className="chaseReasons">{p.chase_profile.why_exciting?.map((x,i)=><span key={i}>+ {x}</span>)}</div>
        <p className="chaseCaveat">{p.chase_profile.caveat}</p>
        {p.chase_profile.source_url&&<a className="chaseSource" href={p.chase_profile.source_url} target="_blank" rel="noreferrer">ÖPPNA VERIFIERAD CHECKLISTKÄLLA →</a>}
      </> : <div className="chasePending"><b>Inte rankad ännu.</b><span>BoxFinder visar ingen påhittad chase-ranking innan checklista och produktodds har verifierats.</span></div>}
    </section>

    <section className="whyBoxSection">
      <div className="sectionHead"><div><span className="kicker">VARFÖR ÄR DEN INTRESSANT?</span><h2>Bra box eller faktiskt fynd?</h2></div><p>BoxFinder skiljer på produktens innehåll och om dagens pris verkligen är ovanligt bra.</p></div>
      <div className="whyBoxGrid">
        <article><small>VARFÖR DEN KAN VARA BRA</small>{(p.explanation?.why_good||[]).length ? <div>{p.explanation.why_good.map((x,i)=><span key={i}>✓ {x}</span>)}</div> : <p>Vi har ännu inte tillräckligt verifierat innehåll för att säga varför just den här produkten sticker ut.</p>}</article>
        <article className={`dealVerdict ${p.explanation?.deal?.status||'not_verified'}`}><small>FYNDSTATUS</small><b>{p.explanation?.deal?.label||'Ej bedömd'}</b><p>{p.explanation?.deal?.reason||'Prisjämförelse saknas.'}</p>{p.explanation?.price_per_pack_sek!=null&&<span>Pris per pack: {money(p.explanation.price_per_pack_sek)}</span>}</article>
      </div>
    </section>

    <section className="detailGrid">
      <article className="detailPanel"><span className="kicker">PRISANALYS</span><h2>Är priset bra just nu?</h2><div className="statGrid"><div><small>NU</small><b>{money(p.price)}</b></div><div><small>90D MEDIAN</small><b>{money(h90.median)}</b></div><div><small>90D LÄGSTA</small><b>{money(h90.low)}</b></div><div><small>90D HÖGSTA</small><b>{money(h90.high)}</b></div></div><div className="historyStrip">{(p.price_history?.points || []).slice(-18).map((x,i)=><i key={`${x.date}-${i}`} style={{height:`${18 + ((x.price_sek - (h90.low || x.price_sek))/Math.max(1,(h90.high||x.price_sek)-(h90.low||x.price_sek)))*62}px`}} title={`${x.date}: ${x.price_sek} kr`}/>)}</div><small className="panelNote">{h90.observations || 0} prisobservationer senaste 90 dagarna.</small></article>

      <article className="detailPanel"><span className="kicker">EV & DATA</span><h2>Hur mycket vet vi?</h2><div className="evBig">{a.ev_low != null ? `${money(a.ev_low)}–${money(a.ev_high)}` : 'EV saknas'}</div><div className="coverage"><div><span>Marknadsvärden</span><b>{ev.value_pct ?? 0}%</b></div><div><span>Användbara odds</span><b>{ev.odds_pct ?? 0}%</b></div><div><span>I EV-beräkningen</span><b>{ev.ev_pct ?? 0}%</b></div></div>{(ev.notes || []).map((n,i)=><p className="panelNote" key={i}>{n}</p>)}</article>
    </section>

    <section className="outcomeSection"><div className="sectionHead"><div><span className="kicker">VAD KAN JAG FÅ?</span><h2>Från vanligt till jackpot</h2></div><p>Exempel baseras på checklistan. Saknade odds visas inte som gissningar.</p></div><div className="outcomeGrid"><Outcome title="VANLIGT" data={p.outcomes?.common}/><Outcome title="BRA TRÄFF" data={p.outcomes?.good_hit}/><Outcome title="STOR HIT" data={p.outcomes?.big_hit}/><Outcome title="JACKPOT" data={p.outcomes?.jackpot}/></div></section>

    <section className="chaseSection" id="chase"><div className="sectionHead"><div><span className="kicker">CHASE BOARD</span><h2>Viktigaste korten vi har data på</h2></div><p>{p.checklist?.card_count || 0} kort i checklistan · {p.checklist?.verification_status || 'ingen verifiering'}</p></div>
      {p.chase_profile?.key_names?.length ? <div className="searchSuggestions"><small>GÖR EN SÖKNING PÅ NAMNET</small><div>{p.chase_profile.key_names.slice(0,8).map((name,i)=><a href={`/chase?q=${encodeURIComponent(name.replace(/\s+#.*$/,''))}`} key={i}>Sök {name} →</a>)}</div></div> : null}
      {p.chase_ladder?.length ? <div className="headlineChases"><div className="headlineChaseHead"><small>EXAKTA CHASE-KORT · ODDS NÄR DE ÄR VERIFIERADE</small><span>{p.chase_ladder.length} kort/profiler</span></div>{p.chase_ladder.slice(0,10).map((x,i)=><article key={`${x.card}-${i}`}><b className={`chaseTag chaseTag${(x.tier||"").replace(" ","")}`}>{x.tier}</b><div><strong>{x.card}</strong><span>{x.why}</span><small>{x.odds || 'Odds saknas'}</small></div></article>)}</div> : null}
      {(p.chase_cards || []).length ? <div className="chaseTable"><div className="chaseHead"><span>#</span><span>KORT</span><span>RAW-VÄRDE</span><span>CHANS / BOX</span><span>ODDS</span><span>DATA</span></div>{p.chase_cards.map((c,i)=><div className="chaseRow" key={c.card_id}><span>{String(i+1).padStart(2,'0')}</span><div><b>{c.subject}</b><small>{c.card_number || '—'} · {c.subset}{c.parallel ? ` · ${c.parallel}` : ''}{c.serial_numbered_to ? ` /${c.serial_numbered_to}` : ''}</small></div><strong>{money(c.raw_value_sek)}</strong><strong>{pct(c.probability_per_box)}</strong><span className={`oddsBasis ${c.odds_basis}`}>{c.odds_basis}</span><strong>{c.market_data_quality}/100</strong></div>)}</div> : <div className="emptyDeal"><b>Ingen chase-data ännu.</b><span>Checklistan eller marknadsvärdena saknas. BoxFinder fyller inte ut listan med uppskattade kort.</span></div>}
    </section>

    <section className="watchSection">
      <div className="sectionHead"><div><span className="kicker">MIN BEVAKNING</span><h2>Säg till när det blir intressant.</h2></div><p>Bevakningen reagerar på BoxFinders verifierade pris- och lagersignaler.</p></div>
      <WatchControls variantId={p.id} currentPrice={p.price} />
    </section>

    <section className="productSignalSection">
      <div className="sectionHead"><div><span className="kicker">PRISHISTORIK · HÄNDELSER</span><h2>Senaste förändringarna</h2></div><p>{(p.price_signals || []).length} signaler senaste 30 dagarna.</p></div>
      {(p.price_signals || []).length ? <div className="productSignalFeed">{p.price_signals.slice(0,10).map(s=><article key={s.id}>
        <div><small>{s.label} · {s.store_name || 'Butik'}</small><b>{s.signal_type === 'price_drop' && s.old_price_sek != null ? `${money(s.old_price_sek)} → ${money(s.new_price_sek)}` : s.new_price_sek != null ? money(s.new_price_sek) : 'Lagerförändring'}</b></div>
        <span>{s.change_pct != null && s.change_pct < 0 ? `${Math.abs(Math.round(s.change_pct))}% ned` : s.current_stock_status === 'in_stock' ? 'I lager' : 'Ny signal'}</span>
      </article>)}</div> : <div className="candidateEmpty"><b>Ingen prissignal ännu.</b><p>Prisfall, nya lägstanivåer och åter-i-lager-händelser visas här när de upptäcks.</p></div>}
    </section>

    <section className="priceCompareSection">
      <div className="sectionHead"><div><span className="kicker">PRISJÄMFÖRELSE</span><h2>Samma box. Flera svenska butiker.</h2></div><p>{p.price_comparison?.store_count ?? 0} butiker med färsk, matchad lagerdata.</p></div>
      <div className="compareSummary">
        <article><small>BILLIGASTE VARA</small><b>{money(p.price_comparison?.best_item_price?.item_price_sek)}</b><span>{p.price_comparison?.best_item_price?.store || '—'}</span></article>
        <article><small>BILLIGASTE TOTALPRIS</small><b>{money(p.price_comparison?.best_total_price?.total_price_sek)}</b><span>{p.price_comparison?.best_total_price ? `${p.price_comparison.best_total_price.store} · inkl verifierad frakt` : 'Fraktdata saknas'}</span></article>
        <article><small>BUTIKSMEDIAN</small><b>{money(p.price_comparison?.market_median_item_price_sek)}</b><span>Aktuella matchade priser</span></article>
        <article><small>PRISSPANN</small><b>{money(p.price_comparison?.price_spread_sek)}</b><span>Skillnad billigast–dyrast</span></article>
      </div>
      <div className="compareOfferList">{(p.price_comparison?.offers || []).map((o,i)=><article key={`pc-${o.offer_id}`}>
        <span className="compareRank">#{String(i+1).padStart(2,'0')}</span><div><b>{o.store}</b><small>Kontrollerad {o.observed_at ? new Date(o.observed_at).toLocaleDateString('sv-SE') : '—'} · {o.match_status}</small></div>
        <div><small>VARA</small><strong>{money(o.item_price_sek)}</strong></div><div><small>FRAKT</small><strong>{o.shipping_sek == null ? 'Okänd' : money(o.shipping_sek)}</strong></div>
        <div><small>TOTALT</small><strong>{o.total_price_sek == null ? '—' : money(o.total_price_sek)}</strong></div>{o.url ? <a href={o.url} target="_blank" rel="noreferrer">TILL BUTIK →</a> : <span>Ingen länk</span>}
      </article>)}</div><p className="compareNote">{p.price_comparison?.note}</p>
    </section>

    <section className="offersSection"><div className="sectionHead"><div><span className="kicker">RÅDATA FRÅN BUTIKER</span><h2>Alla observerade erbjudanden</h2></div><p>Här visas även erbjudanden som inte ingår i den säkra prisjämförelsen.</p></div><div className="offerList">{(p.offers || []).map((o,i)=><article key={`${o.store}-${i}`}><div><b>{o.store}</b><small>{o.stock_status} · {o.source_kind} · confidence {o.source_confidence}/100</small></div><strong>{money(o.price_sek)}</strong>{o.url ? <a href={o.url} target="_blank" rel="noreferrer">VISA BUTIK →</a> : <span>Ingen länk</span>}</article>)}</div></section>
  </main>
}
