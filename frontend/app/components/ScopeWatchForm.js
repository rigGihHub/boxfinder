"use client";

import { useState } from "react";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ScopeWatchForm() {
  const [category,setCategory]=useState("");
  const [format,setFormat]=useState("");
  const [maxPrice,setMaxPrice]=useState("");
  const [trigger,setTrigger]=useState("matching_offer");
  const [status,setStatus]=useState("");
  const [busy,setBusy]=useState(false);

  async function submit(e){
    e.preventDefault();
    setBusy(true); setStatus("");
    const body={
      category:category||null,
      format:format||null,
      max_price_sek:maxPrice?Number(maxPrice):null,
      trigger_type:trigger,
    };
    try{
      const res=await fetch(`${API}/watchlist/scope-rules`,{
        method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)
      });
      const data=await res.json();
      if(!res.ok) throw new Error(data.detail||"Kunde inte skapa bevakning.");
      setStatus("Bred bevakning skapad.");
      setTimeout(()=>location.reload(),450);
    }catch(err){
      setStatus(err.message||"Kunde inte skapa bevakning.");
    }finally{setBusy(false);}
  }

  return <form className="scopeWatchForm" onSubmit={submit}>
    <div><label>KATEGORI</label><select value={category} onChange={e=>setCategory(e.target.value)}>
      <option value="">Alla</option><option>Hockey</option><option>Fotboll</option><option>Basket</option><option>NFL</option><option>Baseboll</option><option>F1</option><option>Pokémon</option><option>One Piece</option><option>Magic</option><option>Lorcana</option><option>Yu-Gi-Oh</option>
    </select></div>
    <div><label>FORMAT</label><select value={format} onChange={e=>setFormat(e.target.value)}>
      <option value="">Alla</option><option value="hobby box">Hobby box</option><option value="retail box">Retail box</option><option value="blaster">Blaster</option><option value="booster box">Booster box</option><option value="booster bundle">Booster bundle</option><option value="elite trainer box">Elite Trainer Box</option><option value="tin">Tin</option><option value="single pack">Single pack</option>
    </select></div>
    <div><label>MAXPRIS</label><input type="number" min="1" step="1" placeholder="t.ex. 500" value={maxPrice} onChange={e=>setMaxPrice(e.target.value)}/></div>
    <div><label>VAD SKA UTLÖSA?</label><select value={trigger} onChange={e=>setTrigger(e.target.value)}>
      <option value="matching_offer">Alla nya matchande signaler</option><option value="price_drop">Prisfall</option><option value="new_90d_low">Nytt 90d-lägsta</option><option value="back_in_stock">Åter i lager</option>
    </select></div>
    <button disabled={busy}>SKAPA BRED BEVAKNING</button>
    {status&&<p>{status}</p>}
  </form>;
}
