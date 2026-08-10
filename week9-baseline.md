# Week 9 Baseline — `make check` and `make test-unit`

Captured on `fix/151-bias-detector-patterns` **before** implementing the fix for issue #151, so I can prove my change introduces no new failures (per the Week 9 "Pre-existing failures" guidance).

## `make check` — FAILED (`ruff` exit 1)

- **181 lint errors total**, 85 auto-fixable with `ruff --fix`.
- These span the whole codebase (`agent/`, `tests/unit/`, etc.) — unsorted imports (`I001`), unused imports (`F401`), unused locals (`F841`), `Optional` vs `X | None` (`UP045`), naming (`N806`), and one undefined name (`F821` in `test_skill_extractor.py`).
- **None are in `safety/bias_detector.py`.** All pre-existing and unrelated to issue #151.

## `make test-unit` — FAILED (interrupted, exit 2)

- Collection is interrupted by **2 errors** before any test runs.
- Cause: `core/config.py` builds a `Settings` model that forbids extra env vars, but `.env` supplies `gemini_api_key` and `groq_api_key`, which aren't declared fields → `pydantic ValidationError` at import time.
- Affected files: `tests/unit/test_review_service.py`, `tests/unit/test_security.py` (both transitively import `core.config`).
- **Pre-existing and unrelated to issue #151.** Because collection is interrupted, the full `make test-unit` run cannot complete regardless of my change.

## Bias detector tests in isolation — 9 failed, 23 passed

`.venv/bin/pytest tests/unit/test_bias_detector.py` runs fine on its own (it does not import `core.config`). The 9 failures are exactly the ones issue #151 is about:

1. `test_dismissive_bootcamp_language_detected`
2. `test_bootcamp_lacks_rigor_detected`
3. `test_demographic_assumption_age_detected`
4. `test_coding_bootcamp_variant`
5. `test_developer_vs_programmer_distinction`
6. `test_multiple_bias_indicators`
7. `test_negative_educational_claim`
8. `test_rich_poor_assumption`
9. `test_assumption_vs_observation`

## What "passes" means for my PR

My fix targets only `safety/bias_detector.py`. Success criteria:
- These 9 bias tests flip to passing (32/32 in that file).
- The 181 `make check` errors and the 2 `make test-unit` collection errors are unchanged — I introduce no new ones.
