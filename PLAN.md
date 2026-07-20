## Solution plan

**Issue:** [Test coverage for core/services/review_service.py is below 40%
#109](https://github.com/ascherj/pathreview/issues/109)

### Understand

What is the root cause of this issue? What behavior is expected vs. actual?

> The tests only cover 3 of the 8 functions within `review_service.py`. The expected behavior is that more than 40% of the functionality in `review_service.py` has a corresponding test, which would include tests for functions `process_review`, `_run_ingestion_pipeline`, `_run_agent_orchestration`, `_run_rag_retrieval_generation`, and `_run_safety_checks`. The actual behavior is that tests only cover functions `create_review`, `get_review`, and `list_reviews`.

### Map

Which files, functions, or modules are involved?
List the specific files you expect to touch.

> I only expect to touch `test_review_service.py`. Functions involved are listed above.

### Plan

What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

> - Review passing tests for function structure
> - Determine generic 'megatest' that indicates a passing `process_review` function
> - Break down `process_review` into subparts and helper functions
> - Create tests for each of those subparts and bring coverage to > 40%

### Inputs & outputs

What does your fix take as input? What should it produce or change?

> It takes `review_service.py` as input to test against the service functions. The fix should produce tests that indicate pass/fails that are not determined by syntax errors within the tests themselves, but rather by the current state of `review_service.py` in this branch.

### Risks & unknowns

What could go wrong? What are you still unsure about?

> I am not sure about the failing tests that are failing due to syntax issues. Since those failures are beyond the scope of this issue, I will focus on writing the tests for the missing functions.

### Edge cases

What inputs or states should your fix handle gracefully?

> It should handle more than the happy path for any applicable test. It should handle success paths, partial failures and full failures, rather than just successful returns.
