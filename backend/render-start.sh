#!/usr/bin/env bash
set -eu

if [ -n "${DATABASE_URL:-}" ]; then
  DATABASE_URL="${DATABASE_URL/postgres:\/\//postgresql+psycopg://}"
  DATABASE_URL="${DATABASE_URL/postgresql:\/\//postgresql+psycopg://}"
  export DATABASE_URL
fi

alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
