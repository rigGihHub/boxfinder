import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import Base, engine, SessionLocal
from .seed import seed_demo_data, seed_verified_snapshot, seed_chase_profiles, seed_chase_card_db
from .routers import products, matching, admin, deals, checklists, market, players, rankings, budget, compare, watchlist, discovery, system, chase_search
from .services.update_manager import scheduler_loop

app = FastAPI(title=settings.app_name, version=settings.version)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
    seed_verified_snapshot()
    seed_chase_profiles()
    seed_chase_card_db()
    with SessionLocal() as db:
        rankings.prime_resale_rankings(db)
    app.state.update_scheduler_task = asyncio.create_task(scheduler_loop())

@app.get("/health")
def health():
    return {"status":"ok","version":settings.version,"database":settings.database_url.split(":",1)[0]}

app.include_router(products.router)
app.include_router(matching.router)
app.include_router(admin.router)
app.include_router(deals.router)

app.include_router(checklists.router)
app.include_router(market.router)
app.include_router(players.router)
app.include_router(rankings.router)
app.include_router(budget.router)
app.include_router(compare.router)
app.include_router(watchlist.router)
app.include_router(discovery.router)
app.include_router(system.router)

@app.on_event("shutdown")
async def shutdown_update_scheduler():
    task = getattr(app.state, "update_scheduler_task", None)
    if task:
        task.cancel()

app.include_router(chase_search.router)
