# Solution Plan

**Issue:** Add detection logic that checks whether a repository has a `tests/` or `test/` directory, a `pytest.ini`, or test files matching `test_*.py`, and expose this as a boolean field in the analysis output.

## Understand

The goal of this issue is to identify whether a GitHub repository contains automated tests and expose that information as a boolean field (`has_tests`) in the repository analysis output.

While tracing the codebase, I found that `RepoAnalyzer` already contains logic to detect test-related files and directories through `_detect_tests()`. However, the detection is broader than the issue specification. For example, it currently checks whether `"test_"` appears anywhere in the file structure, which incorrectly treats files such as `docs/test_notes.md` as Python test files.

I reproduced this behavior by adding a unit test where the repository contains `docs/test_notes.md`. The current implementation reports `has_tests=True`, even though the issue specifically requires matching Python test files (`test_*.py`).

## Map

During investigation, I traced the repository metadata flow through these files:

- `agent/tools/github_tool.py`
  - Fetches GitHub repository metadata from the GitHub API.
  - Currently returns repository metadata such as language, stars, README status, and topics.

- `ingestion/parsers/repo_analyzer.py`
  - Analyzes repository metadata.
  - Contains `_detect_tests()`, which determines the `has_tests` value from the repository's `file_structure`.

- `ingestion/pipeline.py`
  - Passes the repository metadata into `RepoAnalyzer.parse()` during repository ingestion.

- `tests/unit/test_repo_analyzer.py`
  - Added a reproduction test showing that the current detection logic incorrectly classifies `docs/test_notes.md` as a Python test file because it checks for `"test_"` instead of `test_*.py`.

## Plan

1. Review the current `_detect_tests()` implementation in `RepoAnalyzer` and compare it against the issue requirements.
2. Update the detection logic so it only recognizes the required indicators:
   - `tests/`
   - `test/`
   - `pytest.ini`
   - Python test files matching `test_*.py`
3. Add unit tests covering both valid and invalid cases, including files such as `docs/test_notes.md` that should not be detected as test files.
4. Run the unit tests to verify the updated behavior and ensure existing functionality is not broken.

## Inputs & outputs

**Input**

The repository metadata passed to `RepoAnalyzer.parse()`, including the repository file structure.

Example:

```python
{
    "name": "sample-project",
    "language": "Python",
    "file_structure": [
        "app.py",
        "tests/test_app.py",
        "pytest.ini",
    ],
}
```

**Output**

The analyzer should correctly set the `has_tests` boolean in the metadata.

Examples:

```python
result.metadata["has_tests"] == True
```

or

```python
result.metadata["has_tests"] == False
```

---

## Risks & unknowns

- I need to verify whether the detection should only support Python test files (`test_*.py`) or whether other conventions (such as `spec/` or `__tests__/`) should remain supported.
- The current implementation checks for `"test_"` anywhere in the file structure, so changing it could affect existing behavior.
- I also need to confirm that any changes remain compatible with the rest of the ingestion pipeline.

---

## Edge cases

The implementation should handle:

- Repositories containing a `tests/` directory.
- Repositories containing a `test/` directory.
- A root-level `pytest.ini`.
- Python files matching `test_*.py`.
- Repositories without any tests.
- Files such as `docs/test_notes.md` that should **not** be detected as Python test files.
- Empty or missing `file_structure` data.
