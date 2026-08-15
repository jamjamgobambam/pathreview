## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/129

**Issue title:** Add a database migration validation step to CI that checks all migrations can be applied cleanly

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The current issue is that there needs to be database migration validation, as a broken migration can be committed and cause future issues. The migration validation creates a new database, runs all migrations, and then checks the models. The areas of the codebase that are affected are `alembic` and `.github/workflows/ci.yml`. With a script for the migration validation, errors can be caught and detected before merge, so only clean migrations make it in.

**Branch name:** feat/129-ci-migration-validation

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### Selection notes — "Is this right for me?" checklist

I wanted to work on a skill I have never done to challenge myself. I currently have no devops experience so I thought choosing this issue will help me learn and make future projects easier to complete. The scope is reasonable as, it's one script plus one CI job, with no production app code to change, so it's realistic to finish in my timeline. I'm new to GitHub Actions, so the push-and-watch feedback loop will take a few iterations.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/kelp-Shake/pathreview/commit/dcdfc6d8ecc50e45773baae34f567c2bb5b3bcfe

**Reproduction summary:**
I brought the local stack up (`colima start`, then `docker compose up -d`) and ran the two migration commands against a fresh Postgres. `alembic upgrade head` applied all the migrations fine, but `alembic check` failed with a drift error. It found a `remove_constraint` for `uq_users_email`, which means the database the migrations build has a unique constraint on `users.email` that the current `User` model doesn't declare anymore. The model just uses `unique=True, index=True`, which makes a unique index instead of a named constraint. This is the kind of drift that is the CI check is supposed to catch on its own.

Reproduction steps and observed output:

```
$ alembic upgrade head      # applies cleanly

$ alembic check
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare.constraints] Detected removed unique constraint 'uq_users_email' on 'users'
ERROR [alembic.util.messaging] New upgrade operations detected: [('remove_constraint', UniqueConstraint(Column('email', NullType(), table=<users>)))]
  FAILED: New upgrade operations detected: [('remove_constraint', UniqueConstraint(Column('email', NullType(), table=<users>)))]
```

**PLAN.md link:** https://github.com/kelp-Shake/pathreview/blob/feat/129-ci-migration-validation/PLAN.md

**Walkthrough video (recommended):** N/A, not recorded (optional, not graded)

**Blockers or open questions:**
My main open question is how to fix the existing `uq_users_email` drift. I can either update the `User` model to declare the constraint, or add a new migration that drops it. Both fix the drift, so I need to pick one in Week 9 before the CI check can pass.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I answered the Week 8 open question first and went with updating the `User` model instead of adding a drop-constraint migration. The migration is what every existing database already has, so declaring `UniqueConstraint("email", name="uq_users_email")` in `__table_args__` makes the model match reality without changing anyone's schema. Adding a migration would have turned a CI-only PR into a data-layer one.

With that decided, steps 1–4 of my PLAN.md are done:
- `scripts/validate_migrations.sh`  runs `alembic upgrade head` then `alembic check` under `set -euo pipefail`, and refuses to run if `DATABASE_URL` is missing or isn't using the asyncpg driver (`alembic/env.py` builds an async engine, so a sync URL fails with a confusing error).
- `validate-migrations` job in `.github/workflows/ci.yml` Postgres 16 service container copied from the existing `test-integration` job, pointed at its own empty `pathreview_migrations` database.
- `tests/unit/test_migrations.py` 8 unit tests covering the parts of migration health that don't need a database.
- Tested locally against the compose Postgres, including step 5's on-purpose drift check.

**Next steps:**
[Push the branch and get the Actions run green, open the draft PR, ask for peer review]

**Blockers:**
[Anything slowing you down? Or leave blank.]

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** `feat/129-ci-migration-validation`

> **One blank left:** the PR link above. Delete this note once it's filled in.

**What you built:**
A `validate-migrations` CI job that runs every migration against a fresh, empty Postgres and then checks the resulting schema against the SQLAlchemy models, so drifted or broken migrations fail the PR instead of getting found by hand later. It also fixes the one piece of drift that was already in the repo: the `User` model now declares the `uq_users_email` constraint that migration 001 has been creating all along.

The job passed on GitHub Actions on the first attempt — no fixing-the-Actions-run cycle, which I'd expected to need. I put that down to copying the Postgres service container and health check from the existing `test-integration` job rather than writing them from scratch, and to checking the YAML parsed before pushing. The one thing I did have to get right on my own was the asyncpg driver in `DATABASE_URL`; a sync URL fails in a confusing way because `alembic/env.py` builds an async engine, which is why the script guards against it.

**Tests added or updated:**
`tests/unit/test_migrations.py` (new, 8 tests). `TestMigrationChain` checks the revision chain statically — unique revision ids, exactly one head, exactly one base, every `down_revision` resolving to a real migration, and every migration defining both `upgrade()` and `downgrade()`. `TestModelMigrationParity` guards the drift fix from regressing by asserting the `User` model still declares `uq_users_email` and that `ix_users_email` is still unique.

I read the revision metadata with `ast` instead of importing the migration modules, because the repo has its own `alembic/` package directory that shadows the installed `alembic` once the repo root is on `sys.path` — so `from alembic import op` fails at pytest collection time.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

Both targets run. Output on this branch:

