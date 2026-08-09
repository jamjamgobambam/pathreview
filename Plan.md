## Solution plan

**Issue:** [E-12] Webhook Notifier System Schema Mismatch and Test Failures

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

**Root Causes:**
1. **Pydantic vs. DB Type Mismatch (`events` field):** In `api/schemas/webhook.py`, `WebhookCreate` and `WebhookResponse` define `events` as `list[str]`. However, `core/models/webhook.py` stores `events` in the database as a comma-separated string (`str`). When `WebhookResponse.model_validate(webhook)` is called on an ORM instance, Pydantic fails validation because it receives a `str` instead of `list[str]`. Furthermore, `tests/unit/test_webhooks.py` passes `str` to schema constructors.
2. **Service Layer Normalization:** `core/services/webhook_service.py` receives `events` parameters which may be passed as either `list[str]` or `str`, requiring explicit string normalization before writing to SQLAlchemy models.
3. **Async Test Execution Warning:** `pyproject.toml` lacks `asyncio_mode = "auto"` under `[tool.pytest.ini_options]`, causing pytest to emit `PytestUnhandledCoroutineWarning` and ignore `async def` test functions.

**Expected vs. Actual Behavior:**
* *Expected:* API clients can submit `events` as a list (`["review.completed"]`) or a comma-separated string (`"review.completed,review.failed"`). Schemas, services, and ORM models seamlessly convert between API representations (`list[str]`) and database storage (`str`). All unit and integration tests run asynchronously and pass cleanly.
* *Actual:* 3 tests fail in `tests/unit/test_webhooks.py` with `pydantic_core.ValidationError` and unhandled coroutine warnings.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- [api/schemas/webhook.py](file:///C:/Users/Erold%20Rayan/Downloads/AI201-Summer%20Program/Module%203/Week%207/pathreview/api/schemas/webhook.py): Add `@field_validator` to `WebhookCreate`, `WebhookUpdate`, and `WebhookResponse` to parse and serialize `events` dynamically between `str` and `list[str]`.
- [core/services/webhook_service.py](file:///C:/Users/Erold%20Rayan/Downloads/AI201-Summer%20Program/Module%203/Week%207/pathreview/core/services/webhook_service.py): Ensure `create_webhook` and `update_webhook` normalize `events` to a comma-separated string if a list is provided.
- [tests/unit/test_webhooks.py](file:///C:/Users/Erold%20Rayan/Downloads/AI201-Summer%20Program/Module%203/Week%207/pathreview/tests/unit/test_webhooks.py): Fix schema instantiation in tests, add tests for both list and string inputs, and complete async test assertions.
- [pyproject.toml](file:///C:/Users/Erold%20Rayan/Downloads/AI201-Summer%20Program/Module%203/Week%207/pathreview/pyproject.toml): Add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]`.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. **Configure Pytest Asyncio:** Update `pyproject.toml` to set `asyncio_mode = "auto"` so `async def` tests execute properly without warnings.
2. **Enhance Pydantic Schemas:** In `api/schemas/webhook.py`, implement field validators for `events` on `WebhookCreate`, `WebhookUpdate`, and `WebhookResponse` to handle both `list[str]` and comma-separated `str` inputs/ORM attributes smoothly.
3. **Normalize Service Layer Storage:** In `core/services/webhook_service.py`, handle both `list[str]` and `str` types for the `events` argument, normalizing them into comma-separated strings before SQLAlchemy model initialization/update.
4. **Update & Run Test Suite:** Update `tests/unit/test_webhooks.py` with test cases for both list and string inputs, ensure all async tests complete cleanly, and run `pytest` to confirm 100% test pass rate across the codebase.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

- **Inputs:**
  - JSON payload with `events` specified as either `list[str]` (`["review.completed", "review.failed"]`) or `str` (`"review.completed,review.failed"`).
  - ORM `Webhook` instances with `events` stored as `str`.
- **Outputs:**
  - Standardized database storing comma-separated strings in `webhooks.events`.
  - JSON API responses returning `events` as `list[str]`.
  - 100% green unit test suite execution (`pytest`).

### Risks & unknowns
What could go wrong? What are you still unsure about?

- Breaking existing callers of `WebhookResponse` if they expected `events` as a `str` instead of `list[str]` or vice-versa. (Mitigated by validator accepting both formats).
- Performance overhead from validator conversion (negligible for small event list strings).

### Edge cases
What inputs or states should your fix handle gracefully?

- `events` provided as a string with extra whitespace around commas (e.g. `"review.completed , review.failed"`).
- `events` provided as a list containing single comma-separated strings or individual items (`["review.completed, review.failed"]`).
- `events` passed as `None` in `WebhookUpdate`.
- Empty lists `[]` or empty strings `""`.