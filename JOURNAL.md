# Journal

## 2026-07-21 — Environment setup

Completed local dev environment setup per `docs/SETUP.md`:

- Cloned fork, added `upstream` remote pointing to `ascherj/pathreview`
- `docker compose up -d` — `db` and `redis` healthy. Note: `vector-db` (chromadb 0.4.22) fails to start due to a NumPy 2.0 incompatibility (`np.float_` removed) in that pinned image; not a blocker since `rag/retriever/vector_store.py` uses an embedded local ChromaDB client rather than the Docker service.
- `make setup` — venv, deps, migrations, and seed data all completed successfully
- `make run` — confirmed app loads at `http://localhost:5173` (login page) with API docs at `http://localhost:8000/docs`

Working on issue [#69](https://github.com/ascherj/pathreview/issues/69): add a feedback tone check so generated review feedback is classified as constructive vs. discouraging, with rejection/regeneration for sections that fail the check. Relevant files: `safety/content_filter.py`, `rag/generator/review_generator.py`.
