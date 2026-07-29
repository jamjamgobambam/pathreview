## Solution plan

**Issue:** [Add inline docstrings to all public methods in core/services module](https://github.com/ascherj/pathreview/issues/119)


### Understand
The public functions within `core/services/profile_service.py` and `core/services/review_service.py` currently lack docstrings. To resolve this, each public function needs to be updated to comprehensively document its arguments, return values, and any raised exceptions. These documentation updates must be made without altering the existing runtime behavior.

### Map

Involved Files:
- `core/services/profile_service.py`
- `core/services/review_service.py`
- `JOURNAL.md`
- `PLAN.md`

### Plan
1. Locate all public functions within the two specified service modules.
2. Cross-reference the existing docstrings with each function's actual signature and underlying logic.
3. Implement uniform Google-style formatting for the `Args:` and `Returns:` blocks.
4. Include a `Raises:` block exclusively for exceptions that are explicitly raised or passed through.
5. Execute all relevant formatters, type-checkers (e.g., mypy), and test suites.
6. Audit the resulting diff to guarantee zero modifications to runtime functionality.

### Inputs & outputs
**Inputs:** 

- public function signatures
- their return types
- how they handle exceptions. 

**Output:** standardized  docstrings applied to eight public service functions, ensuring absolutely no changes to the application's runtime behavior.

### Risks & unknowns
* A parameter or return value might be inadvertently misrepresented in the new docstrings.
* The conditions under which exceptions are raised could be documented incorrectly.
* Passing mypy may require making minor, strictly necessary adjustments to type annotations in the target files.
* The original issue mentions a service file that currently does not exist in the `upstream/main` branch.

### Edge cases
* Parameters that are optional must be explicitly noted as such in the documentation.
* If a function returns `None` (e.g., when a record is not found), this behavior must be clearly stated.
* Do not list exceptions under `Raises:` unless they are genuinely triggered or propagated.
* Keep all private helper functions strictly out of scope for these documentation updates.
