# PathReview

**AI-powered portfolio review assistant** that helps early-career developers strengthen their professional portfolios.

PathReview analyzes GitHub profiles, resumes, and project repositories to generate structured, actionable feedback on portfolio completeness, project quality, skill gaps, and presentation improvements.

## Features

- **Profile Ingestion** — Upload a resume (PDF or Markdown), connect a GitHub profile, and link project repositories
- **RAG-Powered Feedback** — Retrieval-augmented generation produces specific, evidence-based feedback referencing your actual work
- **Multi-Tool Agent** — An AI agent orchestrates GitHub analysis, skill extraction, README scoring, and market comparison
- **Safety Guardrails** — Bias detection, content filtering, PII scrubbing, and prompt injection defense ensure feedback is constructive and safe
- **Web Dashboard** — View results, track improvement over time, and export shareable review summaries

## Quick Start

> **Windows users:** Use [Git Bash](https://git-scm.com/download/win) to run these commands, not PowerShell. See [docs/SETUP.md](docs/SETUP.md) for Windows-specific setup including installing `make`.

```bash
# Clone and enter the repo
git clone https://github.com/ascherj/pathreview.git
cd pathreview

# Configure environment (add your OPENROUTER_API_KEY to .env)
cp .env.example .env

# Start backing services — must be running before make setup
docker compose up -d

# Run first-time setup (installs deps, runs migrations, seeds DB, installs frontend)
make setup

# Start the application
make run
```

Then open http://localhost:5173 in your browser.

For detailed setup instructions including platform-specific notes, see [docs/SETUP.md](docs/SETUP.md).

## Architecture

PathReview is structured as a multi-service Python + React application with five major subsystems:

| Subsystem | Directory | Description |
|---|---|---|
| API Layer | `api/` | FastAPI REST API with authentication, validation, and rate limiting |
| Ingestion Pipeline | `ingestion/` | Document parsing, chunking, and embedding generation |
| RAG System | `rag/` | Hybrid retrieval, LLM-based review generation, and quality evaluation |
| Agent System | `agent/` | Multi-tool orchestration with planning, state management, and error handling |
| Safety Layer | `safety/` | Content filtering, bias detection, PII scrubbing, and prompt defense |
| Frontend | `frontend/` | React + TypeScript dashboard with Vite |

For a detailed architecture overview, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Contributing

We welcome contributions! Please read [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) before submitting a pull request.

## Development

```bash
make help          # Show all available commands
make test-unit     # Run unit tests (~30 seconds)
make check         # Run linter + formatter + type checker
make run           # Start the dev servers
```

## License

MIT

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, portfolio review results are only accessible to authenticated users who own the review through the private `/reviews/{review_id}` API endpoint. There is no way for users to share their review summaries with others (colleagues, mentors, potential employers) without granting full account access. The issue requires implementing a public review sharing feature by: (1) adding a unique public share token to the Review model, (2) creating a new public API endpoint to fetch review summaries by share token, and (3) adding a "Copy link" button in the ReviewPage component (frontend) that generates and copies a shareable public URL. This affects the Review model in `core/models/review.py`, review service in `core/services/review_service.py`, API routes in `api/routes/reviews.py`, and the ReviewPage component in `frontend/src/pages/ReviewPage.tsx`.

**Branch name:** feat/101-public-review-sharing

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger