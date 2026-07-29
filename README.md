# PathReview

**AI-powered portfolio review assistant** that helps early-career developers strengthen their professional portfolios.

PathReview analyzes GitHub profiles, resumes, and project repositories to generate structured, actionable feedback on portfolio completeness, project quality, skill gaps, and presentation improvements.

---

## Table of Contents

- [The Problem](#the-problem)
- [Who It's For](#who-its-for)
- [Features](#features)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## The Problem

Early-career developers often struggle to get meaningful, specific feedback on their portfolios before job applications. Generic advice like "add more projects" or "improve your README" doesn't tell you _what_ is actually weak or _how_ to fix it relative to what employers currently look for.

PathReview solves this by treating your portfolio — resume, GitHub profile, and project repos — as a corpus of evidence, then applying AI-driven analysis to produce structured, citation-backed feedback. Instead of vague suggestions, you get targeted notes like: _"Your `data-pipeline` project's README is missing a usage section, which is present in 80% of similarly-scoped projects in your target domain."_

## Who It's For

- **Bootcamp graduates and self-taught developers** preparing for their first technical role
- **CS students** wanting to benchmark their portfolio before internship or new-grad applications
- **Career changers** who need to reframe experience from a prior field into software engineering terms
- **Mentors and coaches** who want a repeatable, structured framework for portfolio reviews

---

## Features

### Profile Ingestion
Upload a resume (PDF or Markdown), connect a GitHub username, and link one or more project repositories. PathReview parses each document, extracts structured information (skills, job titles, project descriptions), and stores it as searchable embeddings. Supported parsers: PDF resume, Markdown resume, GitHub profile, repository README.

### RAG-Powered Feedback
Retrieval-Augmented Generation (RAG) grounds every piece of feedback in your actual uploaded content. When the system says your resume undersells a skill, it points to the exact section it pulled from. Hybrid retrieval (vector similarity + BM25 keyword search) ensures both semantic and exact matches are considered.

### Multi-Tool Agent
A plan-and-execute AI agent orchestrates five specialized analysis tools:

| Tool | What it does |
|---|---|
| GitHub Analyzer | Inspects repository activity, language mix, and contribution history |
| Skill Extractor | Identifies technical skills mentioned in resume and repos |
| README Scorer | Rates project READMEs against completeness criteria |
| Market Comparator | Benchmarks skills against current job posting data |
| Tech Detector | Detects frameworks and tooling from code and config files |

### Safety Guardrails
All AI-generated feedback passes through a four-stage safety pipeline before delivery: prompt injection defense → content filter → bias detector → PII scrubber. Safety events are logged with structured metadata for monitoring and audit. This ensures feedback is constructive, unbiased, and free of inadvertently included personal data.

### Web Dashboard
A React + TypeScript single-page application lets you submit your profile, track review status in real time, read structured feedback organized by category, and export a shareable review summary. Review history is persisted so you can compare feedback across iterations.

---

## How It Works

```
1. You submit your GitHub username, upload a resume, and optionally link repos
         │
         ▼
2. Ingestion Pipeline parses each document, chunks it, and stores embeddings
         │
         ▼
3. Agent Orchestrator builds an analysis plan and runs the five tools in parallel
         │
         ▼
4. RAG System retrieves the most relevant chunks and generates structured feedback
         │
         ▼
5. Safety Layer filters the output for bias, PII, and harmful content
         │
         ▼
6. Your review appears on the dashboard with section-by-section citations
```

A full technical walkthrough of each step is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

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

For the full data-flow diagram and subsystem design notes, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Key architectural decisions (chunking strategy, embedding model selection, agent orchestration approach) are documented in [docs/adr/](docs/adr/).

---

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

---

## Development

```bash
make help          # Show all available commands
make test-unit     # Run unit tests (~30 seconds)
make check         # Run linter + formatter + type checker
make run           # Start the dev servers
```

Test credentials seeded by `make setup`:

| Email | Password |
|---|---|
| user1@example.com | password1 |
| user2@example.com | password2 |
| user3@example.com | password3 |

---

## Contributing

We welcome contributions! Please read [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) before submitting a pull request. Browse open issues at the [issue tracker](https://github.com/jamjamgobambam/pathreview/issues) — issues labeled `tier-1` are good starting points for first-time contributors.

## License

MIT
