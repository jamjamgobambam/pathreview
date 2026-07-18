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
