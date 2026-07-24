## Solution plan

**Issue:** Add a `has_tests` boolean to the repo analysis output  
https://github.com/ascherj/pathreview/issues/50

### Understand

`GitHubTool` returns information about a repository, such as its name, language, stars, and whether it has a README.

The problem is that it does not return a `has_tests` field.

Expected:

```python
"has_tests": True