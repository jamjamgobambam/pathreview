## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/82]

**Issue title:** [Concurrent review requests for the same profile can produce inconsistent results]

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
[When the user submit 2 reviews back to back, there will be 2 background tasks scheduled for the same profile. 
Given each step of the process review function utilitizes nonblock async, both background tasks can be processed interwind and concurrently as the thread frees up during await. 
With the 2 tasks happening in concurrent and the processing pipeline does not verify the state/version of database records before committing, this opens up rooms for both pipelines to see/share the results and feedbacks of each other and possibility overwriting them. 
Even during fetching of profile resources, both tasks can be commit on top of each other, resulting in duplicated resources. 
The relevant codes are in `api/routes/reviews.py` and `core/services/review_service.py create_review(), process_review(), and _run_ingestion_pipeline()` and currently it is missing a profile-level write lock to ensure the concurrent review tasks will not write to the IngestedSource for a given Profile at the same time and before inserting new IngestedSources to check for duplicates against the existing.
When concurrent reviews are implemented correctly, only 1 review task will be responsible to fetch the IngestedSources and the 2nd review task will only add the missing IngestedSource or edit the IngestedSource once review 1 has finished writing and reading the Profile and all its child relationships (might be loaded into cache/heap). 
In essense, review 1 should only have visibility to Profile and IngestedSource data that existed before review 1 started its background task and changes made by its own background task. Review 1 will never be able to see changes made by review 2 regardless of when review 2 commit its changes. ]

**Branch name:** [fix/82-concurrent-reviews]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Is this right for me?

### Part 1 — Understanding the Issue

**Can I explain what this issue is asking for in my own words?**
- [x] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
  Two concurrent review requests for the same profile interleave at `await` points inside `process_review()`, so `_run_ingestion_pipeline()` can insert duplicate `IngestedSource` rows (and, once retrieval is fully wired to the DB, let one review's query see a torn mix of both runs' data). The fix is a per-profile lock so review 1 stays blind to any change review 2 makes, regardless of commit timing.

**Do I understand which part of the app is affected?**
- [x] I've located the relevant files and confirmed they exist in the codebase.
  Confirmed `api/routes/reviews.py` (`create_review_endpoint`) and `core/services/review_service.py` (`create_review`, `process_review`, `_run_ingestion_pipeline`) all exist at the lines the issue references.

**Do I understand what "done" looks like?**
- [x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.
  Before: two concurrent reviews for one profile can produce duplicated `IngestedSource` rows and nondeterministic retrieval results; after: a per-profile lock serializes the pipeline so review 1 only ever sees Profile/IngestedSource state as of its own start plus its own writes, never review 2's.

### Part 2 — Tier Fit

**Is the tier a realistic match for where I am right now?**
- [ ] Not fully confirmed — worth a second look before committing.
  The concurrency fix itself only touches two files and one DB model (no RAG/agent/infra change), which reads closer to Tier 2's "service layer + API endpoint" description than Tier 3's typical scope — worth re-checking the issue's official tier tag and my own prior-contribution experience before locking in the Tier 3 time budget.

### Part 3 — Codebase Readiness

**Can I find the relevant code?**
- [x] I've found and read the specific code the issue references (not just the file — the function or section).
  Read `create_review_endpoint`, `create_review`, `process_review`, and `_run_ingestion_pipeline` line-by-line, not just skimmed the files.

**Do I understand the surrounding code well enough to change it safely?**
- [x] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
  Traced the full call chain, the shared-session lifecycle, and the DB models involved, so I already have a rough plan: acquire a per-profile lock at the top of `process_review`, dedupe/check existing `IngestedSource` rows before inserting, release the lock at the end or on exception.

**Have I read the relevant test file?**
- [x] I've found the test file for my module and read at least one test end-to-end.
  Read `tests/unit/test_review_service.py` in full — but it only covers `create_review`/`get_review`/`list_reviews`; there are zero existing tests for `process_review` or `_run_ingestion_pipeline`, so the concurrency test will be written from scratch with no existing pattern to follow.

### Part 4 — Scope and Time

**How many others are already working on this issue?**
- [x] Checked, only 1 other person in the same section working on this issue.

**Is the scope realistic for Weeks 8–9?**
- [x] With a rough plan in mind, it's possible in 2 weeks.

**Are there any blockers or dependencies?**
- [x] This issue has no open blockers, but there might be some dependencies on other unresolved issues that will determine the scope of lock. Depending on whether there are additional DB fetches in the latter steps of the `process_review()`, the lock will need to cover the DB write and read for the current review. 


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/keyuyan1145/pathreview/commit/b5942a06dd8915b998773300631b5b8f3d8737a4]

