## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159#issue-4884927126

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The issue is that the test isn't passing for tests that test for presence of logs in caplog like in test_empty_chunks_list_return_empty in test_batch_processor.py.
We know that it's that issue because because in this example, the second assert is failing, which isolates the issue to lack of logs present in caplog. 
So, even though the process functions correctly returns an empty list when there are no chunks, 
and the empty list event is caputured (log seen in stderr), caplog isn't receiving the log.

The file I will look at will be tests/conftest.py because that's where test setup is configured, 
and since both structlog and the business logic are working, it wouldn't make sense to check the running code.

A successful fix would mean that the caplog related tests pass. 


**Branch name:** Fix/159/structlog-output-not-captured

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
