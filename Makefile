.PHONY: setup run test-unit test-integration test-all lint format typecheck check migrate seed reset-db eval clean

SHELL := /bin/bash
PYTHON := .venv/bin/python
PIP := .venv/bin/pip
PYTEST := .venv/bin/pytest

# ---- Setup ----

setup: ## First-time setup: venv, deps, migrations, seed data
	python -m venv .venv
	$(PIP) install -e ".[dev]"
	.venv/bin/pre-commit install
	$(PYTHON) -m alembic upgrade head
	$(PYTHON) scripts/seed_db.py
	cd frontend && npm install
	@echo ""
	@echo "Setup complete. Run 'make run' to start the application."

# ---- Run ----

run: ## Start backend + frontend dev servers
	@trap 'kill %1 %2 2>/dev/null' EXIT; \
	source .venv/bin/activate && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 & \
	cd frontend && npm run dev &; \
	wait

# ---- Tests ----

test-unit: ## Run unit tests only (~30 seconds)
	$(PYTEST) tests/unit -v -m unit

test-integration: ## Run integration tests only
	$(PYTEST) tests/integration -v -m integration

test-all: ## Run full test suite
	$(PYTEST) tests/ -v

# ---- Code Quality ----

lint: ## Run ruff linter
	.venv/bin/ruff check .

format: ## Run black formatter
	.venv/bin/black .

typecheck: ## Run mypy type checker
	.venv/bin/mypy pathreview/ api/ core/ ingestion/ rag/ agent/ safety/

check: lint format typecheck ## Run lint + format + typecheck

# ---- Database ----

migrate: ## Run pending database migrations
	$(PYTHON) -m alembic upgrade head

seed: ## Re-seed the database with sample data
	$(PYTHON) scripts/seed_db.py

reset-db: ## Drop and recreate the development database
	docker compose exec db psql -U pathreview -c "DROP DATABASE IF EXISTS pathreview_dev;"
	docker compose exec db psql -U pathreview -c "CREATE DATABASE pathreview_dev;"
	$(PYTHON) -m alembic upgrade head
	$(PYTHON) scripts/seed_db.py

# ---- Evaluation ----

eval: ## Run the RAG evaluation suite
	$(PYTHON) scripts/run_evals.py

# ---- Cleanup ----

clean: ## Remove build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage dist build *.egg-info

# ---- Help ----

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
