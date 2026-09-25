from sqlalchemy.pool import NullPool

from app.database import engine


def test_sqlite_uses_non_blocking_connection_pool():
    if engine.url.get_backend_name() == "sqlite":
        assert isinstance(engine.pool, NullPool)
