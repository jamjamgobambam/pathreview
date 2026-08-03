# JOURNAL

**Issue link:** https://github.com/ascherj/pathreview/issues/82

**Issue title:** Concurrent review requests for the same profile can produce inconsistent results

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Selection Reasoning:**

1. **I understand the problem.** Concurrent `POST /reviews` for the same profile race in `api/routes/reviews.py` and `core/services/review_service.py` — no per-profile lock, no idempotency, stale in-memory state across long awaits, no `IngestedSource` dedup. Before the fix: two overlapping runs overwrite each other's `sections` and double-insert evidence rows. After: duplicates are rejected up front, or serialized safely with consistent output. See problem summary below.

2. **Tier 3 is a scope match.** I've contributed to large codebases before, so navigating multi-file changes across `api/`, `core/services/`, and the DB layer isn't new territory. The problem sits squarely in mutex + caching territory, which I'm actively studying — so the difficulty is a stretch, not a leap.

3. **I've read the actual code, not just the issue.** I traced the request path through the two files, identified where the session leaks into the background task and where the state transition needs a lock + version guard, and posted a rough fix plan in [issue #82 comment](https://github.com/ascherj/pathreview/issues/82#issuecomment-5014425733).

4. **The claim count is fine (4–5), no blockers, and I've scoped it to fit before the Week 9 deadline.**

**Problem summary:**

Concurrent review requests for the same profile can produce inconsistent results because the pipeline in `api/routes/reviews.py` and `core/services/review_service.py` has no protection against overlapping runs. The request-scoped DB session leaks into the background task, `POST /reviews` has no idempotency check, the `Review` row has no lock or version guard, the in-memory review is held stale across long ingestion/agent/RAG awaits, and `IngestedSource` inserts have no dedup — so two loops can overwrite each other's `sections` and pile up duplicate ingestion rows. A successful fix gives the background task its own session, rejects duplicate in-flight creates for the same profile, gates the state transition on a per-profile lock and optimistic version, and enforces ingestion dedup so overlapping runs cannot double-insert. After the fix, two concurrent reviews should either converge on one consistent result or be safely serialized without lost writes or duplicated evidence.

**Out of scope**: LLM sampling non-determinism, external source drift, and orphaned `"processing"` rows from crashed tasks — separate issues.

