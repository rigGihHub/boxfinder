from __future__ import annotations
import csv, io, json, hashlib
from datetime import datetime
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Store, StoreIntakeProfile
from ..adapters.feed_catalog import _price, _stock, _bool
from ..services.matching import normalize_title

CANONICAL_FIELDS = {
    "external_id": ["external_id","id","sku","product_id","variant_id","code","article_number","artnr","artikelnummer"],
    "title": ["title","name","product_name","product","produkt","namn"],
    "price_sek": ["price_sek","price","current_price","sale_price","pris","price_incl_vat"],
    "stock_status": ["stock_status","availability","stock","lagerstatus","lager","available"],
    "url": ["url","link","product_url","permalink","produkt_url"],
    "currency": ["currency","valuta"],
    "is_preorder": ["is_preorder","preorder","pre_order","förbokning","forbokning"],
}

REQUIRED = {"external_id","title","price_sek"}

def _norm_key(value: str) -> str:
    return str(value or "").strip().lower().replace(" ","_").replace("-","_")

def _rows_from_text(text: str, feed_format: str) -> list[dict]:
    if feed_format == "csv":
        reader=csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
        return [dict(r) for r in reader]
    if feed_format == "json":
        data=json.loads(text)
        if isinstance(data,list):
            return [x for x in data if isinstance(x,dict)]
        if isinstance(data,dict):
            for key in ("products","offers","items","data"):
                if isinstance(data.get(key),list):
                    return [x for x in data[key] if isinstance(x,dict)]
        raise ValueError("JSON must be a list or contain products/offers/items/data")
    raise ValueError("feed_format must be csv or json")

def infer_mapping(columns: list[str]) -> dict:
    by_norm={_norm_key(c):c for c in columns}
    mapping={}
    for canonical,aliases in CANONICAL_FIELDS.items():
        for alias in aliases:
            if _norm_key(alias) in by_norm:
                mapping[canonical]=by_norm[_norm_key(alias)]
                break
    return mapping

def _mapped_value(row: dict, mapping: dict, field: str):
    source=mapping.get(field)
    return row.get(source) if source else None

def validate_rows(rows: list[dict], mapping: dict, limit: int=500) -> dict:
    errors=[]
    valid=0
    category_counts=defaultdict(int)
    format_counts=defaultdict(int)
    sealed=0
    randomized=0
    preview=[]
    for idx,row in enumerate(rows[:limit],start=1):
        row_errors=[]
        external_id=str(_mapped_value(row,mapping,"external_id") or "").strip()
        title=str(_mapped_value(row,mapping,"title") or "").strip()
        price_raw=_mapped_value(row,mapping,"price_sek")
        if not external_id: row_errors.append("missing external_id")
        if not title: row_errors.append("missing title")
        try:
            price=_price(price_raw)
        except Exception:
            price=None
            row_errors.append("invalid price")
        if row_errors:
            errors.append({"row":idx,"errors":row_errors})
            continue
        valid+=1
        nrm=normalize_title(title)
        if nrm.category_hint: category_counts[nrm.category_hint]+=1
        if nrm.format: format_counts[nrm.format]+=1
        if nrm.sealed_candidate: sealed+=1
        if nrm.randomized: randomized+=1
        if len(preview)<8:
            preview.append({
                "external_id":external_id,
                "title":title,
                "price_sek":price,
                "stock_status":_stock(_mapped_value(row,mapping,"stock_status")),
                "url":str(_mapped_value(row,mapping,"url") or "").strip() or None,
                "currency":str(_mapped_value(row,mapping,"currency") or "SEK").upper(),
                "is_preorder":_bool(_mapped_value(row,mapping,"is_preorder")),
                "detected_format":nrm.format,
                "category_hint":nrm.category_hint,
                "sealed_candidate":nrm.sealed_candidate,
            })
    required_missing=sorted(REQUIRED-set(mapping))
    return {
        "rows_seen":min(len(rows),limit),
        "valid_rows":valid,
        "invalid_rows":min(len(rows),limit)-valid,
        "required_mapping_missing":required_missing,
        "ready":not required_missing and valid>0,
        "errors":errors[:20],
        "preview":preview,
        "detected_categories":dict(sorted(category_counts.items(),key=lambda x:(-x[1],x[0]))),
        "detected_formats":dict(sorted(format_counts.items(),key=lambda x:(-x[1],x[0]))),
        "sealed_candidates":sealed,
        "randomized_candidates":randomized,
    }

def inspect_sample(text: str, feed_format: str="csv", mapping: dict|None=None) -> dict:
    rows=_rows_from_text(text,feed_format)
    columns=list(rows[0].keys()) if rows else []
    inferred=infer_mapping(columns)
    effective={**inferred,**(mapping or {})}
    report=validate_rows(rows,effective)
    return {
        "feed_format":feed_format,
        "columns":columns,
        "inferred_mapping":inferred,
        "effective_mapping":effective,
        "sample_hash":hashlib.sha256(text.encode("utf-8")).hexdigest(),
        **report,
    }

def save_profile(
    db: Session, store: Store, *, feed_format: str, mapping: dict,
    source_url: str|None=None, base_url: str|None=None,
    sample_hash: str|None=None, validation: dict|None=None,
) -> StoreIntakeProfile:
    profile=db.scalar(select(StoreIntakeProfile).where(StoreIntakeProfile.store_id==store.id))
    if profile is None:
        profile=StoreIntakeProfile(store_id=store.id)
        db.add(profile)
    profile.feed_format=feed_format
    profile.field_mapping_json=json.dumps(mapping,ensure_ascii=False)
    profile.source_url=source_url
    profile.base_url=base_url
    profile.sample_hash=sample_hash
    profile.status="validated" if validation and validation.get("ready") else "draft"
    if validation:
        profile.rows_seen=validation.get("rows_seen",0)
        profile.valid_rows=validation.get("valid_rows",0)
        profile.invalid_rows=validation.get("invalid_rows",0)
        profile.last_validated_at=datetime.utcnow()
    profile.updated_at=datetime.utcnow()
    db.commit(); db.refresh(profile)
    return profile

def serialize_profile(profile: StoreIntakeProfile, store_name: str|None=None) -> dict:
    try:
        mapping=json.loads(profile.field_mapping_json or "{}")
    except Exception:
        mapping={}
    return {
        "id":profile.id,"store_id":profile.store_id,"store_name":store_name,
        "feed_format":profile.feed_format,"field_mapping":mapping,
        "base_url":profile.base_url,"source_url":profile.source_url,
        "sample_hash":profile.sample_hash,"status":profile.status,
        "rows_seen":profile.rows_seen,"valid_rows":profile.valid_rows,
        "invalid_rows":profile.invalid_rows,
        "last_validated_at":profile.last_validated_at.isoformat() if profile.last_validated_at else None,
        "updated_at":profile.updated_at.isoformat(),
    }
