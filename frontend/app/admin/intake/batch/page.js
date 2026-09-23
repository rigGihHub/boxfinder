const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";

async function getJson(path,fallback){
  try{const r=await fetch(`${API}${path}`,{cache:"no-store"});return r.ok?await r.json():fallback}catch{return fallback}
}

export default async function BatchIntakePage(){
  const rows=await getJson("/admin/intake/batch-status",[]);
  const validated=rows.filter(x=>x.status==="validated").length;
  const auto=rows.filter(x=>x.automation_ready).length;
  const missing=rows.filter(x=>x.status==="missing").length;
  return <main className="intakePage">
    <header className="nav sourceNav">
      <a className="brand" href="/"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></a>
      <nav><a href="/admin/source-hub">Datakällor</a><a href="/admin/catalog">Produktkö</a><a href="/admin/intake">Koppla butik</a><a href="/admin/intake/batch">Batch</a><a href="/admin/activation">Aktiveringskö</a></nav>
      <span className="version">v0.45.0</span>
    </header>

    <section className="intakeHero">
      <span className="kicker">FEED ONBOARDING BATCH</span>
      <h1>Flera butiker.<br/><em>En gemensam status.</em></h1>
      <p>Här ser du vilka butikskällor som redan har en validerad feedprofil, vilka som fortfarande saknar mappning och vilka som faktiskt är redo för automatisk insamling.</p>
    </section>

    <section className="batchSummary">
      <article><small>BUTIKER</small><b>{rows.length}</b></article>
      <article><small>VALIDERADE PROFILER</small><b>{validated}</b></article>
      <article><small>AUTOMATIK REDO</small><b>{auto}</b></article>
      <article><small>SAKNAR PROFIL</small><b>{missing}</b></article>
    </section>

    <section className="batchTableWrap">
      <div className="sectionHead"><div><span className="kicker">ONBOARDING STATUS</span><h2>Vilka källor kan börja leverera data?</h2></div><p>Validerad feedprofil räcker inte om policy fortfarande blockerar automatisk körning.</p></div>
      <div className="batchTable">
        <div className="batchRow batchHead"><span>Butik</span><span>Profil</span><span>Policy</span><span>Rader</span><span>Adapter</span><span>Status</span></div>
        {rows.map(x=><div className="batchRow" key={x.store_id}>
          <span><b>{x.store_name}</b></span>
          <span>{x.status}</span>
          <span>{x.policy_status}</span>
          <span>{x.valid_rows||0}/{x.rows_seen||0}</span>
          <span>{x.adapter_key||"—"}</span>
          <span className={x.automation_ready?"batchReady":x.activation_ready?"batchWarn":"batchBlocked"}>{x.automation_ready?"AUTOMATIK REDO":x.activation_ready?"PROFIL REDO, POLICY STOPPAR":"INTE REDO"}</span>
        </div>)}
      </div>
    </section>
  </main>
}
