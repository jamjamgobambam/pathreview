## Week 8: Reproduction & solution planning

**Reproduction commit link:** []

**Reproduction summary:**
To confirm the bug, I temporarily reverted the fix in `api/routes/health.py`,
changing `await db.execute(text("SELECT 1"))` back to the original
`await db.execute("SELECT 1")`. After restarting the server, calling
`GET /health` returned `"postgres":"unhealthy"` in the response, and the
server logs showed the exact error from the issue:

```javascript
error="Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')"
```

This confirmed the root cause. I then restored the `text()` wrapper and
re-verified that `"postgres":"healthy"` returns correctly.

**PLAN.md link:** https://github.com/Kelllyy1/pathreview/blob/fix/154-health-check-raw-sql/PLAN.md

**Walkthrough video (recommended):** (skipped for now)

**Blockers or open questions:**
None. The fix is already implemented and verified; remaining work for
Week 9 is polishing tests and the PR description.

To run the program again call:
    - docker compose up -d
    - docker compose ps
    - make run