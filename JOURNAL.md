# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/38

**Issue title:** Add an integration test that runs the full RAG pipeline against a mock LLM

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview builds a review by chaining several RAG stages together — retrieving the most
relevant profile chunks, reranking them, sending them to an LLM to generate the review
text, and parsing that text into structured feedback sections. Today each of those stages
is only exercised by its own isolated unit tests, and there is no single test that runs the
stages end-to-end. That gap means a regression at a *seam* between stages — for example a
shape mismatch between what the retriever returns and what the generator expects — could
pass every unit test while silently breaking the real flow. A successful fix adds an
integration test at `tests/integration/test_rag_pipeline.py` that drives a representative
query through the entire retrieval → rerank → generation → parsing path against the
deterministic mock LLM provider and asserts a well-formed review comes out, giving CI a
fast, offline regression guard for the whole pipeline.

**Selection reasoning ("Is this right for me?" checklist):**
- **Tier acknowledged / skill alignment:** This is a **Tier 2** issue (intermediate —
  requires cross-module understanding). That matches my comfort level: I'm comfortable with
  Python and `pytest` and can read across modules, so a test that spans the RAG package is a
  deliberate, appropriate stretch rather than an overreach.
- **Do I understand the issue?** Yes — it asks for one end-to-end test, using the existing
  mock LLM provider so results are deterministic (no live API, no cost).
- **Is the scope realistic?** Yes. The change surface is small and additive — a single new
  test file, **no production-code changes required** — while still touching multiple modules
  to read (`rag/` retriever/reranker/generator/parser, `core/config.py` for the mock
  provider, `tests/` conventions). That "read broadly, write narrowly" shape is exactly the
  Tier-2 intent and keeps risk low. The tracker's 4–6h estimate is realistic for one issue.
- **Blockers / dependencies?** None external — the mock provider means no keys or network.
  During setup I already located the pipeline stages and confirmed the pieces exist to wire
  together, so there are no unknown dependencies.
- **Why not Tier 1 / Tier 3?** Larger than a Tier-1 one-line fix (it requires understanding
  the whole pipeline), but well short of a Tier-3 architectural change (no design decisions,
  no schema/API changes).

**Branch name:** `test/38-rag-pipeline-integration-test`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### Setup evidence (Week 7)

Environment stood up on Windows 11 following `docs/SETUP.md` (Docker services + Python venv
+ frontend). Captured 2026-07-21.

**Backing services healthy (`docker compose ps`):**
```
SERVICE   STATUS                    PORTS
db        Up (healthy)              0.0.0.0:5433->5432/tcp
redis     Up (healthy)              0.0.0.0:6379->6379/tcp
```
(Postgres is mapped to host port **5433** on Windows per SETUP.md, matching `.env`'s
`DATABASE_URL`.)

**Database migrated + seeded:**
```
alembic upgrade head  ->  ran migrations 001, 002 successfully
scripts/seed_db.py    ->  seeded 3 test accounts (user1..3@example.com)
```

**Frontend loads at http://localhost:5173 (the Week 7 requirement):**
```
$ curl -sI http://localhost:5173/
HTTP/1.1 200 OK
Content-Type: text/html

$ curl -s http://localhost:5173/ | grep -o '<title>.*</title>'
<title>PathReview - AI Portfolio Review Assistant</title>

# Vite dev server:  VITE v5.4.21  ready
```

**Backend API responds at http://localhost:8000:**
```
$ curl -s http://localhost:8000/
{"message":"PathReview API is running","version":"1.0.0"}   # HTTP 200

$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs
200                                                          # Swagger UI
```

**Environment observations (pre-existing, not part of issue #38):**
- `GET /health` returns 503 due to two pre-existing bugs in `api/routes/health.py`, *not*
  actual outages (Postgres/Redis are up — migrations and seeding both succeeded against
  them): (1) the Postgres check runs a raw `"SELECT 1"` string instead of
  `sqlalchemy.text("SELECT 1")` (invalid under SQLAlchemy 2.0), and (2) the Redis check
  reads `settings.redis_host`, an attribute that does not exist on the `Settings` model
  (only `redis_url` is defined in `core/config.py`).
- The `chromadb/chroma:0.4.22` container image crashes on boot (`AttributeError: np.float_
  was removed in the NumPy 2.0 release`). Neither issue blocks the app from loading at
  `localhost:5173`, and both are outside the scope of issue #38.
