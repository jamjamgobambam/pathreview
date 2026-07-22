# Issue #119 reproduction

**Issue:** [Add inline docstrings to all public methods in `core/services/`](https://github.com/ascherj/pathreview/issues/119)

**Reproduced:** 2026-07-21 on branch `docs/119-add-service-docstrings`

## Gap reproduced

The repository requires Google-style docstrings for public functions, and issue #119 specifically calls for descriptions plus `Args`, `Returns`, and `Raises` sections in `core/services/`. The existing service functions have short descriptive text, but none of the eight public functions contains any of those three sections.

Run this audit from the repository root:

```bash
.venv/bin/python - <<'PY'
import ast
from pathlib import Path

required = ("Args:", "Returns:", "Raises:")
failures = 0

for path in sorted(Path("core/services").glob("*.py")):
    tree = ast.parse(path.read_text())
    for node in tree.body:
        is_public_function = isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) and not node.name.startswith("_")
        if not is_public_function:
            continue

        docstring = ast.get_docstring(node) or ""
        missing = [section for section in required if section not in docstring]
        status = "PASS" if not missing else "FAIL missing " + ", ".join(missing)
        print(f"{path}:{node.lineno} {node.name}: {status}")
        failures += bool(missing)

print(f"public_functions=8 failures={failures}")
raise SystemExit(bool(failures))
PY
```

Observed output:

```text
core/services/profile_service.py:13 create_profile: FAIL missing Args:, Returns:, Raises:
core/services/profile_service.py:36 get_profile: FAIL missing Args:, Returns:, Raises:
core/services/profile_service.py:51 update_profile: FAIL missing Args:, Returns:, Raises:
core/services/profile_service.py:75 delete_profile: FAIL missing Args:, Returns:, Raises:
core/services/review_service.py:15 create_review: FAIL missing Args:, Returns:, Raises:
core/services/review_service.py:35 get_review: FAIL missing Args:, Returns:, Raises:
core/services/review_service.py:50 list_reviews: FAIL missing Args:, Returns:, Raises:
core/services/review_service.py:82 process_review: FAIL missing Args:, Returns:, Raises:
public_functions=8 failures=8
```

The command exits with status 1, reproducing the documentation gap without changing application behavior.

## Scope finding

The issue also names `core/services/notification_service.py`, but that file does not exist in this checkout. The current implementation scope is therefore the four public functions in `profile_service.py` and the four public functions in `review_service.py`; private helpers beginning with `_` are outside the stated public-method scope.
