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

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
I brought up the local stack (`colima start`, `docker compose up -d`) and ran the two migration commands against a fresh Postgres. `alembic upgrade head` applied all migrations cleanly, but `alembic check` failed with a drift error — it detected a `remove_constraint` operation for `uq_users_email`. That means the database built by the migrations has a unique constraint on `users.email` that the current `User` model no longer declares (the model only sets `unique=True, index=True`, which produces a unique index, not a named constraint). This is exactly the kind of drift issue #129's CI check is meant to catch automatically.

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

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]
