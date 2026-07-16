## Week 7 — Issue selection
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

