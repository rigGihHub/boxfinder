import FreshDataButton from "./components/FreshDataButton";
import {API, getJson} from "./lib/api";

function DataBadge({ kind }) {
  const demo = kind === 'demo';
  return <span className={demo ? 'dataBadge demo' : 'dataBadge live'}>{demo ? 'DEMO' : 'VERIFIERAD DATA'}</span>
}

function ProductCard({ p, i, label }) {
  const names = p.chase_profile?.key_names || [];
  const exact = p.chase_ladder || [];
  return (
    <article className={`card rarity-${(i%3)+1} clickableCard`}>
      <a className="cardClickTarget" href={`/product/${p.id}`} aria-label={`Öppna ${p.name}`}></a>
      <div className="foil"/>
      <div className="cardTop"><span className="rank">#{String(i+1).padStart(2,'0')}</span><DataBadge kind={p.source_kind}/><div className="score"><small>{label || 'VALUE'}</small><strong>{p.ranking_score ?? p.box_value_score ?? '—'}</strong><span>/100</span></div></div>
      <div className="productArt"><div className="miniPack"><small>{p.manufacturer}</small><b>{p.category}</b><span>{p.format}</span></div><div className="rarityTag">{i===0?'★ TOP PICK':i===1?'◆ STRONG':'● WATCH'}</div></div>
      <div className="cardBody">
        <span className="category">{p.category} / {p.format}</span><h3>{p.name}</h3>
        <div className="priceRow"><div><small>BÄSTA PRIS</small><strong>{Math.round(p.price)} kr</strong><span>{p.store}{p.offer_count > 1 ? ` · ${p.offer_count} priser` : ''}</span></div>{p.discount_pct != null && <b className="discount">−{p.discount_pct}%</b>}</div>
        <div className="metrics"><div><span>EV</span><b>{p.ev_low != null ? `${Math.round(p.ev_low)}–${Math.round(p.ev_high)} kr` : 'Saknas'}</b></div><div><span>Risk</span><b>{p.risk}</b></div><div><span>Data</span><b>{p.data_quality}/100</b></div></div>
        <div className="goodHits"><small>DET BRA DU KAN FÅ</small>{p.good_hits?.length ? <div>{p.good_hits.slice(0,3).map((h,j)=><span key={`${p.id}-hit-${j}`}>★ {h.name}{h.parallel ? ` · ${h.parallel}` : ''}{h.market_value_raw != null ? ` · ca ${Math.round(h.market_value_raw)} kr` : ''}</span>)}</div> : <p>Ingen verifierad chase-data ännu.</p>}</div>
        {names.length ? <div className="namedChases"><small>ROOKIES / POKÉMON ATT JAGA</small><div>{names.slice(0,4).map((name,j)=><a href={`/chase?q=${encodeURIComponent(name.replace(/\s+#.*$/,''))}`} key={`${p.id}-name-${j}`}>{name} ↗</a>)}</div></div> : null}
        {exact.length ? <div className="exactChases"><small>ODDS / BRA TRÄFFAR</small>{exact.slice(0,2).map((x,j)=><span key={`${p.id}-exact-${j}`}>★ {x.card} · {x.odds}</span>)}<a href={`/product/${p.id}#chase`}>SE ALLA CHASE-KORT →</a></div> : null}
        <div className="packInfo">{p.packs ?? '—'} packs <i/> {p.cards_per_pack ?? '—'} kort/pack <i/> {p.total_cards ?? '—'} kort</div>
        {p.url&&<a className="cta buyDirect" href={p.url} target="_blank" rel="noreferrer">KÖP HOS {p.store?.toUpperCase()} <span>↗</span></a>}
        <a className="cta" href={`/product/${p.id}`}>SE HELA ANALYSEN <span>→</span></a>
      </div>
    </article>
  )
}

