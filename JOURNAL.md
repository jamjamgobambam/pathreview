# Development Journal — Module 3

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/111

**Issue title:** No property-based tests for the PII scrubber

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The `PIIScrubber` in `safety/pii_scrubber.py` strips personal data (emails,
US/international phone numbers, SSNs, and street addresses) out of text by
running a set of regexes and replacing matches with `[REDACTED]`. Today it is
only covered by example-based tests in `tests/unit/test_pii_scrubber.py` — a
fixed list of hand-picked strings — so any PII format the author didn't happen
to think of can slip through untested. The missing piece is *property-based*
testing: using `hypothesis` to generate large numbers of randomized but valid
PII values and assert an invariant (the raw value never survives in the
scrubber's output). A successful fix adds `hypothesis` strategies for each PII
type plus round-trip properties that catch regex gaps (e.g. unusual but valid
emails, spacing/punctuation variants in phone numbers) which the current fixed
examples miss.

**Branch name:** test/111-pii-scrubber-property-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger  *(action item — record #111 in the cohort ledger)*

### "Is this right for me?" — scope reasoning

- **Scope fits the tier.** Tier 2, estimated 4–6 hours. It's additive test work in
  one file against a small, well-defined public API (`PIIScrubber.scrub` /
  `.detect`) — no schema, API, or frontend changes required.
- **Clear, verifiable definition of done.** "Generated PII is always removed" is a
  concrete invariant, so success is objectively checkable via `make test-unit`.
- **Tooling already in place.** `hypothesis` is already a dev dependency
  (`pyproject.toml`), and the existing example tests give a working template.
- **Bounded blast radius.** Adding tests can't regress production behavior; the
  worst case is that new properties surface real regex gaps in the scrubber,
  which is exactly the value the issue is asking for.

---

## Setup notes (Week 7)

Bootstrapped and verified the local environment before starting.

**Verified working:**
- `docker compose up -d` → `db`, `redis`, `vector-db` all healthy
- `make setup` → venv on Python 3.13.11, deps installed, Alembic at head (`002`), DB seeded
- `make run` → backend on :8000, frontend on **:5173** (returns 200)

**Setup fixes committed on this branch:**
- `Makefile` — bootstrap the venv with an auto-detected Python ≥3.11
  (`python3.13/3.12/3.11`) instead of the hardcoded system `python`, which was
  3.9 and failed the `requires-python >= 3.11` constraint.
- `docker-compose.yml` — bumped `chromadb/chroma` `0.4.22` → `0.5.23`; `0.4.22`
  crashes on startup under NumPy 2.0 (`np.float_` was removed).

**Follow-up noted:** `GET /health` returns 503 due to two pre-existing bugs in
`api/routes/health.py` (raw `SELECT 1` needs `text()` for SQLAlchemy 2.0; the
redis check reads a nonexistent `settings.redis_host`/`redis_port`). The
containers themselves are reachable.
