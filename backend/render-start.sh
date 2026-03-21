#!/usr/bin/env bash
set -eu

if [ -n "${DATABASE_URL:-}" ]; then
  DATABASE_URL="${DATABASE_URL/postgres:\/\//postgresql+psycopg://}"
  DATABASE_URL="${DATABASE_URL/postgresql:\/\//postgresql+psycopg://}"
  export DATABASE_URL
fi

if python - <<'PY'
from sqlalchemy import create_engine, text
import os

database_url = os.environ.get("DATABASE_URL", "")
engine = create_engine(database_url)
with engine.connect() as conn:
    has_version_table = conn.execute(text("select to_regclass('public.alembic_version') is not null")).scalar()
    has_workers_table = conn.execute(text("select to_regclass('public.workers') is not null")).scalar()
    raise SystemExit(0 if (not has_version_table and has_workers_table) else 1)
PY
then
  alembic stamp head
fi

alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
