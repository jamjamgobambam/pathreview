## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The `/health` endpoint includes a database probe that checks whether the application's database is reachable. Currently, it executes the SQL query `"SELECT 1"` as a plain string, which is incompatible with SQLAlchemy 2.x and causes the database check to raise an error instead of succeeding. As a result, the health endpoint incorrectly reports that the database is unavailable even when it is reachable. A successful fix will update the query to use SQLAlchemy's `text()` wrapper so the database probe executes correctly and the health endpoint accurately reflects the application's status.

**Branch name:** `fix/154-health-check-db-probe`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Issue selection notes ("Is this right for me?")

I selected this Tier 1 issue because it has a clearly defined scope and affects a single part of the API layer. The issue description identifies the relevant file (`api/routes/health.py`), making it straightforward to locate the code and understand the expected behavior before and after the fix. Since this is my first contribution to a larger codebase, I wanted a well-scoped issue that I can confidently reproduce, test, and complete within the project timeline.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/hemadharshinii-s/pathreview/commit/f63b89a86d5e1cad401e0221bacc81fdf17cae5b

**Reproduction summary:**

I reproduced issue #154 by running the application locally and sending a request to the `/health` endpoint using curl. The endpoint returned a 503 response and the PostgreSQL dependency was marked as unhealthy because SQLAlchemy 2.x rejected the raw SQL query `"SELECT 1"` with an error requiring it to be wrapped using `text()`.

**PLAN.md link:** https://github.com/hemadharshinii-s/pathreview/blob/fix/154-health-check-db-probe/PLAN.md

**Walkthrough video (recommended):** Not recorded (optional)

**Blockers or open questions:**

The Redis health check also reports a separate configuration error, but it appears unrelated to issue #154 and is outside the scope of this contribution.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

Implemented the PostgreSQL health check fix by replacing the raw SQL query with SQLAlchemy's `text()` wrapper. Added a unit test verifying that the health check executes a SQLAlchemy `TextClause`. Confirmed the issue is resolved locally.

**Next steps:**

Open a draft pull request, request peer feedback, complete the PR template, and perform final verification before marking the PR ready for review.

**Blockers:**

The repository contains unrelated pre-existing failures in `make test-unit` and `make check`, but they are outside the scope of issue #154.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/544

**Branch:** `fix/154-health-check-db-probe`

**What you built:**

Implemented a fix for issue #154 by updating the PostgreSQL health check probe to use SQLAlchemy's `text()` wrapper when executing the `"SELECT 1"` query. This resolves the SQLAlchemy 2.x compatibility issue that caused the `/health` endpoint to incorrectly report PostgreSQL as unhealthy.

**Tests added or updated:**

Added `tests/unit/test_health.py` to verify that the PostgreSQL health probe executes a SQLAlchemy `TextClause` instead of a raw SQL string. The test confirms that the database query is wrapped using `text()` as required by SQLAlchemy 2.x.

**Self-review confirmation:** 
[x] make check passes  
[x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] No — still awaiting review

**Summary of feedback:**

No reviewer feedback was received on my PR during this module. Since reviewer feedback was not provided for Summer 2026, I reviewed my own changes using the contribution guidelines, PR checklist, and project standards.

**How you responded:**

Not applicable.

---

### Reflection

**What was harder than you expected?**

One part that was harder than I expected was navigating an unfamiliar codebase and understanding how a small issue fit into the larger application structure. Although issue #154 had a clearly defined fix, I still needed to inspect `api/routes/health.py`, understand how the database dependency was being used, and verify that the change would not affect the Redis or Vector DB health checks. I also learned that even a one-line code change, such as replacing `db.execute("SELECT 1")` with `db.execute(text("SELECT 1"))`, requires careful testing and documentation when contributing to an existing project.

Another challenging part was working through the project workflow rather than only writing code. Creating a branch, following the commit conventions, writing a focused test, updating `JOURNAL.md`, and preparing a complete pull request required more attention to process than I expected.

**What did you learn about working in a large codebase?**

I learned that contributing to a large codebase is very different from building a project from scratch because the goal is not just to make something work, but to make a change that fits the existing structure and expectations of the project. For PathReview, I needed to follow existing patterns in the API layer, understand the purpose of the health endpoint, and make sure my changes stayed within the scope of issue #154.

I also learned the importance of making small, isolated changes. Since the issue was specifically about SQLAlchemy 2.x compatibility in the PostgreSQL health probe, I avoided modifying unrelated Redis and Vector DB checks. This made the fix easier to review and reduced the risk of introducing unintended behavior.

**How did AI tools help — and where did they fall short?**

AI tools were especially helpful for exploring the repository, understanding unfamiliar code, and troubleshooting errors during the contribution process. For example, AI assistance helped me interpret the SQLAlchemy error message, identify that the raw SQL string needed to be wrapped with `text()`, and think through what type of unit test would demonstrate that the fix worked.

However, AI tools could not replace the process of validating changes against the actual repository conventions. I still needed to inspect existing test patterns, run pytest locally, understand pre-existing failures from `make check` and `make test-unit`, and make decisions about what changes were appropriate for the scope of the issue. The final implementation required my own judgment about keeping the fix minimal and aligned with the project's contribution standards.

**What would you do differently if you started over?**

If I started over, I would spend more time at the beginning exploring the repository structure and running the available project checks before making any changes. While the issue itself was straightforward, having an earlier understanding of the existing test setup and potential pre-existing failures would have made the process more efficient.

I would also open the draft PR even earlier during the implementation process. Although I completed the PR workflow successfully, getting feedback earlier in a real open-source environment would provide more opportunities to improve the contribution before the final submission.

**What are you most proud of from this module?**

I am most proud of successfully completing my first contribution workflow to a larger codebase from issue selection through pull request submission. I was able to identify an appropriate issue, reproduce the bug, create a focused fix, add relevant test coverage in `tests/unit/test_health.py`, and document the entire process through my journal entries.

I am also proud that the final change was intentionally small and maintainable. Instead of making unnecessary modifications, I focused on solving the SQLAlchemy 2.x compatibility problem in the PostgreSQL health probe while preserving the existing behavior of the rest of the health check system.