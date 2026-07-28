## Solution plan

**Issue:** [Add inline docstrings to all public methods in `core/services/`](https://github.com/ascherj/pathreview/issues/119)

### Understand

The public functions in `core/services/profile_service.py` and
`core/services/review_service.py` have incomplete or inconsistent docstrings.
The expected behavior is for each public function to consistently document its
arguments, return value, and raised exceptions where applicable without changing
runtime behavior.

### Map

Files involved:

- `core/services/profile_service.py`
- `core/services/review_service.py`
- `JOURNAL.md`
- `PLAN.md`

The issue also references `core/services/notification_service.py`, but that file
does not exist on the latest `upstream/main`.

### Plan

1. Identify every public function in the two existing service modules.
2. Compare each function signature and implementation with its current docstring.
3. Add consistent Google-style `Args:` and `Returns:` sections.
4. Add `Raises:` only when an exception is actually raised or propagated.
5. Run formatting, type-checking, and applicable repository tests.
6. Review the final diff to ensure application behavior is unchanged.

### Inputs & outputs

The inputs are the existing public function signatures, return types, and exception
behavior. The output is clearer Google-style documentation for eight public service
functions, with no intended runtime behavior changes.

### Risks & unknowns

- A docstring could incorrectly describe a parameter or return value.
- Exception behavior could be documented inaccurately.
- Repository checks may expose pre-existing lint or test failures unrelated to the issue.
- Minimal type-annotation changes may be necessary for the modified files to pass mypy.
- The issue references a service file that is absent from `upstream/main`.

### Edge cases

- Optional parameters should be documented as optional.
- Functions returning `None` when no record is found should state that behavior.
- Only exceptions actually raised or propagated should appear under `Raises:`.
- Private helper functions should remain outside the issue’s documentation scope.
- The missing `notification_service.py` should not be created solely to match the issue description.
