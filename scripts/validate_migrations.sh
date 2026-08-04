#!/usr/bin/env bash
#
# Validate that all Alembic migrations apply cleanly to a blank database and
# that the resulting schema matches the SQLAlchemy models.
#
# Steps:
#   1. `alembic upgrade head` -- applies every migration in order. Fails if any
#      migration is broken or if the history has multiple heads.
#   2. `alembic check` -- compares the live schema against `core.models.Base`
#      metadata. Fails if the schema has drifted from the models.
#
# Input:  DATABASE_URL in the environment, pointing at a fresh, empty database.
#         The URL must use the async driver (postgresql+asyncpg://...) because
#         alembic/env.py builds an async engine from it.
# Output: exit code 0 if everything applies cleanly and matches the models,
#         non-zero (with an error message) otherwise.

set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set. Point it at a fresh, empty database." >&2
  exit 1
fi

echo "==> Applying all migrations to a blank database (alembic upgrade head)"
alembic upgrade head

echo "==> Checking that the schema matches the models (alembic check)"
alembic check

echo "==> Migrations applied cleanly and schema matches the models."
