from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Store, StoreIntakeProfile
from .store_intake import inspect_sample, save_profile, serialize_profile

def batch_status(db: Session) -> list[dict]:
    stores=db.scalars(select(Store).where(Store.collection_method != "demo").order_by(Store.name)).all()
    profiles={p.store_id:p for p in db.scalars(select(StoreIntakeProfile)).all()}
    rows=[]
    for s in stores:
        p=profiles.get(s.id)
        if p:
            profile=serialize_profile(p,s.name)
            profile.update({
                "store_id":s.id,
                "store_name":s.name,
                "policy_status":s.policy_status,
                "adapter_key":s.adapter_key,
                "collection_method":s.collection_method,
                "active":s.active,
                "activation_ready":p.status=="validated" and bool(p.source_url or s.source_url),
                "automation_ready":p.status=="validated"
                    and bool(p.source_url or s.source_url)
                    and s.policy_status in {"feed_allowed","api_allowed"},
            })
        else:
            profile={
                "store_id":s.id,"store_name":s.name,"policy_status":s.policy_status,
                "adapter_key":s.adapter_key,"collection_method":s.collection_method,"active":s.active,
                "status":"missing","rows_seen":0,"valid_rows":0,"invalid_rows":0,
                "source_url":None,"activation_ready":False,"automation_ready":False,
            }
        rows.append(profile)
    return rows

def preview_batch_item(item: dict) -> dict:
    result=inspect_sample(
        item.get("sample_text") or "",
        item.get("feed_format") or "csv",
        item.get("field_mapping"),
    )
    result["store_id"]=item.get("store_id")
    return result

def save_batch(db: Session, items: list[dict]) -> dict:
    result={"processed":0,"validated":0,"draft":0,"errors":[],"stores":[]}
    for item in items:
        result["processed"]+=1
        try:
            store=db.get(Store,int(item["store_id"]))
            if not store:
                raise ValueError("Store not found")
            preview=preview_batch_item(item)
            profile=save_profile(
                db,store,
                feed_format=preview["feed_format"],
                mapping=preview["effective_mapping"],
                source_url=item.get("source_url"),
                base_url=item.get("base_url"),
                sample_hash=preview["sample_hash"],
                validation=preview,
            )
            if profile.status=="validated": result["validated"]+=1
            else: result["draft"]+=1
            result["stores"].append({
                "store_id":store.id,"store_name":store.name,
                "status":profile.status,"valid_rows":profile.valid_rows,
                "invalid_rows":profile.invalid_rows,
            })
        except Exception as exc:
            result["errors"].append({"store_id":item.get("store_id"),"error":str(exc)})
    return result
