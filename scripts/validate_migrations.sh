#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL must be set to a disposable PostgreSQL database." >&2
  exit 1
fi

echo "Applying all Alembic migrations to the validation database..."
alembic upgrade head

echo "Comparing the migrated schema with the SQLAlchemy models..."
alembic check

echo "Migration validation passed."
