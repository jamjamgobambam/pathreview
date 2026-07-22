\## Solution plan



\*\*Issue:\*\* Test coverage for core/services/review\_service.py is below 40% (#109)

https://github.com/ascherj/pathreview/issues/109



\### Understand

`review\_service.py` currently has 22% test coverage. The main orchestration function,

`process\_review`, and its helper functions (`\_run\_ingestion\_pipeline`,

`\_run\_agent\_orchestration`, `\_run\_rag\_retrieval\_generation`, `\_run\_safety\_checks`)

have almost no tests. Expected behavior: process\_review should reliably set the review's

status to "complete" on success, "failed" on a safety check rejection, and "failed" on

any unhandled exception, while ingestion errors for individual sources (GitHub, portfolio,

resume) should be logged but not crash the whole pipeline. None of this branching is

currently verified by tests.



\### Map

Files I expect to touch:

\- `tests/unit/test\_review\_service.py` (primary file — adding new test cases)

\- Possibly `core/services/review\_service.py` (only if a test reveals an actual bug,

&#x20; not just a coverage gap)



Functions to cover:

\- `process\_review` (lines 98-194): success path, safety-check-failure path, profile-not-found path, unhandled-exception path

\- `\_run\_ingestion\_pipeline` (lines 202-\~230): success case, and case where one source (e.g. GitHub) throws but others still process

\- `\_run\_agent\_orchestration` / `\_run\_rag\_retrieval\_generation` (lines \~230-279): basic output shape validation

\- `\_run\_safety\_checks` (lines 369-390): passing case, missing-sections case, invalid-confidence case



\### Plan

1\. Write tests for `process\_review` success path (mock all helper functions to return valid data, assert status becomes "complete")

2\. Write tests for `process\_review` failure paths (profile not found, safety check fails, unhandled exception raised mid-pipeline)

3\. Write tests for `\_run\_ingestion\_pipeline` covering partial failure (one source fails, others still return data)

4\. Write tests for `\_run\_safety\_checks` covering all three validation branches (missing sections, missing name/content, invalid confidence range)

5\. Run full coverage report again and confirm we've crossed the 40% threshold, targeting closer to 70-80% for this file



\### Inputs \& outputs

Input: a `review\_id` and `profile\_id` (UUIDs), plus a mocked `db` session and mocked profile data.

Output: assertions on the `Review` object's `status` field, and on what gets passed to `db.commit()`.



\### Risks \& unknowns

\- The 13 pre-existing failing tests (AsyncMock misconfiguration for `get\_review`/`list\_reviews`)

&#x20; are NOT part of this issue's scope, but they run in the same file — need to make sure my new

&#x20; tests don't accidentally depend on shared broken fixtures.

\- Not yet sure how the shared `mock\_db\_session` fixture is defined at the top of

&#x20; `test\_review\_service.py` — need to check whether I can reuse it as-is or need my own mocking pattern for `process\_review`'s multiple `db.execute` calls.

\- `process\_review` calls multiple helper functions in sequence — mocking all of them correctly

&#x20; without conflicting patches could get fiddly.



\### Edge cases

\- Profile has no GitHub username, no portfolio URL, and no resume text at all (empty ingestion)

\- Safety check returns exactly 0 or exactly 1 for confidence (boundary values)

\- `review` is None when `process\_review` starts (already-deleted review)

\- Exception raised inside the outer `except` block itself (the fallback status update fails too)

