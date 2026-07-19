# Module 3 Journal

> Weekly engineering journal for my work on **PathReview**.
> Fork: https://github.com/arunkasala-open/pathreview

---

## Week 7 — Environment Setup & Issue Selection

**Dates:** 2026-07-19

### Issue I'm working on
- **Issue #28 — Generator produces duplicate feedback sections when a user has multiple projects in the same tech stack** (`fix`, labels: `tier-3`, `rag`)
- Branch: `fix/28-duplicate-feedback-sections-when-multiple-projects`
- Summary: When a user has several projects in the same stack (e.g. three Python projects), the review generator emits nearly identical skills feedback for each one, so the review reads as repetitive. The fix is to deduplicate and consolidate cross-project observations in the generator.
- Relevant files: `rag/generator/review_generator.py`, `rag/generator/output_parser.py`

### What I did this week
- Forked the repo and set up the local development environment per `docs/SETUP.md`.
- Configured `.env`, including the OpenRouter LLM settings.
- Brought up the backing services with Docker Compose (PostgreSQL, Redis, ChromaDB).
- Ran first-time setup: created the Python virtual environment, installed backend + dev dependencies, installed pre-commit hooks, applied database migrations, and seeded the sample data.
- Installed the frontend dependencies.
- Read `docs/CONTRIBUTING.md` and created my working branch following the naming convention.

### Environment setup notes / issues I had to fix
- **Python version:** `make setup` was creating the virtualenv with Python 3.8, but the project requires `>=3.11`. On 3.8, pip could only install an older setuptools, which rejected the modern `license = "MIT"` field in `pyproject.toml` and broke the editable install. Rebuilt the venv with Python 3.12.
- **ChromaDB:** the pinned `chromadb/chroma:0.4.22` image crash-looped against NumPy 2.0 (`np.float_` removed). Bumped the image to a NumPy-2-compatible release so `docker compose up` reports all services healthy.
- **Node.js:** Node/npm were not installed, so the frontend install step failed until I installed Node.

### Blockers
- None currently blocking. The LLM review path (`_run_rag_retrieval_generation`) is still a placeholder in `core/services/review_service.py`, which is relevant context for the duplicate-feedback work.

### Next steps
- Reproduce the duplicate-feedback behavior with a profile that has multiple same-stack projects.
- Implement real consolidation in `review_generator.py` (the current `_consolidate_feedback` only dedupes by section name, not by content).
- Add unit tests covering the multi-project deduplication case.
