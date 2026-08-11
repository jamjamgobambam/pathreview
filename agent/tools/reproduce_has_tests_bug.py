"""
Reproduction for issue #50: has_tests is always False in practice.

RepoAnalyzer._detect_tests() correctly checks repo_data["file_structure"]
for test indicators, but GitHubTool._fetch_repo_metadata() never populates
file_structure — so has_tests silently always evaluates to False,
regardless of whether the repo actually has tests.
"""

import json

from agent.tools.repo_analyzer import RepoAnalyzer

analyzer = RepoAnalyzer()

# Simulates a repo that DOES have tests, when file_structure is known
with_structure = analyzer.parse(
    json.dumps({"name": "example-repo", "file_structure": "tests/test_foo.py"})
)
print("With file_structure provided:", with_structure.metadata["has_tests"])  # True

# Simulates what github_tool.py actually produces today (no file_structure key)
without_structure = analyzer.parse(json.dumps({"name": "example-repo"}))
print(
    "Without file_structure (real pipeline behavior):", without_structure.metadata["has_tests"]
)  # False, even if repo has tests
