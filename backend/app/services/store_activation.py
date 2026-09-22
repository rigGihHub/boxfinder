from sqlalchemy import select
from ..models import Store, StoreIntakeProfile
from .source_hub import SOURCE_PROFILES
WEIGHTS={"Hockey":1.35,"Fotboll":1.25,"Pokémon":1.25,"Basket":1.05,"F1":1.0,"Magic":.85,"One Piece":.9,"Lorcana":.8,"Yu-Gi-Oh":.75}
READY={"feed_allowed","api_allowed"}
def activation_queue(db):
    stores=db.scalars(select(Store).where(Store.collection_method!="demo").order_by(Store.name)).all()
    rows=[]
    for s in stores:
        meta=SOURCE_PROFILES.get(s.name,{})
        coverage=meta.get("coverage",[]); priority=int(meta.get("priority",3))
        p=db.scalar(select(StoreIntakeProfile).where(StoreIntakeProfile.store_id==s.id))
        strategic=round(min(100,42+sum(WEIGHTS.get(c,.65) for c in coverage)*7+(4-priority)*8))
        readiness=(25 if p and p.status=="validated" else 0)+(25 if s.policy_status in READY else 0)+(15 if s.adapter_key else 0)+(10 if (s.source_url or (p and p.source_url)) else 0)
        blockers=[]
        if not p or p.status!="validated": blockers.append("validerad feedprofil saknas")
        if s.policy_status not in READY: blockers.append("feed/API-policy ej klar")
        if not (s.source_url or (p and p.source_url)): blockers.append("verifierad feed/API-URL saknas")
        status="ready" if not blockers else ("blocked" if "feed/API-policy ej klar" in blockers else "setup")
        action="Kör verifierad import och kontrollera katalogmatchning" if status=="ready" else ("Verifiera tillåten feed/API eller använd manuell import" if status=="blocked" else "Slutför feedprofil och källkonfiguration")
        rows.append({"store_id":s.id,"store":s.name,"priority":priority,"coverage":coverage,"strategic_score":strategic,"readiness_score":readiness,"activation_score":round(min(100,strategic*.58+readiness*.42)),"policy_status":s.policy_status,"profile_status":p.status if p else "missing","adapter_key":s.adapter_key,"status":status,"blockers":blockers,"next_action":action})
    rows.sort(key=lambda x:(-x["activation_score"],x["priority"],x["store"]))
    return {"count":len(rows),"ready":sum(x["status"]=="ready" for x in rows),"blocked":sum(x["status"]=="blocked" for x in rows),"setup":sum(x["status"]=="setup" for x in rows),"queue":rows,"top_10":rows[:10],"principle":"Strategisk prioritet och teknisk readiness hålls isär. Hög sortimentsnytta får aldrig kringgå policy eller datakvalitet."}
