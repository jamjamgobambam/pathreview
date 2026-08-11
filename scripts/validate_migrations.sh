#!/usr/bin/env bash
# Applies all Alembic migrations to $DATABASE_URL and verifies the resulting
# schema matches the SQLAlchemy models in core/models/. Used by the
# test-integration CI job and by `make migrate-check` locally.
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL must be set}"

MAX_ATTEMPTS=10
attempt=0
until alembic current >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
    echo "Could not reach the database at DATABASE_URL after $MAX_ATTEMPTS attempts" >&2
    exit 1
  fi
  echo "Waiting for database to be ready... ($attempt/$MAX_ATTEMPTS)"
  sleep 2
done

echo "==> Applying all migrations to a fresh database"
alembic upgrade head

echo "==> Checking that the schema matches the SQLAlchemy models"
alembic check

echo "Migrations applied cleanly and the schema matches the models."
