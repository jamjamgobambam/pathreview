## Solution plan

**Issue:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

https://github.com/ascherj/pathreview/issues/159#issue-4884927126

### Understand

What is the root cause of this issue? What behavior is expected vs. actual?

The root cause of this issue is that caplog listens on stdlib, while structlog is currently writing to stderr. So even though the log is being captured after the correct event triggers its creation, caplog, which is what the test uses to check to if logs exist, isn't able to see it. This is why the assertion is throwing an error because it doesn't exist in caplog even though it does exist.

The expected behavior is that when the appropriate event triggers a log, the log exists in caplog. For this case, there was nothing to chunk, so the should flag it and a log should be generated to reflect that the issue happened in caplog.

### Map

Which files, functions, or modules are involved?
List the specific files you expect to touch.

`tests/unit/test_batch_processor.py` holds the actual test (`test_empty_chunks_list_returns_empty`). Not too much to change there except used to verify whether or not the fix is sufficient.

`core/logging.py` holds configurations related to logging that I may call or modify

`tests/conftest.py` this is where I would check how caplog is configured since it's a built-in pytest fixture. This is what I will be modifying most likely

### Plan

_What are the steps to fix this issue?_

The issue is that caplog isn't receiving the logs, so I have configure something with caplog so it finds the log. Right now, it's currently being written to stderr via structlog. I learned that you can't configure caplog to listen on stder since it's already built by pytest to listen to stdlib, so my only other option is to configure structlog to write to stdlib so caplog can find it.

1. Understand how to configure structlog to write to stdlib and what is required of that change.
2. Look into `core/logging.py` to see if there's any configuration I can use and/or adapt.
3. Figure out how to configure the option and add the configuration in conftest.
4. Verify that the test now passes

### Inputs & outputs

_What does your fix take as input? What should it produce or change?_

Module I'm changing: `tests/conftest.py`

New behavior: `test_empty_chunks_list_returns_empty` passes

### Risks & unknowns

_What could go wrong? What are you still unsure about?_

While we can infer that logging is used throughout the codebase, caplog isn't used in any of other tests, so that means logs aren't being correctly tested for. I know that it's only this test because this is the only test that mentions caplog. The issue implied a suite-wide fix was needed, but my fix does not guarantee that.

Additionally, my test doesn't check for specific content of the log like correct severity labels, so that is something that would have to be extended within the test.

### Edge cases

_What inputs or states should your fix handle gracefully?_

My fix handles the case for testing to see if the app handles a no chunks result correctly. That being said, it should also work for all tests that check for logs being generated.
