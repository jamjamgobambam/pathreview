## Solution plan

**Issue:** Test coverage for `core/services/review_service.py` is below 40% (https://github.com/ascherj/pathreview/issues/109)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The review service contains the main workflow for creating, processing, and finalizing reviews, but the current unit tests mostly assert basic mock interactions instead of exercising the real success and failure branches. As a result, the service logic is under-tested and the coverage target is not being met.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- `core/services/review_service.py`
- `tests/unit/test_review_service.py`
- Possibly `core/models/review.py` 

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Review the main functions in `review_service.py` and identify the key execution paths: create/list/get, successful processing, failed processing, and safety-check failure.
2. Replace the existing superficial tests with focused unit tests that mock the service dependencies and verify the review state transitions and stored output.
3. Add coverage for the ingestion, orchestration, RAG, and safety-check branches, including both success and failure cases.
4. Run the targeted test suite with coverage reporting and iterate until the relevant coverage threshold is reached.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

The tests will take mocked database sessions, profile objects, and review objects as input. They should verify that the service updates review status, stores sections and scores, and handles exceptions or safety failures correctly.

### Risks & unknowns
What could go wrong? What are you still unsure about?

The main uncertainty is how much of the workflow should be mocked versus exercised directly, so the tests need to stay focused on behavior rather than implementation details.

### Edge cases
What inputs or states should your fix handle gracefully?

- Missing review or profile records
- Safety-check failures
- Exceptions raised during processing
- Reviews with no ingested sources or missing section data
