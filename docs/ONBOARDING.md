# Contributor Onboarding Guide

This guide walks you through the complete lifecycle of a contribution: from forking the repo to getting your PR merged.

## 1. Fork and clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/<your-username>/pathreview.git
cd pathreview
git remote add upstream https://github.com/jamjamgobambam/pathreview.git
git fetch upstream
```

## 2. Set up your environment

Follow [SETUP.md](SETUP.md) to configure Docker, Python, Node.js, and environment variables.

Quick-start:
```bash
cp .env.example .env                   # configure environment
docker compose up -d                    # start PostgreSQL + Redis + ChromaDB
make setup                              # create venv, install deps, migrate DB, seed data
make run                                # start backend (:8000) + frontend (:5173)
```

Open http://localhost:5173 — log in with `user1@example.com` / `password1`.

## 3. Find an issue

Browse [open issues](https://github.com/jamjamgobambam/pathreview/issues) and look for these labels:

| Label | Description |
|-------|-------------|
| `tier-1` / `good first issue` | Starter — one file or module |
| `tier-2` | Intermediate — cross-module understanding |
| `tier-3` | Advanced — architectural or AI system changes |

Comment on the issue to let others know you're working on it.

## 4. Create a branch

```bash
git checkout -b <issue-number>-<short-description>
# Example: git checkout -b 42-fix-rate-limiting
```

## 5. Make your changes

- Follow the existing code style (the linter enforces this)
- Run the linter before committing: `make lint`
- Add or update tests for your changes
- Keep changes focused on the issue — unrelated formatting changes are discouraged

## 6. Run tests

```bash
# Fast unit tests (no Docker needed)
make test-unit

# Full suite (requires Docker services)
make test-all
```

Aim for all tests passing before submitting your PR. If pre-existing failures exist (see `make test-unit` output), note them in your PR description.

## 7. Commit and push

```bash
# Stage your changes
git add <files>

# Commit with a Conventional Commits message
git commit -m "type(scope): brief description

Closes #<issue-number>"
```

The pre-commit hook runs ruff, black, and mypy on staged files. If it fails, fix the issues and try again.

Push to your fork:
```bash
git push origin <branch-name>
```

## 8. Open a pull request

- Go to your fork on GitHub and click "Compare & pull request"
- Use the PR template — fill in each section
- Reference the issue: `Closes #<issue-number>`
- CI runs automatically on your PR — check that all checks pass
- If CI fails, push additional commits to fix

## 9. Address review feedback

- Maintainers may request changes — respond with commits
- Keep the conversation focused on the code
- Once approved, a maintainer will merge your PR

## 10. Celebrate

You've made your first contribution to PathReview. Thank you!
