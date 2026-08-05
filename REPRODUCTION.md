# Issue #158 reproduction

## Command

```bash
./.venv/Scripts/python.exe -m pytest tests/unit/test_review_service.py -q
```

## Result

The test run completed with 13 failed tests and 6 passed tests.

The failures occur because the tests configure SQLAlchemy result objects as `AsyncMock`. The production service correctly awaits `db.execute()`, but methods on the returned result—such as `scalars()`, `first()`, and `all()`—are synchronous. The incorrect mocks therefore return coroutine objects, producing errors including:

- `AttributeError: 'coroutine' object has no attribute 'first'`
- `AttributeError: 'coroutine' object has no attribute 'all'`

This reliably reproduces the behavior described in issue #158.
