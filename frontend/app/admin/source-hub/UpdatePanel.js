"use client";
import { useEffect, useState } from "react";

export default function UpdatePanel({ api }) {
  const [status, setStatus] = useState(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);

  async function load() {
    try {
      const r = await fetch(`${api}/admin/update-manager/status`, { cache: "no-store" });
      if (r.ok) setStatus(await r.json());
    } catch {}
  }

  useEffect(() => { load(); }, []);

  async function runNow() {
    setRunning(true); setResult(null);
    try {
      const r = await fetch(`${api}/admin/update-manager/run`, { method: "POST" });
      const data = await r.json();
      setResult(data);
      await load();
    } catch (e) {
      setResult({ status:"error", error:String(e) });
    } finally { setRunning(false); }
  }

  const summary = result || status?.last_summary;
  return <section className="updatePanel">
    <div className="updatePanelHead">
      <div><span className="kicker">DATA UPDATE MANAGER</span><h2>Uppdatera BoxFinder</h2><p>Automatiken kör var 6:e timme. Du kan också starta en kontroll direkt.</p></div>
      <button onClick={runNow} disabled={running || status?.running}>{running || status?.running ? "UPPDATERAR…" : "UPPDATERA DATA NU ↻"}</button>
    </div>
    <div className="updateMeta">
      <article><small>AUTO</small><b>VAR 6:E TIMME</b></article>
      <article><small>SENAST KLAR</small><b>{status?.last_run_finished_at ? new Date(status.last_run_finished_at).toLocaleString("sv-SE") : "Inte körd"}</b></article>
      <article><small>NÄSTA KÖRNING</small><b>{status?.next_run_at ? new Date(status.next_run_at).toLocaleString("sv-SE") : "Efter första körningen"}</b></article>
      <article><small>STATUS</small><b>{status?.running ? "KÖR" : "REDO"}</b></article>
    </div>
    {summary && <div className="updateSummary">
      <span><small>BUTIKER</small><b>{summary.checked ?? 0}</b></span>
      <span><small>LYCKADES</small><b>{summary.success ?? 0}</b></span>
      <span><small>BLOCKERADE</small><b>{summary.blocked ?? 0}</b></span>
      <span><small>HÄMTADE</small><b>{summary.fetched ?? 0}</b></span>
      <span><small>NYA</small><b>{summary.created ?? 0}</b></span>
      <span><small>UPPDATERADE</small><b>{summary.updated ?? 0}</b></span>
    </div>}
    <p className="updateWarning">Källor som inte är godkända för automatisk insamling hoppas över. Det är avsiktligt — knappen får aldrig kringgå källpolicy.</p>
  </section>
}
