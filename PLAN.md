## Solution Plan

**Issue:** Add `has_tests` boolean to repository analysis output

---

### Understand

The root cause is that the current `GitHubTool` only fetches basic repository metadata (e.g., stars, forks, README) but does not analyze repository contents to detect the presence of tests.

This issue was **confirmed via a failing unit test**, which demonstrated that the `has_tests` field is currently missing from the metadata output.

The expected behavior is to include a `has_tests` boolean field indicating whether a repository contains common testing indicators such as:
- `tests/` or `test/` directories  
- `pytest.ini` file  
- files matching `test_*.py`  

Currently, this information is not included in the output.

---

### Map

**Relevant files and components:**

- `agent/tools/github_tool.py`
  - `_fetch_repo_metadata()` → assembles repository metadata
  - `_has_readme()` → reference pattern for helper methods

**Tests**

 `tests/unit/test_github_tool.py`

Used to validate:

- Metadata includes `has_tests`
- Repositories containing tests return `True`
- Repositories without tests return `False`

---

**External dependencies:**
- GitHub API endpoints:
  - `/repos/{owner}/{repo}`
  - `/repos/{owner}/{repo}/git/trees/{branch}`

---

### Plan

**Step 1: Reproduce the Current Failure**

Actions:

- Add a failing unit test in:

```
tests/unit/test_github_tool.py
```

- Verify that metadata does not currently contain:

```json
"has_tests": true
```

Run:

```bash
pytest tests/unit/test_github_tool.py -v
```

Expected failure:

```
AssertionError: Expected 'has_tests' field is missing
```

---

**Step 2: Implement Test Detection Helper**

Actions:

Create a new helper method in:

```
agent/tools/github_tool.py
```

Function:

```python
_has_tests(owner, repo)
```

The helper should inspect repository contents and return:

```python
True
```

when any supported test indicator exists:

- `tests/` directory
- `test/` directory
- `pytest.ini`
- files matching:

```
test_*.py
```

Otherwise return:

```python
False
```

---

**Step 3: Integrate `has_tests` Into Repository Metadata**

Update:

```
_fetch_repo_metadata()
```

Add the new metadata field:

```python
metadata = {
    "name": repo_json.get("name", ""),
    "description": repo_json.get("description") or "",
    "primary_language": repo_json.get("language") or "Unknown",
    "star_count": repo_json.get("stargazers_count", 0),
    "fork_count": repo_json.get("forks_count", 0),
    "open_issues_count": repo_json.get("open_issues_count", 0),
    "last_commit_date": repo_json.get("pushed_at", ""),
    "has_readme": self._has_readme(username, repo_name),
    "has_tests": self._has_tests(username, repo_name),
    "topics": repo_json.get("topics", []),
    "homepage": repo_json.get("homepage") or "",
}
```

---

**Step 4: Add Test Coverage**

Update:

```
tests/unit/test_github_tool.py
```

Add test cases for:

1. Repository containing tests:

Expected:

```json
{
  "has_tests": true
}
```

2. Repository without tests:

Expected:

```json
{
  "has_tests": false
}
```

3. Repository with only configuration indicator:

Example:

```
pytest.ini
```

Expected:

```json
{
  "has_tests": true
}
```

---

**Step 5: Validate the Fix**

Run:

```bash
pytest tests/unit/test_github_tool.py -v
```

Confirm:

- Existing tests pass
- New `has_tests` tests pass
- Metadata output contains the new field

---

### Inputs and Outputs

**Input**

The repository analysis receives:

```text
github_username
repo_name
```

The implementation uses GitHub repository information and repository tree contents.

---

**Output Before**

Current metadata response:

```json
{
  "name": "example-repo",
  "description": "Sample repository",
  "primary_language": "Python",
  "star_count": 120,
  "fork_count": 25,
  "open_issues_count": 8,
  "last_commit_date": "2026-07-20T10:30:00Z",
  "has_readme": true,
  "topics": [
    "machine-learning",
    "python"
  ],
  "homepage": "https://example.com"
}
```

---

**Output After**

Updated metadata response:

```json
{
  "name": "example-repo",
  "description": "Sample repository",
  "primary_language": "Python",
  "star_count": 120,
  "fork_count": 25,
  "open_issues_count": 8,
  "last_commit_date": "2026-07-20T10:30:00Z",
  "has_readme": true,
  "has_tests": true,
  "topics": [
    "machine-learning",
    "python"
  ],
  "homepage": "https://example.com"
}
```

---

### Risks and Unknowns

**GitHub API Rate Limits**

Risk:

`_has_tests()` may require additional GitHub API requests.

Investigation area:

```
agent/tools/github_tool.py
```

Consider minimizing API calls by using existing repository tree data when available.

---

**Incomplete Test Detection**

Risk:

Some repositories may use different testing conventions:

Examples:

```
spec/
__tests__/
custom_test_folder/
```

These may produce false negatives.

---

**Performance Impact**

Risk:

Scanning repository trees may increase execution time.

Investigation area:

```
_has_tests()
```

The implementation should avoid unnecessary API calls.

---

**GitHub API Failures**

Risk:

Network errors, permission issues, or rate limits may prevent test detection.

Expected behavior:

`has_tests` should safely default to:

```json
false
```

without breaking repository analysis.

---

**Default Branch Handling**

Risk:

Repositories may use branches other than:

```
main
master
```

Investigation area:

Use the repository default branch from GitHub metadata instead of assuming a branch name.

---

**Large Repository Handling**

Risk:

Large repositories may contain thousands of files.

The implementation should avoid downloading the complete repository contents.

---

### Edge Cases

The implementation should handle:

**Repository With No Tests**

Example:

```
src/
README.md
requirements.txt
```

Expected:

```json
{
  "has_tests": false
}
```

---

**Repository With Only pytest.ini**

Example:

```
pytest.ini
src/
```

Expected:

```json
{
  "has_tests": true
}
```

---

**Empty Repository**

Example:

```
(no files)
```

Expected:

```json
{
  "has_tests": false
}
```

---

**Case Variations**

Examples:

```
Tests/
TEST/
test_example.PY
```

The detection logic should handle case differences where possible.

---

**Private or Inaccessible Repository**

Expected:

- No crash
- Return safe default:

```json
{
  "has_tests": false
}
```

---

**Test Directory as a File**

Example:

```
test
```

exists as a file instead of a directory.

Expected:

- Do not incorrectly classify it as a test directory.

---

**Completion Criteria**

The issue is complete when:

- `GitHubTool` returns a `has_tests` boolean field.
- Test repositories return `has_tests: true`.
- Non-test repositories return `has_tests: false`.
- Unit tests pass.
- Existing repository metadata behavior remains unchanged.



