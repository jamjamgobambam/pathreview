## Solution plan

**Issue:** [Implement a caching layer for repeated identical portfolio queries](https://github.com/ascherj/pathreview/issues/32)

### Understand

When a new review is submitted, the user's portfolio is analyzed through the full RAG pipeline. The expected behavior is that the system checks whether this portfolio has already been analyzed and returns the cached review instead of re-processing. In reality, no such checks exist, and the pipeline runs every time. The fix should add a caching layer that compares the portfolio content hash to existing reviews and returns the previous review if a match is found, avoiding redundant processing.

### Map

A new review request hits POST /reviews in `/api/routes/reviews.py`, which calls `create_review_endpoint()`. This endpoint calls `create_review()` and `process_review()` from `/core/services/review_service.py`. The `create_review()` function uses the Review model schema in `/core/models/review.py`, and the service layer is tested in `/tests/unit/test_review_service.py`.

The files I will touch will be /api/routes/reviews.py, /core/services/review_service.py, /unit/test_review_service.py, and /core/models/review.py.

### Plan

1. Add `content_hash` field to Review model.
2. Create `get_or_create_review()` that wraps caching logic, with `_get_cached_review()` as a helper.
3. In `get_or_create_review()`, calculate the content hash from the profile data.
4. Query the database for an existing completed review with the same content hash.
5. If found, return the cached review; otherwise, create and return a new review in pending status.
6. Update the route to check review status and only queue background processing if pending.

### Inputs & outputs

The fix takes the same input as `create_review()` — `db`, `profile_id`, and `user_id`. It produces a Review object that is either cached (with status="complete" if hash matches) or newly created (with status="pending" if no match). The Review model gains a `content_hash` field. The service refactors `create_review()` to `get_or_create_review()` with internal cache checking. The route checks review status and only queues background processing for pending reviews, skipping it for cached ones. Tests are updated to verify both cache hits and misses.

### Risks & unknowns

Using portfolio data for hashing could theoretically cause collisions, though SHA-256 makes this unlikely. Other services don't directly depend on `create_review()`, so I anticipate refactoring should not affect them.

### Edge cases

If the hash doesn't match any existing completed review, a new review in pending status is created. If a user updates their profile slightly, the hash changes and triggers a new review, which is the correct behavior for detecting portfolio changes.
