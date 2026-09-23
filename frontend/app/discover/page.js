import FreshDataButton from "../components/FreshDataButton";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getJson(path,fallback){
  try{
    const res=await fetch(`${API}${path}`,{cache:"no-store"});
    if(!res.ok)return fallback;
    return res.json();
  }catch{return fallback;}
}

const goals=[
  ["balanced","Balanserat"],["autographs","Autografer"],["rookies","Rookies"],
  ["jackpot","Monsterhit"],["hits","Många hits"],["fun","Kul att öppna"]
];

function metric(v){return v==null?"—":`${v}/10`}
function money(v){return v==null?"—":`${Math.round(v).toLocaleString("sv-SE")} kr`}

export default async function DiscoverPage({searchParams}){
  const category=searchParams?.category||"";
  const budget=searchParams?.budget||"750";
  const goal=searchParams?.goal||"balanced";
  const format=searchParams?.format||"";
  const qs=new URLSearchParams();
  if(category)qs.set("category",category);
  if(budget)qs.set("budget",budget);
  if(format)qs.set("format",format);
  qs.set("goal",goal);
  const [data, realCatalog]=await Promise.all([
    getJson(`/discovery/recommendations?${qs.toString()}`,{recommendations:[],considered:0,rankable:0,note:""}),
    getJson(`/discovery/real-catalog?${qs.toString()}&limit=60`,{products:[],count:0,note:""}),
  ]);
  const recs=data.recommendations||[];
  const realProducts=realCatalog.products||[];

  return <main className="discoverPage">
    <header className="productNav">
      <a className="brand" href="/"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></a>
      <a className="backLink" href="/">← STARTSIDAN</a>
      <span className="version">v0.41.0</span>
    </header>

    <section className="discoverHero">
      <span className="kicker">COLLECTOR DISCOVERY</span>
      <h1>Jag vill öppna något.</h1>
      <p>Välj vad du samlar, din budget och vad du hoppas få. BoxFinder väljer tre olika vägar istället för att låtsas att en box passar alla.</p>

      <div className="discoverQuick"><small>SNABBSÖKNINGAR</small><div>
        <a href="?category=Hockey&budget=2500&goal=rookies">ROOKIES</a>
        <a href="?budget=5000&goal=autographs">AUTOGRAFER</a>
        <a href="?category=Pok%C3%A9mon&budget=2500&goal=jackpot">POKÉMON</a>
        <a href="?category=Hockey&budget=250&goal=hits&format=single%20pack">LÖSA PAKET</a>
        <a href="?budget=500&goal=balanced">UNDER 500 KR</a>
        <a href="?budget=5000&goal=jackpot">MONSTERHIT</a>
      </div></div>

      <form className="discoverForm" method="get">
        <div><label>VAD SAMLAR DU?</label><select name="category" defaultValue={category}>
          <option value="">Allt</option><option>Hockey</option><option>Fotboll</option><option>Basket</option><option>NFL</option><option>Baseboll</option><option>F1</option><option>Pokémon</option><option>One Piece</option><option>Magic</option><option>Lorcana</option>
        </select></div>
        <div><label>MAXBUDGET</label><select name="budget" defaultValue={String(budget)}>
          <option value="100">100 kr</option><option value="250">250 kr</option><option value="500">500 kr</option><option value="750">750 kr</option><option value="1000">1 000 kr</option><option value="1500">1 500 kr</option><option value="2500">2 500 kr</option><option value="5000">5 000 kr</option>
        </select></div>
        <div><label>FORMAT</label><select name="format" defaultValue={format}>
          <option value="">Alla format</option><option value="single pack">Lösa paket</option><option value="hobby box">Hobbybox</option><option value="blaster">Blaster</option><option value="booster box">Boosterbox</option><option value="collection box">Collection box</option>
        </select></div>
        <div className="goalField"><label>VAD JAGAR DU?</label><div className="goalChoices">{goals.map(([value,label])=><label key={value}><input type="radio" name="goal" value={value} defaultChecked={goal===value}/><span>{label}</span></label>)}</div></div>
        <button>VISA VAD JAG SKA KÖPA →</button>
      </form>
    </section>

    <FreshDataButton />

    <section className="realCatalogSection">
      <div className="sectionHead"><div><span className="kicker">RIKTIG SVENSK BUTIKSDATA</span><h2>Vilken box har bäst innehåll?</h2></div><p>{realCatalog.count||0} verifierade produkter matchar filtret · chase-data rankas först.</p></div>
      {realProducts.length ? <div className="realCatalogGrid">{realProducts.map(x=><article className="realProductCard clickableCard" key={x.id}>
        <a className="cardClickTarget" href={`/product/${x.id}`} aria-label={`Öppna ${x.name}`}></a>
        <div className="realProductTop"><span>VERIFIERAD SNAPSHOT</span><small>{x.store}</small></div>
        <h3>{x.name}</h3>
        <div className="realPrice">{money(x.price)}</div>{x.content_rating?.score!=null&&<div className="contentScore"><small>CHASE-INNEHÅLL</small><b>{x.content_rating.score}/100</b><span>{x.content_rating.label} · {x.content_rating.style}</span></div>}{x.pull_profile?.repeatable!=null&&<div className="pullMini"><span>Bra saker ofta <b>{x.pull_profile.repeatable}</b></span><span>Tak <b>{x.pull_profile.ceiling}</b></span></div>}
        <div className="realMeta">
          <span>{x.format}</span>
          {x.packs!=null&&<span>{x.packs} pack</span>}
          {x.cards_per_pack!=null&&<span>{x.cards_per_pack} kort/pack</span>}
          {x.total_cards!=null&&<span>{x.total_cards} kort totalt</span>}
        </div>
        {x.facts?.length ? <div className="realFacts"><small>VERIFIERAT INNEHÅLL</small>{x.facts.slice(0,4).map((f,i)=><span key={i}>✓ {f}</span>)}</div> : <div className="realFacts pending"><small>ANALYSUNDERLAG</small><span>Pris, lager och format verifierat. Hit-/EV-analys är ännu inte klar.</span></div>}
        {x.chase_ladder?.length>0&&<div className="quickExactChase"><small>EXAKTA CHASE-KORT</small>{x.chase_ladder.slice(-3).reverse().map((r,i)=><span key={i}><b>{r.tier}</b> {r.card}</span>)}</div>}
        {x.chase_profile&&<div className="quickChase"><small>BRA KORT DU KAN DRA</small>{x.chase_profile.tiers?.good?.items?.slice(0,3).map((r,i)=><span key={i}>★ {r}</span>)}{x.chase_profile.tiers?.jackpot?.items?.[0]&&<b>JACKPOT: {x.chase_profile.tiers.jackpot.items[0]}</b>}</div>}
        {x.chase_profile?.key_names?.length ? <div className="quickSearches"><small>SÖK ETT NAMN DIREKT</small><div>{x.chase_profile.key_names.slice(0,4).map((name,i)=><a className="aboveOverlay" href={`/chase?q=${encodeURIComponent(name.replace(/\s+#.*$/,''))}`} key={i}>Sök {name} →</a>)}</div></div> : null}
        <div className="realWhy"><small>VARFÖR BRA / FYND?</small>{(x.explanation?.why_good||[]).slice(0,2).map((r,i)=><span key={i}>✓ {r}</span>)}<b>{x.explanation?.deal?.label||"Fyndstatus ej verifierad"}</b><p>{x.explanation?.deal?.reason}</p></div>
        <div className="realSource"><span>Kontrollerad {x.observed_at?new Date(x.observed_at).toLocaleDateString("sv-SE"):"—"}</span>{x.url?<a className="aboveOverlay" href={x.url} target="_blank" rel="noreferrer">ÖPPNA BUTIK →</a>:null}</div>
      </article>)}</div> : <div className="discoveryEmpty"><b>Ingen verifierad produkt matchar just detta filter.</b><p>Höj budgeten eller välj “Allt”. Riktig butikssnapshot visas här separat från testdata och analysförslag.</p></div>}
      <p className="discoveryDisclaimer">{realCatalog.note}</p>
    </section>

    <section className="discoverResults">
      <div className="sectionHead"><div><span className="kicker">3 VÄGAR</span><h2>BoxFinders val</h2></div><p>{data.rankable||0} av {data.considered||0} produkter hade tillräckligt med data för den här sökningen.</p></div>
      {recs.length ? <div className="discoveryGrid">{recs.map((r,i)=><article className={`discoveryCard discovery-${i} clickableCard`} key={r.id}>
        <a className="cardClickTarget" href={`/product/${r.id}`} aria-label={`Öppna ${r.name}`}></a>
        <div className="discoveryBadgeRow"><div className="discoveryRole">{r.recommendation_role}</div>{r.source_kind==="demo"&&<span className="testDataBadge">TESTDATA · EJ BUTIKSPRIS</span>}</div>
        <div className="discoveryTop"><div><small>{r.category} · {r.format}</small><h2>{r.name}</h2><p>{r.store} · <b>{money(r.price)}</b></p></div><div className="discoveryScore"><small>MATCH</small><strong>{r.discovery_score??"—"}</strong><span>/100</span></div></div>

        <div className="splitScores"><div><small>BOXEN</small><b>{r.box_score??"—"}/100</b><span>Hur bra innehållet ser ut</span></div><div><small>PRISET NU</small><b>{r.price_score??"—"}{r.price_score!=null?"/100":""}</b><span>{r.price_score==null?"För lite jämförelsedata":"Mot aktuell butiksnivå"}</span></div></div>

        <div className="openingProfile"><small>ÖPPNINGSPROFIL</small><div>
          <span>Jackpot <b>{metric(r.opening_profile?.jackpot)}</b></span>
          <span>Hits <b>{metric(r.opening_profile?.hit_frequency)}</b></span>
          <span>Rookies <b>{metric(r.opening_profile?.rookies)}</b></span>
          <span>Variation <b>{metric(r.opening_profile?.variety)}</b></span>
          <span>Autograf <b>{metric(r.opening_profile?.autographs)}</b></span>
          <span>Risk <b>{metric(r.opening_profile?.risk)}</b></span>
        </div></div>

        <div className="whyExciting"><small>VARFÖR DEN ÄR INTRESSANT</small>{r.why_exciting?.length?r.why_exciting.map((x,j)=><span key={j}>✓ {x}</span>):<span>Analysdata finns, men ännu inga starka särskiljande signaler.</span>}</div>

        <div className="discoveryChases"><small>CHASE-KORT</small>{r.chase_cards?.length?r.chase_cards.slice(0,3).map((c,j)=><div key={j}><b>{c.name}</b><span>{c.parallel||c.outcome||"Verifierad checklistträff"}{c.market_value_raw!=null?` · ca ${money(c.market_value_raw)}`:""}</span></div>):<p>Verifierad chase-data saknas ännu.</p>}</div>

        <div className="discoveryFoot"><span>Datasäkerhet {r.discovery_confidence}/100</span><a href={`/product/${r.id}`}>SE BOXEN →</a></div>
      </article>)}</div>:<div className="discoveryEmpty"><b>Inte tillräckligt med verifierad data ännu.</b><p>BoxFinder fick inget användbart svar från backend. Kontrollera DATASTATUS ovan. Om frontend och backend har olika version behöver backend startas om.</p></div>}
      <p className="discoveryDisclaimer">{data.note}</p>
    </section>
  </main>
}
