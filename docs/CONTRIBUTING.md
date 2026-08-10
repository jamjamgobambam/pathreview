# Contributing to PathReview

Thank you for contributing to PathReview! This guide explains our development workflow and standards.

## Getting Started

1. **Fork** the repository and clone your fork
2. **Set up** your development environment following [SETUP.md](SETUP.md)
3. **Browse issues** and find one that interests you
4. **Comment** on the issue to let others know you're working on it

## Branch Naming Convention

Create a branch from `main` using this format:

```
<type>/<issue-number>-<short-description>
```

Where `<issue-number>` is the GitHub issue number (the number shown under the issue title in the tracker — e.g., `#124`).

Examples:
- `fix/124-resume-parser-index-error`
- `feat/128-first-impression-prompt`
- `test/115-readme-scorer-unit-tests`
- `docs/110-update-setup-guide`

Types: `fix`, `feat`, `test`, `docs`, `refactor`, `perf`, `chore`

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/). Every commit message must follow this format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:** `fix`, `feat`, `test`, `docs`, `refactor`, `perf`, `chore`, `ci`

**Scopes:** `ingestion`, `rag`, `agent`, `safety`, `api`, `frontend`

**Examples:**
```
fix(ingestion): handle missing experience section in resume parser

Resume parser crashed with IndexError when a resume had no work experience
section. Added a bounds check before accessing sections['experience'][0].

Fixes #42
```

```
test(agent): add unit tests for readme_scorer tool
```

## Pull Request Process

1. **Ensure your code passes all checks:** `make check && make test-unit`
2. **Push your branch** and open a PR using the PR template
3. **Fill out the PR template completely** — incomplete PRs will be sent back
4. **Respond to review feedback** within 48 hours
5. **Squash fixup commits** before final merge if requested

## Code Style

- **Python:** Formatted with `black`, linted with `ruff`, type-checked with `mypy`
- **TypeScript/React:** Follows the existing component patterns in `frontend/src/`
- **Tests:** Every code change should include or update relevant tests
- **Docstrings:** All public functions and classes must have Google-style docstrings

## Running Checks Locally

```bash
make lint       # Ruff linter
make format     # Black formatter
make typecheck  # Mypy type checker
make check      # All three
make test-unit  # Unit tests
```

## Adding a New Parser

If your issue involves adding a new document parser to the ingestion pipeline:

1. Create a new file in `ingestion/parsers/` (e.g., `web_parser.py`)
2. Implement the `BaseParser` interface:
   ```python
   from ingestion.parsers.base import BaseParser, ParseResult

   class WebParser(BaseParser):
       def parse(self, content: str | bytes) -> ParseResult:
           ...
   ```
3. Register the parser in `ingestion/pipeline.py`
4. Add unit tests in `tests/unit/test_<parser_name>.py`
5. Add a sample fixture in `tests/fixtures/` if needed

## Adding a New Agent Tool

If your issue involves adding a new tool to the agent system:

1. Create a new file in `agent/tools/` (e.g., `dependency_audit_tool.py`)
2. Implement the `BaseTool` interface:
   ```python
   from agent.tools.base import BaseTool, ToolResult

   class DependencyAuditTool(BaseTool):
       name = "dependency_audit"
       description = "Checks for outdated dependencies in project repos"

       def execute(self, input_data: dict) -> ToolResult:
           ...
   ```
3. Register the tool in `agent/orchestrator.py`
4. Add unit tests in `tests/unit/test_<tool_name>.py`
5. Add mock responses in `tests/fixtures/` if the tool calls external APIs

## Questions?

Open a discussion or reach out in the course Discord channel.
