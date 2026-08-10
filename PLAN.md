## Solution plan

**Issue:** Agent session state is not cleared between reviews for the same user #43, https://github.com/ascherj/pathreview/issues/43

### Understand
<!-- What is the root cause of this issue? What behavior is expected vs. actual? -->
The root cause of the issue is not deleting the previous result, and instead continue using that result with the newly created response.

Expected: User submits a review, gets feedback that is stored. The next submission, the user submits a new review, the agent checks the new review, and gives a new response, storing the new response over the previous one.

### Map
<!-- Which files, functions, or modules are involved?
List the specific files you expect to touch. -->
1. agent/memory/session_store.py
2. agent/orchestrator.py

### Plan
<!-- What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks. -->
1. Review the issue on Github, understanding what session_store.py provides and what each function does.
2. Backtrace and find instances where session_store.py is used.
3. Check the usage, noting how its used. Check to make sure the usage follows the guidelines. If it doesn't, note what is wrong with it.
4. After finding the mistake, review what the original purpose is, how to implement it, and draft the corrected version.
5. Test the code, if it works, create a PR. Else, go back to step 4.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
The input takes in "profile_id" and "profile_data", and returns a dictionary containing "profile_id," "tool_results," and "cached_results." The fix should make sure that the output only returns the current review's results.

### Risks & unknowns
What could go wrong? What are you still unsure about?
Some unknowns raised is when "profile_id" is not unique per user/review. If they are truly unique, would deleting mid-run lose data if two reviews run concurrently on the same profile?
### Edge cases
What inputs or states should your fix handle gracefully?
First review should have 0 prior state, and review 2 should have fewer tools than review 1. Alongside this, we should be able to deal with an empty "profile_data". Reproducing these edge cases should prove the bug.