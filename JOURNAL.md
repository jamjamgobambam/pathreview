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

