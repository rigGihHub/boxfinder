const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
async function getData(){try{const r=await fetch(`${API}/admin/stores/activation-queue`,{cache:"no-store"});return r.ok?await r.json():{top_10:[]}}catch{return {top_10:[]}}}
export default async function ActivationPage(){
 const d=await getData();
 return <main className="intakePage">
  <header className="nav sourceNav"><a className="brand" href="/"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></a><nav><a href="/admin/source-hub">Datakällor</a><a href="/admin/intake">Koppla butik</a><a href="/admin/intake/batch">Batch</a><a href="/admin/activation">Aktiveringskö</a></nav><span className="version">v0.39.1</span></header>
  <section className="intakeHero"><span className="kicker">STORE ACTIVATION QUEUE</span><h1>Vilka butiker<br/><em>ska vi få live först?</em></h1><p>Prioriteringen väger sortimentsnytta mot faktisk teknisk readiness. En viktig butik hamnar högt, men kan fortfarande vara blockerad tills feed/API och policy är verifierade.</p></section>
  <section className="batchSummary"><article><small>KÄLLOR</small><b>{d.count||0}</b></article><article><small>REDO</small><b>{d.ready||0}</b></article><article><small>POLICYBLOCKERADE</small><b>{d.blocked||0}</b></article><article><small>SETUP KVAR</small><b>{d.setup||0}</b></article></section>
  <section className="activationQueue">
   <div className="sectionHead"><div><span className="kicker">TOPP 10</span><h2>Aktiveringsordning</h2></div><p>{d.principle}</p></div>
   {(d.top_10||[]).map((x,i)=><article key={x.store_id}>
    <div className="activationRank">#{i+1}</div><div className="activationStore"><small>P{x.priority} · {(x.coverage||[]).join(" · ")||"Täckning ej kartlagd"}</small><h3>{x.store}</h3><p>{x.next_action}</p></div>
    <div className="activationScores"><span>STRATEGI <b>{x.strategic_score}</b></span><span>READINESS <b>{x.readiness_score}</b></span><span>TOTAL <strong>{x.activation_score}</strong></span></div>
    <div className={`activationState ${x.status}`}>{x.status==="ready"?"REDO ATT KÖRA":x.status==="blocked"?"BLOCKERAD":"SETUP KVAR"}<small>{(x.blockers||[]).join(" · ")||"Inga blockerare"}</small></div>
   </article>)}
  </section>
 </main>
}