**Branch name:** `fix/82-concurrent-reviews-races`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [6daedb7 — `test(api): add regression test for concurrent review race (#82)`](https://github.com/ascherj/pathreview/commit/6daedb7)

**Reproduction summary:**
Wrote a throwaway `scripts/repro_82.py` (inlined below) that opens two `AsyncSessionLocal` sessions against the local dev Postgres, seeds one User + one Profile, then fires `create_review` + `process_review` concurrently against the same `profile_id` via `asyncio.gather`. Both calls are accepted as `pending` with distinct review IDs and both pipelines run to completion — the profile ends up with **two `complete` reviews** produced from overlapping reads/writes, confirming there is no per-profile serialization today.

**PLAN.md link:** [PLAN.md on `fix/82-concurrent-reviews-races`](https://github.com/zuccamia/pathreview/blob/fix/82-concurrent-reviews-races/PLAN.md)

**Walkthrough video (recommended):** _TBD — Loom, ≤2 min_

**Blockers or open questions:**
- The original problem summary called out "double-insert `IngestedSource` rows" as a second observable symptom, but that evidence path can't be reproduced on `main`: `_run_ingestion_pipeline` constructs `IngestedSource(raw_data=...)` against a model that has no `raw_data` column, so the constructor raises `TypeError`, the surrounding `except Exception` swallows it as `*_ingestion_failed`, and no rows are ever persisted. Flagged as an adjacent finding on the issue thread and kept out of scope for this PR. The concurrency race itself still reproduces cleanly via the two overlapping `complete` reviews above.

<details>
<summary>Reproduction script (inlined; not committed to the repo)</summary>

```python
"""Reproduce issue #82: concurrent reviews for the same profile race.

Runs against the local dev stack (Docker Postgres). Demonstrates the core
symptom called out in the issue: `POST /reviews` has no per-profile
serialization, so two overlapping requests both create pending reviews and
both drive `process_review` to completion against the same profile state.

Run:

    python -m scripts.repro_82

Prereqs: postgres up (docker compose up -d db), migrations applied
(alembic upgrade head).
"""

import asyncio
import sys
from uuid import uuid4

from sqlalchemy import delete, select

from core.database import AsyncSessionLocal
from core.models.ingested_source import IngestedSource
from core.models.profile import Profile
from core.models.review import Review
from core.models.user import User
from core.services.review_service import create_review, process_review


async def _make_fixture(db) -> Profile:
    user = User(
        id=str(uuid4()),
        email=f"repro-{uuid4().hex[:8]}@example.com",
        hashed_password="not-a-real-hash",
    )
    db.add(user)
    await db.flush()

    profile = Profile(
        id=str(uuid4()),
        user_id=user.id,
        github_username="octocat",
        portfolio_url="https://example.com",
        resume_filename="resume.pdf",
        resume_text="resume body",
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def _cleanup(db, profile_id: str, user_id: str) -> None:
    await db.execute(delete(IngestedSource).where(IngestedSource.profile_id == profile_id))
    await db.execute(delete(Review).where(Review.profile_id == profile_id))
    await db.execute(delete(Profile).where(Profile.id == profile_id))
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()


async def demonstrate_race() -> bool:
    print("Fixture: one User + one Profile.")
    async with AsyncSessionLocal() as db_a, AsyncSessionLocal() as db_b:
        profile = await _make_fixture(db_a)

        print("\nFiring two concurrent create_review calls for the same profile…")
        review_1, review_2 = await asyncio.gather(
            create_review(db_a, profile.id, profile.user_id),
            create_review(db_b, profile.id, profile.user_id),
        )
        print(f"  request A → review {review_1.id}  status={review_1.status}")
        print(f"  request B → review {review_2.id}  status={review_2.status}")

        both_pending = review_1.status == "pending" and review_2.status == "pending"
        distinct = review_1.id != review_2.id
        print(
            f"\n  both accepted as pending?   {both_pending}"
            f"\n  distinct review ids?        {distinct}"
        )

        print("\nRunning both process_review pipelines concurrently…")
        await asyncio.gather(
            process_review(db_a, review_1.id, profile.id),
            process_review(db_b, review_2.id, profile.id),
        )

        async with AsyncSessionLocal() as reader:
            all_for_profile = (
                await reader.execute(
                    select(Review).where(Review.profile_id == profile.id)
                )
            ).scalars().all()

        completes = [r for r in all_for_profile if r.status == "complete"]
        print(f"  reviews on this profile: {len(all_for_profile)}")
        print(f"  reviews in 'complete' status: {len(completes)}")

        bug_reproduced = both_pending and distinct and len(completes) == 2
        await _cleanup(db_a, profile.id, profile.user_id)

    print(f"\n→ Race reproduced: {bug_reproduced}")
    print(
        "  Expectation once the per-profile lock lands:"
        "\n    - request A gets 201/200 with a pending review;"
        "\n    - request B is rejected with 400 while A is in flight;"
        "\n    - exactly one 'complete' review exists for the profile."
    )
    return bug_reproduced


async def main() -> int:
    print("Reproducing issue #82: concurrent reviews for the same profile\n")
    ok = await demonstrate_race()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

Observed run against local dev Postgres:

```
Fixture: one User + one Profile.

Firing two concurrent create_review calls for the same profile…
  request A → review 1dfde8f9-…  status=pending
  request B → review c164862e-…  status=pending

  both accepted as pending?   True
  distinct review ids?        True

Running both process_review pipelines concurrently…
  reviews on this profile: 2
  reviews in 'complete' status: 2

→ Race reproduced: True
```

</details>

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
PLAN.md sub-tasks 1–4 are done. `core/services/review_lock.py` implements a Redis SET NX EX primitive with a per-instance token and a compare-and-delete Lua release; `POST /reviews` in `api/routes/reviews.py` now acquires the lock before creating the row and releases it in the background task's `finally`. Concurrent callers get a 409 with the in-progress review's id. Unit tests cover the lock (acquire/release/foreign-owner/error swallow) and the route-level race regression using a fake Redis.

**Next steps:**
Run through the self-review checklist against `docs/CONTRIBUTING.md`, open the PR against `main`, and share the draft link for peer feedback before Sunday.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/591

**Branch:** `fix/82-concurrent-reviews-races`

**What you built:**
A per-profile Redis lock that serializes `POST /reviews`: the first request acquires `review_lock:{profile_id}` via SET NX EX (5-minute TTL), creates the review, and releases the lock in the background task's `finally` using a compare-and-delete Lua script so a stale TTL can't drop someone else's lock. Concurrent callers on the same profile get 409 with the in-progress review id instead of racing to insert duplicate rows.

**Tests added or updated:**
- `tests/unit/test_review_lock.py` — 6 unit tests covering SET NX EX arguments, TTL default, contention (only one acquirer wins), release Lua semantics, error swallowing during teardown, and the foreign-owner safety guarantee.
- `tests/unit/test_reviews_race.py` — regression test that exercises two concurrent `POST /reviews` calls against a fake Redis and asserts exactly one 201 and one 409.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Pre-existing ruff/mypy failures unrelated to issue #82 documented in the PR description; my changes introduce no new failures.)

**Draft PR feedback received from:** @hkumar30 (peer review exchange)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
- Peer reviewer: PR description promised `409` with an in-progress review id, but the code returned `400` with a static message; `lock.acquire()` sat above the endpoint's `try:` block, so a Redis outage there bypassed the endpoint's logged error path.
- Architectural reviewer: lock design is sound, but the background task still uses the request-scoped `AsyncSession`, so the lock only prevents duplicate rows, not corrupted state within a single review run. Asked me to be explicit in the PR description about what the fix does and doesn't guarantee.

**How you responded:**
Two commits: (1) 400 → 409 with `profile_id` in the detail; (2) wrapped `acquire()` in its own try/except that emits a dedicated `review_lock_acquire_error` log and returns 500 with a specific message, plus a unit test simulating a Redis outage. Updated the PR body so the "409" wording matches what shipped and added a **Scope** section naming what's in scope (row-level duplication) and what's deferred (session lifecycle in `process_review`), linking my earlier out-of-scope comment on the issue.

---

### Reflection

**What was harder than you expected?**
Writing the PR description honestly. I paraphrased from PLAN.md instead of re-reading the code, and shipped "409 with the review id" in the description while the code returned 400 with no id. Intent documents drift the moment you start implementing — the PR body has to be written against the diff, not the plan.

**What did you learn about working in a large codebase?**
The bar is "don't break things," not "make everything green" — `main` had 53 failing tests and 186 ruff errors, and the honest move was to note the baseline and confirm my diff added zero new failures rather than treat pre-existing debt as my scope. And a surprising amount of review is about the PR description itself: in a shared codebase it's the primary interface for everyone who comes after you.

Reviewing a peer's health-check PR also pushed me to articulate the codebase's dependency-injection pattern out loud — something I'd applied correctly in my own PR without having to defend it. The pattern has two halves that give different perks: services take their Redis/DB client as a plain constructor argument (no `Depends`), which is what keeps them framework-independent — the same code runs from a worker or a script, not just a FastAPI request. The route, on the other side, wires those clients via `Depends(get_redis_client)`, which is what enables clean test overrides (`app.dependency_overrides[...]`) and self-documenting endpoint signatures. Applying a convention correctly and being able to explain *why* each half is shaped that way are two different skills, and code review is where the second one gets built.

**How did AI tools help — and where did they fall short?**
Helped most with navigation, running the test/lint/typecheck matrix, drafting commits and messages, and reasoning through the compare-and-delete release. Fell short on judgment calls that needed codebase or stakeholder context — it drafted a verbose PR body I hadn't approved, defaulted to 503 for the Redis-outage case when the existing pattern was 500, and ran `gh pr create` against my fork instead of upstream without checking `git remote -v` first (I would have caught that if I'd been driving the terminal myself). Excellent at *doing* a specific thing well; needs a human on the "which thing" and "how much" calls, and on the sanity checks that live in muscle memory rather than in the current context.

**What would you do differently if you started over?**
Write the PR description last, from the diff, not from the plan — that's where the 409/400 mismatch came from. Decide up front whether the concurrency guard and the session-lifecycle fix ship together, and put that decision in the PR body from the first draft rather than letting a reviewer draw the scope line for me. And when delegating routine git/gh operations to AI, name the pre-flight checks explicitly (remote, branch target, staged files) instead of assuming they'll happen — the assistant is confident enough to skip them if I don't ask.

**What are you most proud of from this module?**
The compare-and-delete Lua release. My first draft had a bare `DEL`, which would silently delete a foreign owner's key if my TTL expired mid-pipeline and a fresh request took the same lock. Adding a per-instance token and gating the delete on `GET == token` is the one change that made the lock actually safe rather than probably-safe-most-of-the-time — and it's the specific piece both reviewers called out.

