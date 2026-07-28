.PHONY: setup run services test-unit test-integration test-all lint format typecheck check migrate seed reset-db eval clean

SHELL := /bin/bash

# Detect Windows (Git Bash) vs Unix
ifeq ($(OS),Windows_NT)
  VENV_BIN := .venv/Scripts
else
  VENV_BIN := .venv/bin
endif

PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
PYTEST := $(VENV_BIN)/pytest

# ---- Setup ----

setup: services ## First-time setup: venv, deps, migrations, seed data
	python -m venv .venv || python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PIP) install -e ".[dev]"
	$(VENV_BIN)/pre-commit install
	$(VENV_BIN)/alembic upgrade head
	$(PYTHON) scripts/seed_db.py
	cd frontend && npm install
	@echo ""
	@echo "Setup complete. Run 'make run' to start the application."

# ---- Services (container engine) ----

services: ## Start the Colima engine + Docker Compose services (idempotent)
	@command -v colima >/dev/null 2>&1 || { echo "colima not found. Install it with: brew install colima" >&2; exit 1; }
	@colima status >/dev/null 2>&1 || colima start
	@docker compose up -d
	@printf "Waiting for Postgres to be ready"
	@for i in $$(seq 1 30); do \
		if docker compose exec -T db pg_isready -U pathreview >/dev/null 2>&1; then \
			echo " ready."; exit 0; \
		fi; \
		printf "."; sleep 1; \
	done; \
	echo " timed out waiting for Postgres" >&2; exit 1

# ---- Run ----

run: services ## Start backend + frontend dev servers
	@trap 'kill %1 %2 2>/dev/null' EXIT; \
	source $(VENV_BIN)/activate && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 & \
	cd frontend && npm run dev & \
	wait

# ---- Tests ----

test-unit: ## Run unit tests only (~30 seconds)
	$(PYTEST) tests/unit -v -m unit

test-integration: services ## Run integration tests only
	$(PYTEST) tests/integration -v -m integration

test-all: services ## Run full test suite
	$(PYTEST) tests/ -v

# ---- Code Quality ----

lint: ## Run ruff linter
	$(VENV_BIN)/ruff check .

format: ## Run black formatter
	$(VENV_BIN)/black .

typecheck: ## Run mypy type checker
	$(VENV_BIN)/mypy api/ core/ ingestion/ rag/ agent/ safety/

check: lint format typecheck ## Run lint + format + typecheck

# ---- Database ----

migrate: services ## Run pending database migrations
	$(VENV_BIN)/alembic upgrade head

seed: services ## Re-seed the database with sample data
	$(PYTHON) scripts/seed_db.py

reset-db: services ## Drop and recreate the development database
	docker compose exec db psql -U pathreview -d postgres -c "DROP DATABASE IF EXISTS pathreview_dev;"
	docker compose exec db psql -U pathreview -d postgres -c "CREATE DATABASE pathreview_dev;"
	$(VENV_BIN)/alembic upgrade head
	$(PYTHON) scripts/seed_db.py

# ---- Evaluation ----

eval: services ## Run the RAG evaluation suite
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
