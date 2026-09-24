import ScopeWatchForm from "../components/ScopeWatchForm";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getJson(path, fallback) {
  try {
    const res = await fetch(`${API}${path}`, { cache: "no-store" });
    if (!res.ok) return fallback;
    return res.json();
  } catch {
    return fallback;
  }
}

function triggerText(rule) {
  if (rule.trigger_type === "price_below") return `Under ${Math.round(rule.threshold_sek)} kr`;
  if (rule.trigger_type === "back_in_stock") return "Åter i lager";
  if (rule.trigger_type === "new_90d_low") return "Nytt 90-dagarslägsta";
  if (rule.trigger_type === "price_drop") return "Nästa prisfall";
  return rule.trigger_type;
}

export default async function WatchlistPage() {
  const [rules, events, scopeRules, scopeEvents] = await Promise.all([
    getJson("/watchlist/rules", []),
    getJson("/watchlist/events?limit=100", []),
    getJson("/watchlist/scope-rules", []),
    getJson("/watchlist/scope-events?limit=100", []),
  ]);
  const unread = events.filter(e => !e.read);

  return <main className="watchlistPage">
    <header className="productNav">
      <a className="brand" href="/"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></a>
      <a className="backLink" href="/">← TILL STARTSIDAN</a>
      <span className="version">v0.46.1</span>
    </header>

    <section className="watchlistHero">
      <span className="kicker">MINA BEVAKNINGAR</span>
      <h1>Boxarna BoxFinder håller ögonen på.</h1>
      <p>Prisgränser, åter i lager, nya 90-dagarslägsta och prisfall samlas på ett ställe.</p>
      <div className="watchlistStats">
        <div><small>AKTIVA</small><b>{rules.filter(r=>r.active).length}</b></div>
        <div><small>NYA HÄNDELSER</small><b>{unread.length}</b></div>
        <div><small>TOTALT HÄNDELSER</small><b>{events.length}</b></div>
      </div>
    </section>

    <section className="watchlistSection">
      <div className="sectionHead"><div><span className="kicker">BRED BEVAKNING</span><h2>Hitta något spännande – inte bara en viss box.</h2></div><p>Exempel: alla hockeyboxar under 500 kr eller alla Pokémon ETB under 600 kr.</p></div>
      <ScopeWatchForm />
      {scopeRules.length ? <div className="scopeRuleList">{scopeRules.map(rule=><article key={rule.id}>
        <small>{rule.active ? "AKTIV" : "PAUSAD"}</small>
        <b>{[rule.category,rule.format,rule.max_price_sek?`under ${Math.round(rule.max_price_sek)} kr`:null].filter(Boolean).join(" · ") || "Bred bevakning"}</b>
        <span>{rule.trigger_type==="matching_offer"?"Alla matchande signaler":rule.trigger_type==="price_drop"?"Prisfall":rule.trigger_type==="new_90d_low"?"Nytt 90D-lägsta":"Åter i lager"}</span>
      </article>)}</div> : null}
      {scopeEvents.length ? <div className="scopeEventMini"><small>SENASTE MATCHNINGAR</small>{scopeEvents.slice(0,5).map(e=><a href={`/product/${e.variant_id}`} key={e.id}>{e.message}</a>)}</div> : null}
    </section>

    <section className="watchlistSection">
      <div className="sectionHead"><div><span className="kicker">REGLER</span><h2>Det här bevakar du</h2></div><p>Skapa nya bevakningar direkt från en produktsida.</p></div>
      {rules.length ? <div className="watchRuleGrid">{rules.map(rule=><article key={rule.id} className={!rule.active ? "watchRule inactive" : "watchRule"}>
        <small>{rule.active ? "AKTIV" : "PAUSAD"}</small>
        <h3>{rule.product_name || `Produkt ${rule.variant_id}`}</h3>
        <b>{triggerText(rule)}</b>
        <span>{rule.last_triggered_at ? `Senast triggad ${new Date(rule.last_triggered_at).toLocaleDateString("sv-SE")}` : "Inte triggad ännu"}</span>
        <a href={`/product/${rule.variant_id}`}>ÖPPNA PRODUKT →</a>
      </article>)}</div> : <div className="signalEmpty"><b>Du bevakar ingen box ännu.</b><span>Öppna en produkt och välj exempelvis “under 799 kr” eller “åter i lager”.</span></div>}
    </section>

    <section className="watchlistSection">
      <div className="sectionHead"><div><span className="kicker">HÄNDELSER</span><h2>Det BoxFinder har fångat</h2></div><p>Nyaste händelsen först.</p></div>
      {events.length ? <div className="watchEventFeed">{events.map(event=><a href={`/product/${event.variant_id}`} key={event.id} className={!event.read ? "watchEvent unread" : "watchEvent"}>
        <span>{event.read ? "LÄST" : "NY"}</span>
        <div><small>{event.product_name || "Produkt"}</small><h3>{event.message}</h3><p>{new Date(event.created_at).toLocaleString("sv-SE")}</p></div>
        <strong>{event.price_sek != null ? `${Math.round(event.price_sek)} kr` : "ÖPPNA →"}</strong>
      </a>)}</div> : <div className="signalEmpty"><b>Ingen bevakning har triggats ännu.</b><span>När ett villkor uppfylls visas händelsen här.</span></div>}
    </section>
  </main>;
}
