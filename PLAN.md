## Solution plan

**Issue:**Add a mock GitHub API server for integration tests  https://github.com/ascherj/pathreview/issues/57

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
Root cause is missing web server for GitHub. The expected behavior is that it tests for GitHub and it does not do that. This is not a bug, it is more of a feature addition.
### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
Files I will need to add:
tests/integration/test_github_tool.py
This file should have setup script for the HTTP server and environment for the application.

tests/fixtures/github_responses/

This folder should have responses that are called and code for the mock server API.
### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
1. Check and test current testing suite
    a. Look for existing tests for code stlyes and syntax
    b. Run tests and view output before modifying code
2. Create pytest file to create a HTTP server for GitHub
    a. Use HTTP server library and create a fixture called in a otherwise empty test
3. Ensure the server works and causes no errors with existing tests
    a. Test new test on its own
    b. Test enture test suite and ensure no errors or unexpected crashes occur
3. Create test cases as in other test suites.
    a. Test pull, login

4. Run full test suite and make sure no errors or issues are found.
### Inputs & outputs
What does your fix take as input? What should it produce or change?

It should add a testing suite and be invoked by pytest. It should take in an HTTP server fixture and use that to run the tests.
### Risks & unknowns
What could go wrong? What are you still unsure about?
Testing suite could break or the AI tests could run into an infinite loop.
### Edge cases
What inputs or states should your fix handle gracefully?

If the server does not work or returns an error, it should fail all the tests not yet run for the github API mock server.


