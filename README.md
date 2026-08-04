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
make audit         # Scan Python + frontend deps for known vulnerabilities
make run           # Start the dev servers
```

### Dependency security scanning

CI runs a `security-scan` job on every pull request and push to `main`. It fails the
build when a **high-severity (or worse)** vulnerability is found in a shipped dependency:

- **Python** — [`pip-audit`](https://pypi.org/project/pip-audit/) over the installed
  environment. Advisories with no patched release upstream are ignored via an explicit,
  commented allowlist (see the `PIP_AUDIT_IGNORE` variable in the [`Makefile`](Makefile)).
- **Frontend** — `npm audit --omit=dev --audit-level=high` over production dependencies.
  Dev-tooling advisories (build/test chain) are reported in a separate, non-blocking step.

Run the same checks locally with `make audit` before opening a PR.

## License

MIT