```
$ make check
Found 182 errors.        # ruff
make: *** [lint] Error 1

$ make test-unit
53 failed, 383 passed
```

The same 53 test ids fail on `main`, and `main` reports the same 182 ruff
errors. See the comparison table below.

**Pre-existing failures (per the Week 9 instructions):**
This repo already fails its lint and unit-test checks on `main`, so I recorded a baseline before my changes and compared after. I ran the tools directly rather than through `make` (see above); these are the same commands the Makefile and CI invoke:

| Check | Baseline (unmodified) | With my changes |
|---|---|---|
| `ruff check .` | 182 errors | 182 errors (identical per-file) |
| `black --check .` | 52 files | 52 files (identical) |
| `mypy` | 1 error (numpy stub, local env) | same |
| `pytest tests/unit -m unit` | 53 failed, 375 passed | 53 failed, 383 passed |

The 53 failures are the same test ids before and after, and the +8 passing are my new tests. `ruff` and `black` are clean on the two files I touched. My changes introduce no new failures.

**Draft PR feedback received from:** none

---

### Verification notes

**Scope:** everything below is the script run **by hand on my machine**, against the
`docker compose` Postgres. It shows that the two Alembic commands behave correctly and
that the drift fix is what makes them pass. It does **not** show that the GitHub Actions
job works — that's still unverified (see the list at the end).

```
$ DATABASE_URL=postgresql+asyncpg://pathreview:pathreview@localhost:5433/pathreview_migrations \
    ./scripts/validate_migrations.sh
==> Applying all migrations to a fresh database
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema creation...
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, Add error_message column to reviews table.
==> Comparing the migrated schema against the models
No new upgrade operations detected.
==> Migrations apply cleanly and match the models
```

Then step 5 of my plan — confirming it actually goes red, not just green:

1. **Without my model fix** (reverted `core/models/user.py`): fails with the same `remove_constraint uq_users_email` error from my Week 8 reproduction. So the fix is what makes the check pass.
2. **With drift added on purpose** (a `fake_drift_column` on the `Profile` model with no migration): fails with `add_column ... fake_drift_column`, exit code 255, which is what fails the CI job. Reverted afterwards.
3. **Guard clauses**: unset `DATABASE_URL` and a sync `postgresql://` URL both exit 1 with an explanatory message instead of a confusing async-engine traceback.

---

### CI verification (dry-run PR in my own fork)

Rather than find out on the real PR, I opened a PR from my branch into my own fork's
`main`, which fires the identical workflow on GitHub's runners without touching
upstream. Checking off the list of things local runs couldn't prove:

- [x] The workflow YAML parses and `validate-migrations` appears in the checks list.
- [x] The Postgres **service container** comes up and passes its health check (`postgres service is healthy` after ~6s). Locally I used the compose database on port 5433; CI started its own on 5432.
- [x] `pip install -e ".[dev]"` succeeds on **Python 3.11.15** (I'd only built on 3.12), including asyncpg 0.31.0 and alembic 1.19.1.
- [x] `scripts/validate_migrations.sh` is **executable in the checkout** — the `100755` mode survived, the step ran rather than dying on "permission denied".
- [x] Both migrations applied to the fresh CI database and `alembic check` reported **"No new upgrade operations detected."** The whole job took 1m 1s.
- [x] The job **fails the PR** when a migration is bad. I pushed a commit adding a `drift_probe` column to the `Profile` model with no migration behind it, watched `validate-migrations` go red, then removed the commit from the branch. The log:

      ```
      INFO  [alembic.autogenerate.compare.tables] Detected added column 'profiles.drift_probe'
      ERROR [alembic.util.messaging] New upgrade operations detected:
        [('add_column', None, 'profiles', Column('drift_probe', String(length=50), table=<profiles>))]
      ##[error]Process completed with exit code 255.
      ```

      Two things I checked in that run. The migrations still applied cleanly first, so the failure came from `alembic check` (drift) rather than a broken migration — the job tells those apart. And `lint`, `typecheck` and `test-unit` returned exactly the same numbers as before the drift: 182, 99, and 53/383. **Only `validate-migrations` changed state.** A well-typed column with no migration is invisible to ruff, black and mypy — the pre-commit hooks passed on that commit too. That gap is what this issue is filling.

- [ ] `make check` / `make test-unit` run as the graders will run them (needs a populated `.venv`).

**The overall run is red, but not because of my changes.** Five other jobs fail, and
I checked each log for my three files:

| Job | Result | Mine? |
|---|---|---|
| `validate-migrations` | ✅ passed | — |
| `lint` | ❌ 182 ruff errors | No — same 182 as my baseline, and neither `core/models/user.py` nor `tests/unit/test_migrations.py` appears anywhere in the output |
| `typecheck` | ❌ 99 mypy errors in 25 files | No — `core/models/user.py` is not among them |
| `test-unit` | ❌ 53 failed / 383 passed | No — exactly my baseline, and all 8 of my new tests **passed on CI** |
| `test-integration` | ❌ exit code 5 | No — `collected 0 items`, "no tests ran"; the integration directory has no tests to run |
| `frontend` | ❌ 2 suites | No — a missing `@testing-library/user-event` dependency and a `ReviewSection` assertion |

This is the strongest version of the "no new failures" claim: not "it looks the same on
my laptop" but "the same jobs fail in the same way on CI, and none of the failures name
a file I touched."
