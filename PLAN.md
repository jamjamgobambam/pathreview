## Solution plan

**Issue:** Add a database migration validation step to CI that checks all migrations can be applied cleanly #129: https://github.com/jamjamgobambam/pathreview/issues/129

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?:

The root cause is that CI never actually runs the migrations, so nothing checks them before code reaches main. A migration could fail to apply, or it could apply fine but leave a schema that no longer matches the SQLAlchemy models, and the build would still go green either way. I actually showed this with my reproduction commit (6f6b982), where I renamed `reviews.error_message` in migration 003 so it drifts from the model, and everything still passed.

What I want instead is for CI to create a blank database, apply every migration from start to finish, and then confirm the resulting schema matches the models. If either of those fails, the build should fail too. 

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.:

- `scripts/validate_migrations.sh` — I need to create this. It's the script that runs the actual checks against a blank database.
- `.github/workflows/ci.yml` — I'll add a new migrations job here. It'll basically copy the Postgres setup from the existing `test-integration` job and then run my script.
- `alembic/env.py` and `alembic.ini` — I'm only reading these, not changing them. `env.py` already imports the models (`from core.models import Base`) and grabs the DB URL from settings, which is what alembic needs.
- `core/models/*` — read only. These are the models the migrations are supposed to match.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Write `scripts/validate_migrations.sh`. It reads the `DATABASE_URL` from the environment and runs, in order: `alembic upgrade head` (applies all migrations, fails if one is broken), and `alembic check` (compares the schema to the models and fails if there's drift).
2. Add a migrations job to `ci.yml` that stands up a Postgres service, installs deps, and runs the script with `DATABASE_URL` pointed at that service.
3. Test that it actually works: with my broken migration 003 still there, the new job should fail. Once I remove 003, it should pass. That's how I know the check does its job.
4. Remove the reproduction migration (003) once I've confirmed the check catches it, so main stays clean.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

Input is a `DATABASE_URL` pointing at a fresh, empty database, and the current migrations and models. Output is just an exit code — 0 if everything applies cleanly and matches the models, and a non-zero value with an error message if not. In CI that shows up as a passing or failing check on the PR. The only things that change are the new script and the new CI job — no app code.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- The database has to be empty every run, otherwise `upgrade head` might fail for the wrong reason. CI's throwaway Postgres service should handle that.
- Migrations run through the async driver (`postgresql+asyncpg`) in `env.py`, so I need to make sure `alembic check` actually works through that path in CI.
- `alembic check` might flag stuff the models allow on purpose (server defaults, index naming, etc.), so I want to confirm the current correct repo passes `check` before I trust it to fail on real problems.

### Edge cases
What inputs or states should your fix handle gracefully?

- A migration that can't apply → `upgrade head` fails → build fails.
- A migration that applies but drifts from the models (like my 003) → `alembic check` fails → build fails.
- No migrations, or a DB that's already up to date → should just pass without doing anything.
- Multiple heads from a branched history → `upgrade head` should error clearly instead of hanging.