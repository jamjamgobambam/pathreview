# PathReview Contribution Journal

## Week 7 – Issue Selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The database health check currently sends a raw SQL string when checking whether the database is available. SQLAlchemy 2.x no longer accepts raw SQL strings in this way, causing the health check to fail even when the database is working correctly. The fix is to wrap the SQL statement using SQLAlchemy's `text()` function so the health endpoint correctly reports the database status.

**Branch name:** `fix/154-health-check-sql-text`

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### "Is this right for me?" checklist reasoning

I selected this issue because it is labeled Tier 1 and Good First Issue, making it appropriate for a first contribution. The issue is small in scope and focuses on a single SQLAlchemy compatibility problem. The expected fix is clearly described, and I can verify the change by running the health check after updating the SQL query.

### Selection notes

The issue affects the health check endpoint that tests the database connection. SQLAlchemy 2.x requires textual SQL statements to be wrapped using the `text()` function instead of passing plain strings. I will make the smallest possible change, verify the health check works correctly, and ensure no other functionality is affected.

## Week 8 – Reproduction & Planning

### Reproduction

I investigated Issue #154 by locating the health check implementation in `api/routes/health.py`. I identified that the PostgreSQL health check executes a raw SQL string using:

```python
await db.execute("SELECT 1")
```

SQLAlchemy 2.x no longer allows raw SQL strings to be passed directly into `execute()`. Instead, the query must be wrapped using SQLAlchemy's `text()` helper. Although I was unable to fully run the application because I was still configuring Docker locally, I confirmed the issue by comparing the existing implementation with the SQLAlchemy 2.x requirements and the issue description.

### Reproduction Commit

<PASTE YOUR REPRODUCTION COMMIT LINK HERE>

### Solution Plan

Created `PLAN.md` describing:

- Files to modify
- Planned implementation steps
- Risks
- Edge cases
- Points & Remedies

### PLAN.md

<PASTE YOUR PLAN.MD LINK HERE>

### Status

- Reproduced the issue through code investigation.
- Created PLAN.md.
- Implemented the compatibility fix.
- Opened a pull request.

### Walkthrough Video

Not recorded.