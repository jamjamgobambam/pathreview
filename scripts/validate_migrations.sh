#!/usr/bin/env bash
#
# Validate that all Alembic migrations apply cleanly to a fresh database and
# that the resulting schema matches the SQLAlchemy models in core/models/.
#
# The script:
#   1. resets the target database to an empty schema,
#   2. applies every migration in order (`alembic upgrade head`),
#   3. round-trips down to base and back up to catch broken downgrades,
#   4. compares the migration-built schema against the models (`alembic check`).
#
# It exits non-zero if a migration fails to apply, a downgrade is broken, or the
# schema drifts from the models -- which is exactly the safeguard CI was missing.
#
# Usage:
#   scripts/validate_migrations.sh
#
# Environment:
#   DATABASE_URL  Postgres connection string. Accepts sync (postgresql://,
#                 postgresql+psycopg2://) or async (postgresql+asyncpg://) forms;
#                 it is normalized to the asyncpg driver that alembic/env.py needs.
#                 Defaults to the CI integration-test database.
#
# WARNING: this DROPs and recreates the `public` schema on the target database.
# Only run it against a disposable database (CI service, local dev/test DBs).
set -euo pipefail

# --- Resolve the database URL and force the async driver -------------------
# alembic/env.py builds a create_async_engine, so migrations need the +asyncpg
# driver even though CI's integration job exports a sync postgresql:// URL.
DB_URL="${DATABASE_URL:-postgresql://pathreview:pathreview@localhost:5432/pathreview_test}"
DB_URL="$(printf '%s' "$DB_URL" | sed -E 's#^postgresql(\+psycopg2)?://#postgresql+asyncpg://#')"
export DATABASE_URL="$DB_URL"
echo "==> DATABASE_URL=$DATABASE_URL"

# --- 0. Reset to an empty schema so migrations build everything from scratch
echo "==> Resetting public schema (fresh database)"
python - <<'PY'
import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def reset() -> None:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await engine.dispose()


asyncio.run(reset())
PY

# --- 1. Apply every migration, in order, to the fresh database -------------
echo "==> alembic upgrade head"
alembic upgrade head

# --- 2. Round-trip: full downgrade then re-upgrade (validates downgrades) --
echo "==> alembic downgrade base && alembic upgrade head (round-trip)"
alembic downgrade base
alembic upgrade head

# --- 3. Verify the migration-built schema matches the SQLAlchemy models ----
echo "==> alembic check (schema vs models)"
alembic check

echo "==> Migration validation passed."
