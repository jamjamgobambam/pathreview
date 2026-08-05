# Development Journal

## 2026-07-18 — Environment setup

- Cloned my fork and configured `upstream` remote.
- Started backing services (PostgreSQL on `:5433`, Redis on `:6379`) via `docker compose up -d`.
- Ran `make setup` (venv, dependencies, migrations, seed data) and `npm install` in `frontend/`.
- Verified the app runs: backend API on http://localhost:8000, frontend (Vite) on http://localhost:5173.
- Confirmed the seeded test accounts work for login.

Environment is up and running.

## Issue #34 — LLM re-ranking step (feat, rag, tier-3)

**Goal:** Add an optional re-ranking pass that prompts a smaller LLM to score each
retrieved chunk's relevance to the query, before passing the top-k to the generator.
The current retriever ranks with vector + keyword scores only.

**Relevant files:**
- `rag/retriever/reranker.py` (new)
- `rag/retriever/hybrid.py`

**Plan (initial):**
- [ ] Read `rag/retriever/hybrid.py` to understand the current ranking flow and top-k output.
- [ ] Add a `reranker.py` with an LLM-backed relevance scorer over retrieved chunks.
- [ ] Make re-ranking opt-in (config flag) so the existing path is unchanged by default.
- [ ] Wire the re-ranking pass into the hybrid retriever before generation.
- [ ] Add unit tests with mocked LLM responses.
