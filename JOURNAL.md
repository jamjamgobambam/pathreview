# Week 7 — Issue selection
Issue Overview
---

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅ ] Issue added to cohort ledger

**Tier:** [ ] Tier 1  [ ] Tier 2  [✅] Tier 3 

Tier 3 is a good fit for me because this issue requires understanding how the CI infrastructure, database, migration system, and SQLAlchemy models work together across the codebase. My previous backend SWE experience gives me a strong foundation for working across multiple system components and understanding how changes in one part of the system affect others.

**Issue link:** https://github.com/ascherj/pathreview/issues/129

**Issue title:** Add a database migration validation step to CI that checks all migrations can be applied cleanly

**Branch name:** test/129-migration-validation


Problem summary
---
**Overview**: Add scripts/validate_migrations.sh to create or use a fresh database, run all database migrations in order, and verify that the resulting schema matches the SQLAlchemy models. Update .github/workflows/ci.yml to execute the validation script as part of the CI workflow.

**Behavior Missing**: The project currently relies on manually testing database schema migrations before merging. CI does not automatically verify that migrations can be applied sequentially to a fresh database or that the resulting schema matches the current SQLAlchemy model definitions.

**Success Indicator**: A CI run successfully executes scripts/validate_migrations.sh against a fresh database, applies all migrations in order, and passes the schema comparison against the SQLAlchemy models. The CI check should fail if a migration cannot be applied or if the resulting schema is inconsistent with the models.

**Relevant Files**:
- `.github/workflows/ci.yml`
- `scripts/validate_migrations.sh`

# Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/2ef5a45ea958d13a3b4b8a89bb1df07fe670395d 

**Reproduction summary:**
Because #129 is a *missing* safeguard, the reproducible fact is that CI's result is **invariant to migration/model drift** — nothing in `.github/workflows/ci.yml` applies migrations to a fresh DB and compares the result to the SQLAlchemy models. I proved this two ways: (1) structurally, `ci.yml` runs no `alembic upgrade`/`alembic check`; (2) behaviorally, I added a `reviewer_notes` column to the `Review` model with no matching migration, and **every CI job returned the same exit code as before the drift** (see table below), while a fresh-DB `alembic check` — the check CI lacks — detected the added column and failed non-zero.

**Reproduction evidence (manual command replication, model-ahead drift):**

Setup: `docker compose up -d db`; `DATABASE_URL=postgresql+asyncpg://pathreview:pathreview@localhost:5433/pathreview_dev`.

| Command (mirrors a CI job / the missing check) | (a) schema matches models | (b) `reviewer_notes` added, no migration |
|---|---|---|
| `ruff check .` | exit 1 | exit 1 |
| `black --check .` | exit 1 | exit 1 |
| `mypy …` | exit 2 | exit 2 |
| `pytest tests/unit` | exit 1 (53 failed) | exit 1 (53 failed) |
| `pytest tests/integration` | exit 5 (no tests) | exit 5 (no tests) |
| **CI verdict — depends on drift?** | — | **NO — identical** |
| `alembic upgrade head` *(not in CI)* | exit 0 | exit 0 (applies cleanly) |
| `alembic check` *(not in CI)* | non-zero — `uq_users_email` diff | non-zero — **`Detected added column 'reviews.reviewer_notes'`** + `uq_users_email` |

Key observations:
- **CI outcome never changes** when the model drifts from the migrations — the mismatch is invisible to every existing job. (Note: `ruff`/`black`/`mypy`/`unit`/`integration` are already red for *unrelated planted issues*; `mypy` exit 2 is an environmental numpy-stub/py3.11 quirk. None of these detect or are affected by the schema drift.)
- Migrations still **apply cleanly** (`upgrade head` = 0); only the model-vs-schema comparison catches the drift.
- Bonus finding: `alembic check` fails **even on the clean tree** because migration `001` creates a `uq_users_email` unique constraint that the `User` model declares only as a unique index — a pre-existing, already-merged model/migration inconsistency that CI never surfaced. This is live proof the gap has already bitten.

**PLAN.md link:** https://github.com/bgayatri3/pathreview/blob/test/129-migration-validation/PLAN.md  — full reproduction plan in `PLAN.md` / `~/.claude/plans/`.


**Blockers or open questions:**
- The eventual `scripts/validate_migrations.sh` must (a) force `DATABASE_URL` to the `+asyncpg` scheme (CI's integration job uses the sync `postgresql://`, but `alembic/env.py` builds an async engine), and (b) add a `naming_convention` to `Base.metadata` and/or reconcile the `uq_users_email` constraint so `alembic check` isn't noisy — otherwise the new gate fails on the pre-existing constraint diff before it ever sees real drift.

# Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the full fix from PLAN.md (Part B) and verified it end-to-end against a local Postgres:
- **Sub-task 1 — script:** added `scripts/validate_migrations.sh`, which normalizes `DATABASE_URL` to the `+asyncpg` driver `alembic/env.py` needs, resets the target DB to an empty `public` schema, runs `alembic upgrade head`, round-trips `downgrade base` → `upgrade head` (catches broken downgrades), and runs `alembic check`. Confirmed **exit 0 in-sync** (`No new upgrade operations detected`) and **exit non-zero on drift** (re-injected the `reviewer_notes` model column → `Detected added column 'reviews.reviewer_notes'`).
- **Sub-task 2 — schema reconciliation:** added `UniqueConstraint("email", name="uq_users_email")` to the `User` model so `Base.metadata` matches migration `001`. This clears the pre-existing `alembic check` false positive documented in Week 8, so the new gate is green when in sync (no new migration needed — the constraint already exists in the DB).
- **Sub-task 3 — CI wiring:** added a dedicated `migration-validation` job to `.github/workflows/ci.yml` (own Postgres service) that runs the script, plus a `make validate-migrations` target for local parity.
- **Sub-task 4 — tests:** added `tests/unit/test_user_model.py` and `tests/integration/test_migration_validation.py` (both pass locally).

**Next steps:**
Open a draft PR and request peer/mentor feedback; fill in the PR template; record the final `make check` / `make test-unit` results and the pre-existing-failure note; complete Check-in 2 with the PR link.

**Blockers:**
None. Note: the repo has pre-existing, unrelated failures (`make check` fails at `ruff`/`black` style and a `mypy` numpy-stub/py3.11 quirk; `make test-unit` has 53 failing tests from other planted issues). My changed files pass `ruff`/`black`/`mypy` individually, and the unit suite goes from 375 → 376 passing with no new failures.

---

### Check-in 2 (end of week)

**PR link:** _pending — will be added once the PR is opened_

**Branch:** `test/129-migration-validation`

**What you built:**
A CI safeguard for database migrations: `scripts/validate_migrations.sh` applies every Alembic migration in order to a fresh database and verifies (via `alembic check`) that the resulting schema matches the SQLAlchemy models, and a new `migration-validation` CI job runs it on every PR. A one-line `User` model fix removes a pre-existing model/migration drift so the check is green when the schema is consistent and red when it isn't.

**Tests added or updated:**
- `tests/unit/test_user_model.py` — asserts the `User` model declares the `uq_users_email` unique constraint (guards the schema reconciliation; runs in `make test-unit`).
- `tests/integration/test_migration_validation.py` — drives `scripts/validate_migrations.sh` end-to-end against a real Postgres and asserts it exits 0, i.e. all migrations apply cleanly, the downgrade round-trip works, and there is no schema/model drift.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
_(In this codebase with documented pre-existing failures, "passes" = my changes introduce no new failures; see the Blockers note above.)_

**Draft PR feedback received from:** _pending_
