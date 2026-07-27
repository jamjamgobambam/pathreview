"""
Manual reproduction script for issue #86:
"API clients have no way to know how many requests they have left before
hitting the rate limit until they receive a 429."

This is not part of the automated test suite (no pytest marker, not
collected by CI) -- it's a standalone script documenting how the bug was
reproduced locally.

How to reproduce against `main` (before the fix in this branch):

    git worktree add /tmp/pathreview-main main
    cp tests/manual/repro_issue_86.py /tmp/pathreview-main/
    cd /tmp/pathreview-main
    PYTHONPATH=. <path-to-venv>/bin/python repro_issue_86.py

Observed on `main`: every response's X-RateLimit-Limit and
X-RateLimit-Remaining headers are None, and no request is ever blocked with
a 429, no matter how many are sent -- because `RateLimiter.check_rate_limit`
(safety/rate_limiter.py) is fully implemented and unit-tested but is never
called anywhere in the API layer (no middleware, no route dependency wires
it up).

Run against this branch (after the fix) to confirm resolution: the same
script reports X-RateLimit-Limit / X-RateLimit-Remaining on every response.
"""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

print("Sending 5 requests to GET / (no DB/Redis dependency needed for this route)...\n")

for i in range(1, 6):
    response = client.get("/")
    rl_limit = response.headers.get("X-RateLimit-Limit")
    rl_remaining = response.headers.get("X-RateLimit-Remaining")
    print(
        f"request {i}: status={response.status_code} "
        f"X-RateLimit-Limit={rl_limit!r} X-RateLimit-Remaining={rl_remaining!r}"
    )