function MiniRanking({ title, subtitle, items, metric='ranking_score' }) {
  return <div className="miniRanking"><div className="miniHead"><div><span className="kicker">{subtitle}</span><h3>{title}</h3></div></div><div className="miniRows">{items.slice(0,5).map((p,i)=><a className="miniRow" href={`/product/${p.id}`} key={`${title}-${p.id}`}><span className="miniRank">{i+1}</span><div><b>{p.name}</b><small>{Math.round(p.price)} kr · {p.category}</small></div><strong>{p[metric] ?? '—'}</strong></a>)}</div></div>
}

const quickSearches = [
  {title:'BÄST ATT ÖPPNA',text:'Alla kategorier i samma ranking',href:'/resale?strategy=balanced',tone:'acid'},
  {title:'HÖGSTA TAK',text:'Jaga den största säljbara träffen',href:'/resale?strategy=jackpot',tone:'violet'},
  {title:'TRÄFF OFTARE',text:'Prioritera återkommande bra hits',href:'/resale?strategy=frequent',tone:'cyan'},
  {title:'UNDER 100 KR',text:'Lösa paket och billiga öppningar',href:'/resale?strategy=balanced&max_price=100',tone:'cyan'},
  {title:'UNDER 500 KR',text:'Säljpotential med låg insats',href:'/resale?strategy=balanced&max_price=500',tone:'gold'},
  {title:'UNDER 1 000 KR',text:'Rankat oavsett kategori',href:'/resale?strategy=balanced&max_price=1000',tone:'acid'},
  {title:'SÖK CHASE',text:'Spelare, rookie eller Pokémon',href:'/chase',tone:'violet'},
];

