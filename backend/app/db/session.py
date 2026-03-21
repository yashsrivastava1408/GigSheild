from collections.abc import Generator

from sqlalchemy.engine import make_url
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _build_engine():
    database_url = settings.database_url.strip() or "sqlite:///./gigshield.db"
    url = make_url(database_url)
    engine_kwargs = {"pool_pre_ping": True}
    if url.drivername.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **engine_kwargs)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
