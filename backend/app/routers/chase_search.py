from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ChaseCard, VariantChaseCard, ProductVariant, Product, Offer
from ..services.chase_opportunity import opportunity_for_links

router=APIRouter(prefix="/chase",tags=["chase"])

@router.get("/search")
def search_chase(
    q: str = Query("", max_length=100),
    budget: float | None = Query(None, ge=1),
    rookie_only: bool = False,
    limit: int = Query(50,ge=1,le=100),
    db: Session = Depends(get_db),
):
    stmt=select(ChaseCard)
    if q.strip():
        stmt=stmt.where(ChaseCard.player_name.ilike(f"%{q.strip()}%"))
    if rookie_only:
        stmt=stmt.where(ChaseCard.rookie.is_(True))
    cards=db.scalars(stmt.order_by(ChaseCard.player_name,ChaseCard.card_name).limit(limit)).all()
    out=[]
    for card in cards:
        links=db.scalars(select(VariantChaseCard).where(VariantChaseCard.chase_card_id==card.id)).all()
        products=[]
        for link in links:
            v=db.get(ProductVariant,link.variant_id)
            if not v: continue
            p=db.get(Product,v.product_id)
            offers=db.scalars(select(Offer).where(
                Offer.variant_id==v.id,
                Offer.stock_status=="in_stock",
                Offer.is_preorder.is_(False)
            )).all()
            trusted=[o for o in offers if o.source_kind=="verified_snapshot" or o.match_status in ("manual_matched","auto_matched")]
            best=min(trusted,key=lambda x:x.price_sek) if trusted else None
            if budget is not None and (best is None or best.price_sek>budget): continue
            products.append({
                "variant_id":v.id,"product":p.canonical_name,"format":v.format,
                "price":best.price_sek if best else None,"store":best.store.name if best and best.store else None,
                "tier":link.tier,"odds":link.odds_text,"source_url":link.source_url,
            })
        if products:
            products.sort(key=lambda x:(x["price"] is None,x["price"] or 999999))
            out.append({
                "id":card.id,"player":card.player_name,"card":card.card_name,
                "number":card.card_number,"category":card.category,"rookie":card.rookie,
                "products":products,
            })
    return {"query":q,"budget":budget,"count":len(out),"results":out,
            "note":"Visar verifierade checklistkopplingar. Odds är formatspecifika när källan stödjer det; BoxFinder gissar inte saknade odds."}

@router.get("/players")
def players(q: str = Query("",max_length=100), db: Session=Depends(get_db)):
    stmt=select(ChaseCard.player_name).distinct()
    if q.strip(): stmt=stmt.where(ChaseCard.player_name.ilike(f"%{q.strip()}%"))
    return {"players":db.scalars(stmt.order_by(ChaseCard.player_name).limit(30)).all()}


TIER_POINTS={"BRA":20,"MYCKET BRA":38,"MONSTER":62,"JACKPOT":85}

@router.get("/best-boxes")
def best_boxes(
    player: str = Query(...,min_length=2,max_length=100),
    budget: float | None = Query(None,ge=1),
    db: Session = Depends(get_db),
):
    cards=db.scalars(select(ChaseCard).where(ChaseCard.player_name.ilike(f"%{player.strip()}%"))).all()
    grouped={}
    for card in cards:
        links=db.scalars(select(VariantChaseCard).where(VariantChaseCard.chase_card_id==card.id)).all()
        for link in links:
            v=db.get(ProductVariant,link.variant_id)
            if not v: continue
            p=db.get(Product,v.product_id)
            offers=db.scalars(select(Offer).where(Offer.variant_id==v.id,Offer.stock_status=="in_stock",Offer.is_preorder.is_(False))).all()
            trusted=[o for o in offers if o.source_kind=="verified_snapshot" or o.match_status in ("manual_matched","auto_matched")]
            best=min(trusted,key=lambda x:x.price_sek) if trusted else None
            if budget is not None and (best is None or best.price_sek>budget): continue
            row=grouped.setdefault(v.id,{"variant_id":v.id,"product":p.canonical_name,"format":v.format,
                "price":best.price_sek if best else None,"store":best.store.name if best and best.store else None,
                "cards":[],"score":0})
            row["cards"].append({"player":card.player_name,"card":card.card_name,"number":card.card_number,
                "tier":link.tier,"odds":link.odds_text})
            row["score"] += TIER_POINTS.get(link.tier,10)
    rows=list(grouped.values())
    for row in rows:
        v=db.get(ProductVariant,row["variant_id"])
        coverage_score=min(100,row["score"])
        opp=opportunity_for_links(row["cards"],v.packs if v else None,row["price"])
        row["coverage_score"]=coverage_score
        row["opportunity_score"]=opp["opportunity_score"]
        row["opportunity_per_1000_sek"]=opp["opportunity_per_1000_sek"]
        row["numeric_odds_routes"]=opp["numeric_odds_routes"]
        row["cards"]=opp["cards"]
        row["why"]=f'{len(row["cards"])} verifierade chase-vägar för {player}; {opp["numeric_odds_routes"]} har numeriska odds som kan räknas.'
        # Do not pretend checklist coverage equals probability.
        row["score"]=opp["opportunity_score"]
    rows.sort(key=lambda x:(x["opportunity_score"] is None,-(x["opportunity_score"] or 0),-(x["coverage_score"] or 0),x["price"] is None,x["price"] or 999999))
    return {"player":player,"budget":budget,"count":len(rows),"results":rows,
        "note":"Opportunity Score räknas bara när numeriska per-pack-odds finns. Checklisttäckning visas separat och används inte som låtsassannolikhet. Det är inte ekonomiskt EV."}
