"use client";

import { useEffect, useMemo, useState } from "react";

const DEFAULT_SAMPLE=`sku,name,price,stock,url
ABC-001,2025-26 Upper Deck Series 1 Hobby Box,899,in_stock,https://butik.se/abc-001
ABC-002,Topps Chrome UEFA 2025 Hobby Box,1299,in_stock,https://butik.se/abc-002`;

export default function IntakeWizard({ api }) {
  const [stores,setStores]=useState([]);
  const [storeId,setStoreId]=useState("");
  const [format,setFormat]=useState("csv");
  const [sample,setSample]=useState(DEFAULT_SAMPLE);
  const [preview,setPreview]=useState(null);
  const [sourceUrl,setSourceUrl]=useState("");
  const [baseUrl,setBaseUrl]=useState("");
  const [status,setStatus]=useState("");
  const [busy,setBusy]=useState(false);

  useEffect(()=>{
    fetch(`${api}/admin/stores`,{cache:"no-store"}).then(r=>r.ok?r.json():[]).then(rows=>{
      const real=rows.filter(x=>x.collection_method!=="demo");
      setStores(real);
      if(real.length) setStoreId(String(real[0].id));
    }).catch(()=>{});
  },[api]);

  const selected=useMemo(()=>stores.find(x=>String(x.id)===String(storeId)),[stores,storeId]);

  async function inspect(){
    if(!storeId)return;
    setBusy(true); setStatus("");
    try{
      const res=await fetch(`${api}/admin/stores/${storeId}/intake/preview`,{
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({feed_format:format,sample_text:sample})
      });
      const data=await res.json();
      if(!res.ok)throw new Error(data.detail||"Kunde inte analysera provet.");
      setPreview(data);
    }catch(e){setStatus(e.message)}finally{setBusy(false)}
  }

  async function save(){
    if(!preview||!storeId)return;
    setBusy(true);setStatus("");
    try{
      const res=await fetch(`${api}/admin/stores/${storeId}/intake/profile`,{
        method:"PUT",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
          feed_format:format,
          field_mapping:preview.effective_mapping,
          source_url:sourceUrl||null,
          base_url:baseUrl||null,
          sample_hash:preview.sample_hash,
          rows_seen:preview.rows_seen,
          valid_rows:preview.valid_rows,
          invalid_rows:preview.invalid_rows,
          ready:preview.ready
        })
      });
      const data=await res.json();
      if(!res.ok)throw new Error(data.detail||"Kunde inte spara.");
      setStatus(data.status==="validated"?"Profil validerad och sparad.":"Profil sparad som utkast.");
    }catch(e){setStatus(e.message)}finally{setBusy(false)}
  }

  async function activate(){
    if(!storeId)return;
    setBusy(true);setStatus("");
    try{
      const res=await fetch(`${api}/admin/stores/${storeId}/intake/activate`,{method:"POST"});
      const data=await res.json();
      if(!res.ok)throw new Error(data.detail||"Kunde inte aktivera.");
      setStatus(`Aktiverad. Policy är fortfarande ${data.policy_status} och ändrades inte.`);
    }catch(e){setStatus(e.message)}finally{setBusy(false)}
  }

  return <div className="intakeWizard">
    <section className="intakeSetup">
      <div><label>BUTIK</label><select value={storeId} onChange={e=>setStoreId(e.target.value)}>{stores.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></div>
      <div><label>FORMAT</label><select value={format} onChange={e=>setFormat(e.target.value)}><option value="csv">CSV</option><option value="json">JSON</option></select></div>
      <div><label>FEED-URL</label><input value={sourceUrl} onChange={e=>setSourceUrl(e.target.value)} placeholder="Verifierad feed/API-URL"/></div>
      <div><label>BAS-URL</label><input value={baseUrl} onChange={e=>setBaseUrl(e.target.value)} placeholder="Valfritt, för relativa länkar"/></div>
    </section>

    <section className="intakeSample">
      <div className="sectionHead"><div><span className="kicker">STEG 1 · KLISTRA IN PROV</span><h2>Låt BoxFinder förstå butikens feed.</h2></div><p>5–20 rader räcker normalt för att identifiera kolumnerna.</p></div>
      <textarea value={sample} onChange={e=>setSample(e.target.value)} spellCheck="false"/>
      <button disabled={busy||!storeId} onClick={inspect}>ANALYSERA PROV →</button>
    </section>

    {preview&&<section className="intakePreview">
      <div className="sectionHead"><div><span className="kicker">STEG 2 · VALIDERING</span><h2>{preview.ready?"Redo att spara":"Behöver justeras"}</h2></div><p>{preview.valid_rows}/{preview.rows_seen} rader kunde läsas.</p></div>
      <div className="intakeStats">
        <article><small>GILTIGA</small><b>{preview.valid_rows}</b></article>
        <article><small>FEL</small><b>{preview.invalid_rows}</b></article>
        <article><small>SEALED</small><b>{preview.sealed_candidates}</b></article>
        <article><small>RANDOMISERADE</small><b>{preview.randomized_candidates}</b></article>
      </div>
      <div className="mappingPanel">
        <h3>Identifierad kolumnmappning</h3>
        {Object.entries(preview.effective_mapping||{}).map(([k,v])=><div key={k}><span>{k}</span><b>← {v}</b></div>)}
        {(preview.required_mapping_missing||[]).length>0&&<p>Saknas: {preview.required_mapping_missing.join(", ")}</p>}
      </div>
      <div className="previewRows">
        {(preview.preview||[]).map((x,i)=><article key={i}>
          <small>{x.category_hint||"Kategori okänd"} · {x.detected_format||"Format okänt"}</small>
          <b>{x.title}</b>
          <span>{Math.round(x.price_sek)} kr · {x.stock_status}</span>
        </article>)}
      </div>
      <div className="intakeActions">
        <button disabled={busy||!preview.ready} onClick={save}>SPARA VALIDERAD PROFIL</button>
        <button disabled={busy||!preview.ready||!sourceUrl} onClick={activate}>AKTIVERA FEED-ADAPTER</button>
      </div>
      <p className="intakePolicy">Aktivering ändrar aldrig butikens policy-status. Om feed/API inte är godkänd blockeras automatisk körning fortfarande.</p>
    </section>}
    {selected&&<p className="intakeCurrent">Vald butik: <b>{selected.name}</b> · nuvarande policy: <b>{selected.policy_status}</b></p>}
    {status&&<div className="intakeStatus">{status}</div>}
  </div>
}
