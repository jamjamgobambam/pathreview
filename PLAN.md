# Solution plan — Issue #129: DB migration validation in CI

**Issue:** [#129 — Add a database migration validation step to CI that checks all migrations can be applied cleanly](https://github.com/ascherj/pathreview/issues/129)
**Branch:** `test/129-migration-validation`

## Understand

Schema lives in two places that must agree: the SQLAlchemy **models** (`core/models/`) describe the intended tables; the Alembic **migrations** (`alembic/versions/`) build them step by step. Today they're reconciled by hand before merge — CI never applies migrations to a fresh DB or compares the result to the models. So drift (a model edited without a migration, or vice versa) merges silently. The fix adds `scripts/validate_migrations.sh` and a CI job that (1) applies all migrations to a fresh DB and (2) verifies the resulting schema matches the models, failing the build on either problem.

---

# PART A — Reproduction (step by step)

Goal: prove the safeguard is absent — CI's result is **invariant to schema/model drift**. Method: manual command replication; drift type: model ahead of migrations. *(All steps below have been run; observed results are recorded inline.)*

**Prerequisites**
- venv + deps (`.venv/Scripts` on Windows), Docker Desktop running.
- Start DB: `docker compose up -d db` (Postgres on host port **5433**, db `pathreview_dev`).
- Async URL for Alembic (env.py builds an async engine):
  `export DATABASE_URL=postgresql+asyncpg://pathreview:pathreview@localhost:5433/pathreview_dev`

**Step 1 — Baseline (schema matches models).** Record each CI job's exit code, then the migrate+check a real validation *would* run:
```bash
ruff check . ; black --check .
mypy api/ core/ ingestion/ rag/ agent/ safety/ --ignore-missing-imports
LLM_PROVIDER=mock pytest tests/unit -q
LLM_PROVIDER=mock pytest tests/integration -q
# then, against a fresh DB:
docker compose exec -T db psql -U pathreview -d postgres -c "DROP DATABASE IF EXISTS pathreview_dev; "
docker compose exec -T db psql -U pathreview -d postgres -c "CREATE DATABASE pathreview_dev;"
alembic upgrade head        # observed: exit 0 — migrations apply cleanly
alembic check               # observed: FAILS — 'Detected removed unique constraint uq_users_email'
```
Observed exit codes: `ruff=1  black=1  mypy=2  unit=1 (53 failed)  integration=5`. These jobs are already red for **unrelated planted issues** (this is a teaching repo); `mypy=2` is an environmental numpy-stub/py3.11 quirk. `alembic check` already fails on the clean tree — a real, pre-existing model/migration inconsistency (see [Fix step 2](#step-2--reconcile-the-pre-existing-uq_users_email-drift)).

**Step 2 — Inject drift.** Add a column to the `Review` model in [core/models/review.py](core/models/review.py) with **no** migration:
```python
# in class Review, after error_message:
reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
```
Run `black core/models/review.py` so lint state is unchanged.

**Step 3 — Re-run the CI commands.** Observed exit codes: `ruff=1  black=1  mypy=2  unit=1  integration=5` — **identical to Step 1.** No CI job flips. The drift is invisible to CI.

**Step 4 — Prove the drift is real (the check CI lacks).**
```bash
alembic upgrade head   # observed: exit 0 — still applies cleanly
alembic check          # observed: FAILS, non-zero, and now reports:
#   Detected added column 'reviews.reviewer_notes'
#   Detected removed unique constraint 'uq_users_email' on 'users'
```

**Reproduction result**

| Command | (a) matches | (b) drifted |
|---|---|---|
| `ruff` / `black` / `mypy` / `pytest unit` / `pytest integration` | 1 / 1 / 2 / 1 / 5 | **1 / 1 / 2 / 1 / 5 (unchanged)** |
| `alembic upgrade head` *(not in CI)* | 0 | 0 |
| `alembic check` *(not in CI)* | fails (`uq_users_email`) | fails (**+ `reviewer_notes`**) |

The mismatch is caught only by `alembic check`, which no CI job runs. **Then revert the drift** (`git checkout core/models/review.py`) so the tree is clean before the fix.


# PART B — Fix (step by step)

Two guarantees, matching the issue text: **migrations apply cleanly (in both directions)** and **the resulting schema matches the models**. Delivered as a script (the issue's explicit ask, reusable locally) plus a CI job that runs it.

## Step 1 — Write `scripts/validate_migrations.sh`

New file — applies all migrations to a fresh schema, round-trips downgrade→upgrade (catches broken `downgrade()`s), then compares schema to models via `alembic check`. Normalizes the DB URL to the async driver that `alembic/env.py` requires.

```bash
#!/usr/bin/env bash
#
# Validate that all Alembic migrations apply cleanly to a fresh database
# and that the resulting schema matches the SQLAlchemy models.
#
# Exits non-zero if a migration fails to apply, a downgrade is broken,
# or the migration-built schema drifts from core/models. Intended for CI
# and local use (`make validate-migrations`).
#
# Requires a reachable Postgres via $DATABASE_URL (default: CI service).
set -euo pipefail

# --- Resolve DB URL and force the async driver that alembic/env.py needs ---
# alembic/env.py builds a create_async_engine, so upgrades need +asyncpg,
# even though CI's integration job exports a sync postgresql:// URL.
DB_URL="${DATABASE_URL:-postgresql://pathreview:pathreview@localhost:5432/pathreview_test}"
DB_URL="$(printf '%s' "$DB_URL" | sed -E 's#^postgresql(\+psycopg2)?://#postgresql+asyncpg://#')"
export DATABASE_URL="$DB_URL"
echo "==> DATABASE_URL=$DATABASE_URL"

# --- Reset to an empty schema so migrations build everything from scratch ---
echo "==> Resetting public schema (fresh database)"
python - <<'PY'
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def reset():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await engine.dispose()

asyncio.run(reset())
PY

# --- 1. Apply every migration, in order, to the fresh database ---
echo "==> alembic upgrade head"
alembic upgrade head

# --- 2. Round-trip: full downgrade then re-upgrade (validates downgrade paths) ---
echo "==> alembic downgrade base && alembic upgrade head (round-trip)"
alembic downgrade base
alembic upgrade head

# --- 3. Verify the migration-built schema matches the SQLAlchemy models ---
echo "==> alembic check (schema vs models)"
alembic check

echo "==> Migration validation passed."
```
Make it executable: `git update-index --chmod=+x scripts/validate_migrations.sh` (or `chmod +x`).

## Step 2 — Reconcile the pre-existing `uq_users_email` drift

`alembic check` fails on `main` today because migration `001` created a **named unique constraint** `uq_users_email` on `users.email`, but the `User` model ([core/models/user.py:25](core/models/user.py#L25)) declares email only as `unique=True, index=True` — which produces the unique **index** `ix_users_email`, not the constraint. The model's metadata is therefore missing the constraint. Until this is reconciled, the new gate stays red before it can catch real drift.

Fix (minimal, no new migration — align the model to the already-applied schema): add the constraint to `User.__table_args__`:
```python
from sqlalchemy import UniqueConstraint  # add to imports
...
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_email_active", "email", "is_active"),
    )
```
*(Alternative, more thorough: set a `naming_convention` on `Base.metadata` in [core/database.py](core/database.py) so Alembic reconciles constraint/index names globally. Higher blast radius — verify no new diffs appear before choosing it.)*

After this change, `alembic check` on the clean tree must return **no** differences (empty). Confirm before wiring CI.

## Step 3 — Add a CI job that runs the script

In [.github/workflows/ci.yml](.github/workflows/ci.yml), add a dedicated job (own Postgres service, so failures are clearly attributable):
```yaml
  migration-validation:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: pathreview
          POSTGRES_PASSWORD: pathreview
          POSTGRES_DB: pathreview_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U pathreview"
          --health-interval 5s --health-timeout 5s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - run: pip install -e ".[dev]"
      - name: Validate migrations
        run: bash scripts/validate_migrations.sh
        env:
          DATABASE_URL: postgresql://pathreview:pathreview@localhost:5432/pathreview_test
```
(The script normalizes that sync URL to `+asyncpg` internally, so the job env stays consistent with the existing `test-integration` job.)

## Step 4 — Add a Makefile target (local parity)

In [Makefile](Makefile), next to `migrate`:
```make
validate-migrations: ## Apply migrations to a fresh DB and verify schema matches models
	bash scripts/validate_migrations.sh
```
(Add `validate-migrations` to the `.PHONY` line.)

---

## Inputs & outputs

**Inputs the fix consumes**
- `scripts/validate_migrations.sh` reads one input: the **`$DATABASE_URL`** env var (accepts sync `postgresql://`, `postgresql+psycopg2://`, or async `postgresql+asyncpg://`; default = the CI service URL). It also implicitly consumes the migration chain in `alembic/versions/` and `Base.metadata` (assembled from `core/models/`) — the two artifacts it compares.

**Outputs / behavior that changes**
- **New executable** `scripts/validate_migrations.sh` — no args; **exit 0** on success, **non-zero** on any un-appliable migration, broken `downgrade()`, or schema/model drift; progress to stdout. **Side effect:** `DROP SCHEMA public CASCADE` + recreate on the target DB (destructive by design).
- **Signature change** in [core/models/user.py](core/models/user.py): `User.__table_args__` gains `UniqueConstraint("email", name="uq_users_email")`. Changes only `Base.metadata` (to match the already-applied DB) — **no** new migration, **no** runtime behavior change (the constraint already exists in every migrated DB).
- **New CI job** `migration-validation` in [.github/workflows/ci.yml](.github/workflows/ci.yml): a PR to `main` now **fails** if migrations don't apply cleanly or the schema drifts — the behavior the issue asks for.
- **New Makefile target** `make validate-migrations` (local parity).

## Verification

1. **In sync → green:** on a clean tree (after Step 2), `bash scripts/validate_migrations.sh` exits 0 and prints "Migration validation passed."
2. **Drifted → red:** re-add `reviewer_notes` to the `Review` model with no migration, run the script → it fails at `alembic check` with `Detected added column 'reviews.reviewer_notes'` and exits non-zero. Revert.
3. **Broken migration → red:** temporarily break a migration's `downgrade()` → the round-trip step fails. Revert.
4. **CI:** open a PR to `main`; confirm the `migration-validation` job is green in sync and red when drift is pushed.

## Risks & unknowns

- **`alembic check` may report diffs beyond `uq_users_email`.** *Investigation path:* after the [core/models/user.py](core/models/user.py) edit (Fix step 2), run `alembic check` on a fresh DB and confirm the diff list is **empty**. If not, the remaining diffs (likely `server_default`s in migration `001` not declared on models — `users.is_active`, `reviews.status`, `ingested_sources.chunk_count`) must be reconciled too, or the gate is dead-on-arrival.
- **Global `naming_convention` alternative has unknown blast radius.** If chosen instead of the targeted `UniqueConstraint`, it lives on `Base.metadata` in [core/database.py](core/database.py) (`Base = declarative_base()`) and re-renders *all* constraint/index names. *Investigation path:* set it, run `alembic check`, confirm no new diffs across all four tables before committing.
- **Destructive `DROP SCHEMA public`** in `scripts/validate_migrations.sh` — safe only against disposable DBs (CI service, local `pathreview_test`/`pathreview_dev`); a mispointed `DATABASE_URL` wipes real data. *Mitigation to consider:* guard on DB name / `settings.app_env` before dropping.
- **Async-driver dependency:** [alembic/env.py](alembic/env.py) uses `create_async_engine`, so the script's `sed` normalization to `+asyncpg` is load-bearing; an unrecognized URL scheme passes through unchanged and fails at connect time.

## Edge cases (each = a concrete input/state the fix must handle)

1. **`DATABASE_URL` given as a sync URL** (as CI's `test-integration` job does: `postgresql://…`) → normalized to `+asyncpg` so `env.py`'s async engine connects instead of erroring.
2. **Target DB left non-empty by a prior run** (tables already present) → `DROP SCHEMA public CASCADE` first, so migrations always run against a truly fresh schema.
3. **A migration with a broken `downgrade()`** → caught by the `downgrade base` → `upgrade head` round-trip, not just the forward path.
4. **Drift in either direction** — model-ahead (column on a model, no migration) *or* migration-ahead (column in a migration, not on a model) → `alembic check` reports both; verified against the `reviewer_notes` repro.
