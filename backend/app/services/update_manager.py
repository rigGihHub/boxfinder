from __future__ import annotations
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from ..database import SessionLocal
from ..models import Store, IngestionRun
from .ingestion import ingest_store, POLICY_RUNNABLE

AUTO_INTERVAL_MINUTES = 360
_state = {
    "running": False,
    "last_run_started_at": None,
    "last_run_finished_at": None,
    "last_summary": None,
    "next_run_at": None,
}

def status_payload():
    return dict(_state, auto_interval_minutes=AUTO_INTERVAL_MINUTES)

async def run_all_sources():
    if _state["running"]:
        return {"status":"already_running", **status_payload()}
    _state["running"] = True
    _state["last_run_started_at"] = datetime.utcnow().isoformat()
    summary = {"checked":0,"success":0,"blocked":0,"error":0,"fetched":0,"created":0,"updated":0,"matched":0,"review":0,"unmatched":0,"stores":[]}
    db = SessionLocal()
    try:
        stores = db.scalars(select(Store).where(Store.active.is_(True)).order_by(Store.name)).all()
        for store in stores:
            if store.collection_method == "demo":
                continue
            summary["checked"] += 1
            if store.policy_status not in POLICY_RUNNABLE:
                summary["blocked"] += 1
                summary["stores"].append({"store_id":store.id,"name":store.name,"status":"blocked","reason":f"policy={store.policy_status}"})
                continue
            run = await ingest_store(db, store)
            if run.status == "success":
                summary["success"] += 1
            elif run.status == "blocked":
                summary["blocked"] += 1
            else:
                summary["error"] += 1
            for key, attr in [("fetched","fetched_count"),("created","created_count"),("updated","updated_count"),("matched","matched_count"),("review","review_count"),("unmatched","unmatched_count")]:
                summary[key] += getattr(run, attr) or 0
            summary["stores"].append({"store_id":store.id,"name":store.name,"status":run.status,"error":run.error})
        _state["last_summary"] = summary
        return {"status":"finished", **summary}
    finally:
        db.close()
        finished = datetime.utcnow()
        _state["running"] = False
        _state["last_run_finished_at"] = finished.isoformat()
        _state["next_run_at"] = (finished + timedelta(minutes=AUTO_INTERVAL_MINUTES)).isoformat()

async def scheduler_loop():
    # Give the app a short warm-up before first automatic pass.
    await asyncio.sleep(5)
    while True:
        try:
            await run_all_sources()
        except Exception as exc:
            _state["last_summary"] = {"status":"scheduler_error","error":str(exc)}
            _state["running"] = False
        await asyncio.sleep(AUTO_INTERVAL_MINUTES * 60)
