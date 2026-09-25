from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool
from .config import settings

is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
# Render currently runs the catalog from SQLite. A bounded QueuePool can be
# exhausted by a short burst of server-rendered catalog requests even though
# every FastAPI dependency closes its Session correctly. SQLite connections are
# cheap; opening one per request prevents unrelated requests from waiting 30s
# for a pooled connection.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
    **({"poolclass": NullPool} if is_sqlite else {}),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
