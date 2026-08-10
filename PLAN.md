## Solution plan

**Issue:** Implement a red-teaming test suite for the prompt injection defense #71
https://github.com/ascherj/pathreview/issues/71

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The root cause is that tests/security is empty and does not contain any tests, meaning implementing an automatic test for prompt injection has to be made from scratch. The expected behavior is an automation that runs before each PR that touches "safety/" to see if the changes reduce its prompt injection defense. This leaves this repo vulnerable to any pushes that might break the security functions of the application against prompt injection.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

The files that will be included in the red team testing suite will be all the security files in safety that will be involved in prompt injection defense including prompt_defense.py. Im also expected to make new files in "tests/security" which would hold the red teaming suite in "test_prompt_injection.py". Furthermore I would have to make a file to hold all the attack payloads in "tests/fixtures/injection_attempts/".

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

Sub tasks:
- Research missing prompt_injection techniques from prompt_defense.py
- Create new file called test_prompt_injection.py
- Create the new prompt_injection tests
- Function to run tests in CI during each pr that touches safety/
- Implement Edge case catch for the pull requests with no changes to the security layer
- Implement Edge case catch for the pull requests with missing or altered security tests


### Inputs & outputs
What does your fix take as input? What should it produce or change?

The fix takes in the files with updates/changes in a pull request to validate its safety. It will produce a verdict wether the changes break or keep the functioning security against prompt injection

### Risks & unknowns
What could go wrong? What are you still unsure about?

Some areas where mistakes may arise is not including every form of prompt injection in "tests/fixtures/injection_attempts/" which would lead the app to be vulnerable, another is the tests not running in the CI in ci.yml during the pr's. Another risk is that prompt_defense.py isn't currently called anywhere in the app so running the file wont prove our current security.

### Edge cases
What inputs or states should your fix handle gracefully?

Two different states the application should handle gracefully are when inputs where the pr does not touch the safety layer and where the tests are removed or deleted from a pr.
