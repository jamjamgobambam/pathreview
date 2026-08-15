#!/usr/bin/env bash
#
# Validate that the Alembic migrations are healthy.
#
# Two checks, in order:
#   1. `alembic upgrade head` — every migration applies cleanly to an empty
#      database, so a broken or out-of-order revision fails here.
#   2. `alembic check` — the schema the migrations just built matches the
#      SQLAlchemy models, so model changes that never got a migration fail here.
#
# Expects DATABASE_URL to point at an EMPTY database using the asyncpg driver,
# e.g. postgresql+asyncpg://user:pass@localhost:5432/pathreview_test — that is
# the form alembic/env.py hands to create_async_engine via core.config.settings.
#
# Usage: DATABASE_URL=postgresql+asyncpg://... ./scripts/validate_migrations.sh

set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "ERROR: DATABASE_URL is not set." >&2
    echo "Point it at an empty database, e.g." >&2
    echo "  DATABASE_URL=postgresql+asyncpg://pathreview:pathreview@localhost:5432/pathreview_test" >&2
    exit 1
fi

if [[ "${DATABASE_URL}" != *"+asyncpg"* ]]; then
    echo "ERROR: DATABASE_URL must use the asyncpg driver (postgresql+asyncpg://...)." >&2
    echo "  alembic/env.py builds an async engine and will fail on a sync URL." >&2
    echo "  Got: ${DATABASE_URL}" >&2
    exit 1
fi

echo "==> Applying all migrations to a fresh database"
alembic upgrade head

echo "==> Comparing the migrated schema against the models"
alembic check

echo "==> Migrations apply cleanly and match the models"