export default async function Home({ searchParams }) {
  const rawBudget = Number(searchParams?.budget || 1000);
  const budget = [100,250,500,1000,2000].includes(rawBudget) ? rawBudget : 1000;
  const [overview, resaleData, deals, budgetData] = await Promise.all([
    getJson('/rankings/overview', {value:[],upside:[],balanced:[],rookies:[],hit_density:[],under_500:[],under_1000:[],categories:{}}),
    getJson('/rankings/resale?strategy=balanced&limit=6', {items:[],count:0,disclaimer:''}),
    getJson('/deals?days=90&min_discount=8', []),
    getJson(`/budget/recommendations?budget=${budget}&goal=balanced&limit=3`, {recommendations:[]}),
  ]);
  // Keep the API's small database pool from being saturated by one page load.
  const [quality, readiness, signalSummary, recentSignals] = await Promise.all([
    getJson('/admin/data-quality', {}),
    getJson('/admin/ranking-readiness', []),
    getJson('/deals/signals/summary?days=7', {total_signals:0,price_drops:0,new_30d_lows:0,new_90d_lows:0,back_in_stock:0,new_stores:0,biggest_drop:null}),
    getJson('/deals/signals/recent?days=7&limit=12', []),
  ]);
  const products = overview.value || [];
  const resaleProducts = resaleData.items || [];
  const productById = Object.fromEntries(products.map(p => [String(p.id), p]));
  const fallbackDeals = products.slice(0,3);
  return (
    <main>
      <header className="nav">
        <a className="brand" href="#top"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></a>
        <nav><a href="/resale">Bäst att öppna</a><a href="/chase">Chase Finder</a><a href="/discover">Filtrera</a><a href="#ranking">EV-ranking</a><a href="#budget">Budget</a><a href="#signals">Prisradar</a><a href="/watchlist">Bevakningar</a></nav>
        <span className="version">v0.46.1</span>
      </header>

      <section className="hero" id="top">
        <div className="heroCopy"><div className="eyebrow"><i/> BOX INTELLIGENCE · ALLA KATEGORIER</div><h1>ÖPPNA BOXEN<br/><em>MED BÄST CHANS.</em></h1><p>Hockey, fotboll, Pokémon, One Piece, Marvel och fler möts i samma ranking. Målet är enkelt: hitta produkten med bäst dokumenterad möjlighet till en säljbar träff — utan att låtsas att chans är garanti.</p><div className="heroActions"><a className="primary" href="/resale">VISA BÄSTA BOXARNA <b>→</b></a><a className="secondary" href="/chase">SÖK ETT CHASE-KORT</a></div><div className="heroQuick"><small>TRYCK DIREKT PÅ DET DU VILL HITTA</small><div>{quickSearches.map(x=><a className={`quick-${x.tone}`} href={x.href} key={x.title}><b>{x.title}</b><span>{x.text}</span></a>)}</div></div></div>
        <div className="packStage" aria-hidden="true"><div className="glow"/><div className="pack back"><span>BOX</span><b>FINDER</b></div><div className="pack front"><small>VALUE SERIES · 09</small><span>BOX</span><b>FINDER</b><div className="burst">SMART<br/>CHASE</div><footer>PRICE · ODDS · VALUE</footer></div></div>
      </section>

      <nav className="mobileQuickNav" aria-label="Snabbsökningar"><a href="/resale">BÄST ATT ÖPPNA</a><a href="/resale?strategy=jackpot">HÖGSTA TAK</a><a href="/resale?max_price=100">UNDER 100</a><a href="/resale?max_price=500">UNDER 500</a><a href="/chase">SÖK CHASE</a></nav>

      <section className="ticker"><span>BOX VALUE SCORE</span><b>◆</b><span>UPSIDE</span><b>◆</b><span>ROOKIE STRENGTH</span><b>◆</b><span>HIT DENSITY</span><b>◆</b><span>DEAL CONFIDENCE</span></section>

      <section className="intelStrip"><article><span>01</span><small>PRIS</small><b>Är boxen billig just nu?</b><p>Jämför butik, historik och marknadsnivå.</p></article><article><span>02</span><small>INNEHÅLL</small><b>Vad finns faktiskt i boxen?</b><p>Rookies, inserts, autos, parallels och chase cards.</p></article><article><span>03</span><small>ODDS</small><b>Hur sannolikt är det?</b><p>Officiella och härledda odds hålls isär.</p></article><article><span>04</span><small>VÄRDE</small><b>Vad är korten värda?</b><p>Sålda raw-kort väger tyngre än annonser.</p></article></section>

      <FreshDataButton />

      <section className="homeResaleSection">
        <div className="sectionHead"><div><span className="kicker">SPORT- OCH VARUMÄRKESNEUTRAL</span><h2>Bäst möjlighet till säljbar träff</h2></div><p>{resaleData.count || 0} verifierade chase-profiler jämförs</p></div>
        {resaleProducts.length ? <div className="homeResaleGrid">{resaleProducts.map((x,i)=><a href={`/product/${x.id}`} key={x.id}><span>#{i+1}</span><div><small>{x.category} · {x.evidence_grade}</small><h3>{x.name}</h3><p>{x.sellable_chases?.[0]?.card || 'Verifierad chase-profil'}</p></div><aside><b>{x.resale_score}</b><small>SÄLJPOTENTIAL</small><strong>{Math.round(x.price)} kr</strong></aside></a>)}</div> : <div className="chaseEmpty"><b>Ingen tvärkategoriranking ännu.</b><span>Produkter visas först när chase-innehållet är verifierat.</span></div>}
        <a className="homeResaleCta" href="/resale">ÖPPNA HELA RANKINGEN →</a>
      </section>

      <section className="discoveryHomeCta">
        <div><small>FILTRERA OM DU VILL</small><h2>Kategorin är valfri — säljpotentialen styr.</h2><p>Begränsa först när du har en budget eller uttryckligen vill ha en viss sport, TCG eller produktform.</p></div>
        <a href="/resale">RANKA ALLT →</a>
      </section>

      <section className="ranking" id="ranking"><div className="sectionHead"><div><span className="kicker">MEST PRISVÄRD JUST NU</span><h2>Mest box för pengarna</h2></div><p>{products.length} produkter visas · saknad data ger ingen låtsaspoäng</p></div>{products.length ? <div className="grid">{products.slice(0,6).map((p,i)=><ProductCard p={p} i={i} key={p.id}/>)}</div> : <div className="launchState"><div className="launchMain"><span className="launchBadge">DATA MOTOR AKTIV</span><h3>Topplistan väntar på första verifierade boxarna.</h3><p>BoxFinder är igång, men vi visar inte demodata som riktiga fynd. När butikserbjudanden, checklista, odds och kortvärden är tillräckligt bra fylls topplistan automatiskt.</p><div className="launchSteps"><span><b>01</b> Butikspris</span><i>→</i><span><b>02</b> Checklista</span><i>→</i><span><b>03</b> Odds</span><i>→</i><span><b>04</b> Marknadsvärde</span><i>→</i><span><b>05</b> Ranking</span></div></div><div className="launchStats"><div><small>PRODUKTER</small><b>{quality.products ?? 0}</b></div><div><small>VARIANTER</small><b>{quality.variants ?? 0}</b></div><div><small>BUTIKER</small><b>{quality.stores ?? 0}</b></div><div><small>REDO FÖR RANKING</small><b>{readiness.filter?.(x=>x.status==='ready').length ?? 0}</b></div></div></div>}</section>


      <section className="battleSection" id="battle"><div className="sectionHead"><div><span className="kicker">BOX BATTLE</span><h2>Ställ 2–4 boxar mot varandra</h2></div><p>Vinnare per kategori — men bara när datan räcker.</p></div><div className="battleGrid">{products.length ? products.slice(0,4).map((p,i)=><a className="battlePick" href={`/product/${p.id}`} key={`battle-${p.id}`}><span>0{i+1}</span><div><small>{p.category} · {p.format}</small><h3>{p.name}</h3><p>{Math.round(p.price)} kr · Value {p.box_value_score ?? '—'}</p></div></a>) : ['Värde','Monsterhit','Rookies','Risk'].map((x,i)=><article className="battlePick battleGhost" key={x}><span>0{i+1}</span><div><small>BOX BATTLE</small><h3>{x}</h3><p>Vinnare visas när minst två verifierade produkter finns.</p></div></article>)}</div>{products.length >= 2 && <a className="battleCta" href={`${API}/compare?ids=${products.slice(0,4).map(p=>p.id).join(',')}`}>JÄMFÖR TOPPBOXARNA →</a>}<p className="battleNote">Box Battle jämför pris, EV/pris, rookies, hit density, upside, golv, risk, datakvalitet och Box Value. Saknas tillräckligt underlag lämnas kategorin utan vinnare.</p></section>

      <section className="profiles" id="profiles">
        <div className="sectionHead"><div><span className="kicker">OLIKA SÄTT ATT VINNA RANKINGEN</span><h2>Välj vad du faktiskt jagar</h2></div><p>En jackpotbox och en bra allroundbox är inte samma sak.</p></div>
        <div className="profileGrid">
          <MiniRanking title="Monsterhit" subtitle="HÖGST UPSIDE" items={overview.upside || []}/>
          <MiniRanking title="Balanserad" subtitle="VÄRDE + GOLV + HITS" items={overview.balanced || []}/>
          <MiniRanking title="Rookies" subtitle="STARKAST ROOKIEKLASS" items={overview.rookies || []}/>
          <MiniRanking title="Mest action" subtitle="HIT DENSITY" items={overview.hit_density || []}/>
          <MiniRanking title="Under 500 kr" subtitle="LÅG BUDGET" items={overview.under_500 || []}/>
          <MiniRanking title="Under 1 000 kr" subtitle="BUDGET" items={overview.under_1000 || []}/>
        </div>
      </section>


      <section className="budgetSection" id="budget">
        <div className="sectionHead"><div><span className="kicker">BUDGET BUILDER</span><h2>Jag har {budget.toLocaleString('sv-SE')} kr. Vad ska jag köpa?</h2></div><p>Jämför kombinationer — inte bara enskilda boxar.</p></div>
        <div className="budgetChips"><a href="?budget=100#budget">100 kr</a><a href="?budget=250#budget">250 kr</a><a href="?budget=500#budget">500 kr</a><a href="?budget=1000#budget">1 000 kr</a><a href="?budget=2000#budget">2 000 kr</a></div>
        <div className="budgetGrid">
          {(budgetData.recommendations || []).map((r,i)=><article className="budgetCard" key={`budget-${i}`}><div className="budgetScore"><small>BUDGET FIT</small><strong>{r.score}</strong><span>/100</span></div><div className="budgetLines">{r.lines.map(line=><a href={`/product/${line.product_id}`} key={line.product_id}><b>{line.quantity}×</b><span>{line.name}</span><strong>{Math.round(line.unit_price*line.quantity)} kr</strong></a>)}</div><div className="budgetMeta"><span><small>TOTALT</small><b>{Math.round(r.total_price)} kr</b></span><span><small>KVAR</small><b>{Math.round(r.budget_left)} kr</b></span><span><small>DATA</small><b>{r.data_coverage}%</b></span></div>{r.estimated_ev_low != null && <p className="budgetEv">Uppskattat EV: {Math.round(r.estimated_ev_low)}–{Math.round(r.estimated_ev_high)} kr</p>}<ul>{r.reasons.map((x,j)=><li key={j}>{x}</li>)}</ul></article>)}
        </div>
        <p className="budgetDisclaimer">{budgetData.disclaimer}</p>
      </section>

      <section className="signalSection" id="signals">
        <div className="sectionHead"><div><span className="kicker">PRISRADAR · SENASTE 7 DAGARNA</span><h2>Vad har hänt sedan sist?</h2></div><p>BoxFinder reagerar på verkliga pris- och lagerförändringar, inte på gissade fynd.</p></div>
        <div className="signalStats">
          <article><small>PRISFALL</small><b>{signalSummary.price_drops ?? 0}</b></article>
          <article><small>NYA 30D-LÄGSTA</small><b>{signalSummary.new_30d_lows ?? 0}</b></article>
          <article><small>ÅTER I LAGER</small><b>{signalSummary.back_in_stock ?? 0}</b></article>
          <article><small>NYA BUTIKER</small><b>{signalSummary.new_stores ?? 0}</b></article>
        </div>
        {recentSignals.length ? <div className="signalFeed">{recentSignals.slice(0,8).map((s,i)=><a className={`signalEvent signal-${s.signal_type}`} href={s.variant_id ? `/product/${s.variant_id}` : '#signals'} key={s.id}>
          <span className="signalIndex">{String(i+1).padStart(2,'0')}</span>
          <div><small>{s.label} · {s.store_name || 'Butik'}</small><h3>{s.product_name || 'Okänd produkt'}</h3><p>{s.signal_type === 'price_drop' && s.old_price_sek != null ? `${Math.round(s.old_price_sek)} → ${Math.round(s.new_price_sek)} kr` : s.new_price_sek != null ? `${Math.round(s.new_price_sek)} kr` : 'Lagerförändring'}{s.change_pct != null && s.change_pct < 0 ? ` · ${Math.abs(Math.round(s.change_pct))}% ned` : ''}</p></div>
          <strong>{s.signal_type === 'new_90d_low' ? '90D LOW' : s.signal_type === 'new_30d_low' ? '30D LOW' : s.signal_type === 'back_in_stock' ? 'I LAGER' : s.signal_type === 'new_store' ? 'NY BUTIK' : 'PRIS ↓'}</strong>
        </a>)}</div> : <div className="signalEmpty"><b>Inga nya pris- eller lagersignaler ännu.</b><span>När butikskatalogerna börjar uppdateras fylls denna rad automatiskt med prisfall, nya lägstanivåer och åter i lager.</span></div>}
      </section>

      <section className="dealSection" id="deals"><div className="sectionHead"><div><span className="kicker">DEAL SCANNER</span><h2>Dagens boxfynd</h2></div><p>Vi visar de bästa alternativen även när inget når nivån “verifierat fynd”.</p></div>{deals.length ? <div className="dealGrid">{deals.slice(0,6).map((d,i)=>{const p=productById[String(d.variant_id)]||{};return <article className="dealCard clickableCard" key={d.variant_id}><a className="cardClickTarget" href={`/product/${d.variant_id}`} aria-label={`Öppna ${d.name}`}></a><span className="dealNo">0{i+1}</span><div><div className="dealLabel">{d.deal_label || 'Prisfynd'}</div><small>{d.category}</small><h3>{d.name}</h3><p>{d.store} · {Math.round(d.price)} kr</p>{(d.signals || []).length ? <div className="dealSignals">{d.signals.slice(0,3).map((s,j)=><span key={j}>✓ {s}</span>)}</div> : null}{p.good_hits?.length ? <div className="dealHits"><small>DET BRA DU KAN FÅ</small>{p.good_hits.slice(0,2).map((h,j)=><span key={j}>★ {h.name}{h.parallel ? ` · ${h.parallel}` : ''}</span>)}</div>:null}</div><div className="dealStats"><span><small>PRISREFERENS</small><b>{Math.round(d.market_reference)} kr</b></span><span><small>MOT REFERENS</small><b>−{d.discount_pct}%</b></span><span><small>MOT BUTIKER</small><b>{d.cross_store_discount_pct != null ? `−${d.cross_store_discount_pct}%` : '—'}</b></span><span><small>90D LÄGSTA</small><b>{d.history_low != null ? `${Math.round(d.history_low)} kr` : '—'}</b></span><span><small>FYND</small><b>{d.deal_score ?? '—'}</b></span><span><small>SÄKERHET</small><b>{d.deal_confidence}</b></span></div>{d.warning && <em>{d.warning}</em>}</article>})}</div> : fallbackDeals.length ? <><div className="dealNotice"><b>Inget verifierat fynd idag.</b><span>Här är ändå de bästa boxarna i datan just nu. De är inte märkta som fynd.</span></div><div className="dealGrid fallback">{fallbackDeals.map((p,i)=><article className="dealCard clickableCard" key={`fallback-${p.id}`}><a className="cardClickTarget" href={`/product/${p.id}`} aria-label={`Öppna ${p.name}`}></a><span className="dealNo">0{i+1}</span><div><small>{p.category} · BÄST JUST NU</small><h3>{p.name}</h3><p>{p.store} · {Math.round(p.price)} kr</p><div className="dealHits"><small>DET BRA DU KAN FÅ</small>{p.good_hits?.length ? p.good_hits.slice(0,2).map((h,j)=><span key={j}>★ {h.name}{h.parallel ? ` · ${h.parallel}` : ''}</span>) : <span>Chase-data saknas ännu</span>}</div></div><div className="dealStats"><span><small>BOX VALUE</small><b>{p.box_value_score ?? '—'}</b></span><span><small>DATA</small><b>{p.data_quality ?? 0}/100</b></span></div></article>)}</div></> : <div className="emptyDeal"><b>Vi har ännu inga verifierade boxar att jämföra.</b><span>När första riktiga butikserbjudandena är inne visas topp 3 här även om inget är ett starkt fynd.</span></div>}</section>

      <section className="scanner" id="scanner"><div><span className="kicker">PLAYER / CHARACTER SCANNER</span><h2>Jagar du ett särskilt namn?</h2><p>Sök exempelvis Bedard, McDavid, Messi eller Charizard. BoxFinder kan jämföra vilka produkter namnet finns i och, när odds finns, chansen per spenderad krona.</p></div><form action={`${API}/players/search`} method="get"><label>SÖK I CHECKLISTOR</label><div><input name="q" placeholder="Connor Bedard" minLength="2"/><button>SÖK →</button></div><small>Opportunity Score visas bara när användbara odds finns.</small></form></section>

      <section className="principles"><div><b>01</b><span>Profiler före en enda sanning</span><p>Mest prisvärd, jackpot och balanserad får egna rankingar.</p></div><div><b>02</b><span>Fynd måste bevisas</span><p>Deal Scanner kräver historik och väger även datakvalitet och butiksspridning.</p></div><div><b>03</b><span>Ingen affiliatepåverkan</span><p>Kommersiell ersättning ska inte kunna flytta en box i rankingen.</p></div></section>
    </main>
  );
}
