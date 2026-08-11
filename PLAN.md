## Solution plan

**Issue:** Add a has_tests boolean to the repo analysis output - https://github.com/ascherj/pathreview/issues/50

### Understand
There is no actual logic to go through the repo to know if there is a test/ or tests/ folder.

### Map
Out of the two relevant files mentioned in the issue, only one is present in the repo.
agent/tools/github_tool.py
agent/tools/repo_analyzer.py - this is the file that is unavailable

### Plan
1. Find a way to go through the repo
2. Then create detection logic for the project to find test folder.
3. return a boolean value depending on the repo.

### Inputs & outputs
Input: repository's metadata
output: A boolean value(true or false)

### Risks & unknowns
Still figuring out how to make the detection logic

### Edge cases
I still have no idea