**Reproduction summary:**
I reproduced the issue with two new integration tests in `tests/integration/test_concurrent_reviews.py`. These tests run the real `process_review()` function against a real Postgres database (not fake/mocked data), so they experience actual timing and actual concurrency, not a simulation of it. Both tests fail today, on purpose — they describe the *correct* behavior we want, which the code doesn't have yet. Once a per-profile lock is added, both tests should pass without needing to change the tests themselves.

**Test 1 — `test_concurrent_reviews_are_serialized_by_profile_lock`**

*What it does:* It creates one profile and submits two reviews for that same profile at the same time (using `asyncio.gather`, Python's way of running two pieces of async code together). For each review, it records the exact start time and end time of the step that writes to the database (`_run_ingestion_pipeline`, currently the only step that touches shared data for a profile).

*What it checks:* Two reviews for the *same* profile should never write to the database at the same time. Review 2 should only start its database work once Review 1 has completely finished and saved its result. Concretely, the test asserts two things:
1. Review 1's time window and Review 2's time window never overlap.
2. At the exact moment Review 2 starts, Review 1's status in the database already reads `"complete"` or `"failed"` — not `"processing"`. This second check matters because it proves Review 2 genuinely *waited* for Review 1 to finish, instead of the two windows just happening not to overlap by coincidence.

*Why this test exists:* This is the core bug described in the issue. Right now nothing stops two reviews for the same profile from writing to the database at the same time, so their writes can interleave.

The bug, visualized:
```
time ────────────────────────────────────────▶

Review 1 (profile A):   |--- writing to DB ---|
Review 2 (profile A):       |--- writing to DB ---|
                             ▲
                             Review 2 starts before Review 1 is done.
                             Both are touching the same profile's data
                             at the same time. This is the bug.
```

What it should look like once a per-profile lock is added:
```
time ────────────────────────────────────────▶

Review 1 (profile A):   |--- writing to DB ---|
Review 2 (profile A):                          |--- writing to DB ---|
                                                ▲
                                                Review 2 only starts after
                                                Review 1 is fully done and
                                                the lock is released.
```

The real test failure below shows exactly this: Review 2's window starts at `158895.304...` while Review 1's window doesn't end until `158895.311...` — Review 2 began about 7 milliseconds before Review 1 was finished, and Review 1's status was still `"processing"` (not done) at that moment.

**Test 2 — `test_independent_profile_is_not_blocked_by_unrelated_profile_lock`**

*What it does:* Same setup as Test 1 (two reviews on profile A), plus a third review submitted at the same time for a *completely different* profile (profile B). All three run together via `asyncio.gather`.

*What it checks:*
- Profile A's two reviews must still be fully serialized, exactly like Test 1.
- Profile B's review must *not* have to wait for profile A's lock — since it's a different profile, it should be free to run (and finish) its database writes while profile A's first review is still in progress.

*Why this test exists:* It would be easy to "fix" the bug with one lock that blocks the *entire app*, instead of one lock per profile. A single global lock would technically stop the duplicate-write bug, but it would also force every review in the whole app to run one at a time, even ones for completely unrelated profiles — a large, unnecessary performance cost, and not what the issue actually asks for. This test exists specifically to catch that mistake: if the fix uses one global lock instead of a per-profile lock, Test 1 would pass, but this test would fail.

What a correct per-profile lock looks like:
```
time ─────────────────────────────────────────────────▶

Review 1 (profile A):   |--- writing to DB ---|
Review 2 (profile A):                          |--- writing to DB ---|
Review 3 (profile B):       |--- writing to DB ---|
                             ▲
                             Review 3 runs at the same time as Review 1
                             because it's a different profile — it has
                             its own, separate lock.
```

If the lock were accidentally global, Review 3 would instead be stuck waiting behind Review 1, the same way Review 2 is — and this test would catch that.

Full failure output from running both tests today:
```
tests/integration/test_concurrent_reviews.py::TestConcurrentReviews::test_concurrent_reviews_are_serialized_by_profile_lock FAILED [ 50%]
tests/integration/test_concurrent_reviews.py::TestConcurrentReviews::test_independent_profile_is_not_blocked_by_unrelated_profile_lock FAILED [100%]

=========================================================== FAILURES ===========================================================
_________________________ TestConcurrentReviews.test_concurrent_reviews_are_serialized_by_profile_lock _________________________

self = <tests.integration.test_concurrent_reviews.TestConcurrentReviews object at 0x7f70e8c69c50>

    async def test_concurrent_reviews_are_serialized_by_profile_lock(self):
        user_id, profile_id = await self._make_profile()
        try:
            async with AsyncSessionLocal() as db1, AsyncSessionLocal() as db2:
                review1 = await create_review(db1, profile_id, user_id)
                review2 = await create_review(db2, profile_id, user_id)

                windows = []
                original_ingestion = review_service._run_ingestion_pipeline

                async def instrumented_ingestion(db, profile):
                    this_id = review1.id if db is db1 else review2.id
                    other_id = review2.id if db is db1 else review1.id

                    start = time.monotonic()
                    async with AsyncSessionLocal() as snap_db:
                        other_review = await snap_db.get(Review, other_id)
                        other_status_at_start = other_review.status

                    result = await original_ingestion(db, profile)

                    windows.append(
                        {
                            "review_id": this_id,
                            "other_status_at_start": other_status_at_start,
                            "start": start,
                            "end": time.monotonic(),
                        }
                    )
                    return result

                with patch.object(
                    review_service, "_run_ingestion_pipeline", side_effect=instrumented_ingestion
                ):
                    await asyncio.gather(
                        process_review(db1, review1.id, profile_id),
                        process_review(db2, review2.id, profile_id),
                    )

            assert len(windows) == 2, f"expected both reviews to run ingestion, got {windows}"
            first, second = sorted(windows, key=lambda w: w["start"])

            # No overlap: the second review's ingestion must not start until
            # the first review's ingestion has finished and committed.
>           assert first["end"] <= second["start"], (
                "concurrent reviews were not isolated -- ingestion windows overlapped: "
                f"{first} vs {second}"
            )
E           AssertionError: concurrent reviews were not isolated -- ingestion windows overlapped: {'review_id': '160f3dbe-b548-4953-ae37-72936ff748da', 'other_status_at_start': 'processing', 'start': 158895.303007625, 'end': 158895.311409891} vs {'review_id': '26ab8406-17ca-4680-8256-6781b315e09a', 'other_status_at_start': 'processing', 'start': 158895.304051492, 'end': 158895.313223782}
E           assert 158895.311409891 <= 158895.304051492

tests/integration/test_concurrent_reviews.py:110: AssertionError


___________________ TestConcurrentReviews.test_independent_profile_is_not_blocked_by_unrelated_profile_lock ____________________

self = <tests.integration.test_concurrent_reviews.TestConcurrentReviews object at 0x7f6cc21a7610>

    async def test_independent_profile_is_not_blocked_by_unrelated_profile_lock(self):
        """A per-profile lock must not degrade into a global one.

        Reviews 1 and 2 share profile A and must serialize exactly like the
        test above. Review 3 lives on an unrelated profile B, submitted at
        the same time. If the eventual lock is correctly scoped per profile,
        review 3's ingestion runs and commits while profile A's lock is still
        held by review 1 -- the idle event loop picks it up instead of
        queueing behind an unrelated profile's lock. If the lock is
        accidentally global, review 3 gets stuck behind review 1 too, and
        this test catches that.
        """
        user_a, profile_a = await self._make_profile()
        user_b, profile_b = await self._make_profile()
        try:
            async with (
                AsyncSessionLocal() as db1,
                AsyncSessionLocal() as db2,
                AsyncSessionLocal() as db3,
            ):
                review1 = await create_review(db1, profile_a, user_a)
                review2 = await create_review(db2, profile_a, user_a)
                review3 = await create_review(db3, profile_b, user_b)

                windows = []
                original_ingestion = review_service._run_ingestion_pipeline

                async def instrumented_ingestion(db, profile):
                    if profile.id == profile_b:
                        this_id, other_id = review3.id, None
                    else:
                        this_id = review1.id if db is db1 else review2.id
                        other_id = review2.id if db is db1 else review1.id

                    start = time.monotonic()
                    other_status_at_start = None
                    if other_id is not None:
                        async with AsyncSessionLocal() as snap_db:
                            other_review = await snap_db.get(Review, other_id)
                            other_status_at_start = other_review.status

                    result = await original_ingestion(db, profile)

                    windows.append(
                        {
                            "review_id": this_id,
                            "other_status_at_start": other_status_at_start,
                            "start": start,
                            "end": time.monotonic(),
                        }
                    )
                    return result

                with patch.object(
                    review_service, "_run_ingestion_pipeline", side_effect=instrumented_ingestion
                ):
                    await asyncio.gather(
                        process_review(db1, review1.id, profile_a),
                        process_review(db2, review2.id, profile_a),
                        process_review(db3, review3.id, profile_b),
                    )

            assert len(windows) == 3, f"expected all three reviews to run ingestion, got {windows}"
            by_id = {w["review_id"]: w for w in windows}
            w1, w2, w3 = by_id[review1.id], by_id[review2.id], by_id[review3.id]

            # Same-profile pair: still strictly serialized, same as the test above.
            first, second = sorted([w1, w2], key=lambda w: w["start"])
>           assert first["end"] <= second["start"], (
                "profile A's reviews were not isolated -- ingestion windows overlapped: "
                f"{first} vs {second}"
            )
E           AssertionError: profile A's reviews were not isolated -- ingestion windows overlapped: {'review_id': '9db2a033-9396-4cd5-8c6e-4d74c8e60b62', 'other_status_at_start': 'processing', 'start': 161953.160815048, 'end': 161953.172787515} vs {'review_id': '8733994e-3560-463c-860a-056399123cf2', 'other_status_at_start': 'processing', 'start': 161953.162143959, 'end': 161953.174309918}
E           assert 161953.172787515 <= 161953.162143959

tests/integration/test_concurrent_reviews.py:199: AssertionError

=================================================== short test summary info ====================================================
FAILED tests/integration/test_concurrent_reviews.py::TestConcurrentReviews::test_concurrent_reviews_are_serialized_by_profile_lock - AssertionError: concurrent reviews were not isolated -- ingestion windows overlapped: {'review_id': 'b8c6663d-f45c-42c2-b56...
FAILED tests/integration/test_concurrent_reviews.py::TestConcurrentReviews::test_independent_profile_is_not_blocked_by_unrelated_profile_lock - AssertionError: profile A's reviews were not isolated -- ingestion windows overlapped: {'review_id': '9db2a033-9396-4cd5-8c...
================================================= 2 failed, 1 warning in 1.29s =================================================
```


**PLAN.md link:** [https://github.com/keyuyan1145/pathreview/blob/fix/82-concurrent-reviews/PLAN.md]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
With PLAN.md's high-level plan already done from Week 8, I broke it down into a more detailed, step-by-step build plan in a new file, `IMPLEMENTATION_STEPS.md`. This spells out exactly what code needs to change and in what order: add a way to talk to Redis (a fast, separate in-memory data store, already used elsewhere in this app) so we can build a lock, pick a naming scheme for that lock, and restructure `process_review()` so it can tell apart two different kinds of failure — "we couldn't even get the lock" (a Redis problem) versus "something broke while doing the actual review work" (a normal bug). No code was written yet at this stage, just the plan.

**Next steps:**
Implement the 8 steps from `IMPLEMENTATION_STEPS.md` one at a time: add the Redis connection, wire the lock into `process_review()`, get the test setup ready (the tests now need a real Redis to talk to, not just a real database), and write two new tests for edge cases the original two tests from Week 8 didn't cover.

**Blockers:**
A few design questions came up before writing any code, and I worked through them with a reviewer instead of guessing: (1) should the lock wrap just the one step that touches the database, or the whole `process_review()` function? Decided on the whole function, since it's safer if a future step ever starts touching shared data too. (2) Does this app run as a single process, or several at once? Confirmed it's a single process (no multi-worker setting anywhere), so a simple lock is enough for now. (3) What should happen if Redis itself is down when a review tries to start? Decided the review should fail and log clearly why, rather than silently running unprotected. None of these blocked progress for long — resolving them up front avoided writing code against the wrong assumptions and having to redo it.

---

### Check-in 2 (end of week)

**PR link:** [not yet opened]

**Branch:** `fix/82-concurrent-reviews`

**What you built:**
Added a per-profile lock (backed by Redis) around `process_review()`, so two reviews for the same profile can never run at the same time — the second one now waits until the first is fully done before it starts. Reviews for different profiles are unaffected and still run at the same time as before, since each profile gets its own separate lock. If Redis itself can't be reached, the review fails safely and logs why, instead of running without that protection.

**Tests added or updated:**
`tests/integration/test_concurrent_reviews.py` — the two tests from Week 8 (same-profile reviews must not overlap; a different profile's review must not get stuck waiting behind an unrelated one) now pass against the real fix, unchanged from how they were written. Added two more tests: one confirming the lock still gets released even if a review crashes partway through (so it can't get stuck forever), and one confirming a review fails safely if Redis can't be reached at all.

Getting the test setup itself working took a few rounds of debugging, worth noting since it ate a good chunk of the week:
- The tests need their own temporary, throw-away Postgres and Redis to run against, instead of touching the real dev database. Setting the temporary Redis up the same way the temporary Postgres already was turned up two separate bugs, both about *timing*: some test files were accidentally reading which Postgres/Redis address to use before the temporary one was even ready, so they kept trying to reach the default address instead. Fixed by delaying those specific lookups until right before they're actually needed.
- Each test runs its own separate "event loop" (Python's engine for running async code), but the database and Redis connections were being reused across tests by accident, which doesn't work — like trying to keep using a phone call after the other person already hung up. Fixed by closing and reopening the connection cleanly between tests.
- A migration tool (Alembic) briefly got confused about which of two same-named things to import (its own project folder vs. the actual library), fixed by calling it a slightly different way.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none