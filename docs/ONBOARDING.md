# Contributor onboarding guide

This guide walks a new contributor through the full issue-to-PR lifecycle for PathReview, from choosing an issue to getting a change merged.

## 1. Start with the right issue

1. Read the repository README and contribution docs first.
2. Browse open issues in GitHub and pick one that matches your experience level.
3. Read the issue description carefully, including any acceptance criteria or linked files.
4. If anything is unclear, leave a short comment on the issue before you start coding.

A good issue usually includes:
- a clear problem statement
- relevant files or modules
- expected behavior or acceptance criteria
- the estimated scope or difficulty

## 2. Set up your local environment

Follow the setup instructions in [SETUP.md](SETUP.md) before making changes.

Typical first-time setup:

```bash
cp .env.example .env
docker compose up -d
make setup
make run
```

If you are using Windows, run the commands from Git Bash. If you hit environment issues, check the troubleshooting section in [SETUP.md](SETUP.md).

## 3. Understand the repo before changing code

PathReview is split into a few main areas:

- `api/` — FastAPI routes, schemas, and auth middleware
- `agent/` — orchestration and tool execution for portfolio feedback
- `ingestion/` — parsing, chunking, and embeddings
- `rag/` — retrieval and generation logic
- `safety/` — filtering, scrubbing, and prompt-defense checks
- `frontend/` — React + TypeScript dashboard
- `tests/` — unit, integration, and security coverage

When you start a new issue, look at the files named in the issue and the nearby tests first. That is the fastest way to understand the existing pattern.

## 4. Create a branch and make a small change

Create your working branch from `main` using the repository convention:

```bash
git checkout main
git pull origin main
git checkout -b docs/121-contributor-onboarding-guide
```

Use a branch name that reflects the issue, for example:
- `fix/123-resume-parser-index-error`
- `docs/121-contributor-onboarding-guide`
- `test/115-readme-scorer-unit-tests`

Keep your changes focused. A good contribution usually solves one issue and includes the minimum necessary files.

## 5. Follow the project workflow while you work

Before you open a PR:

1. Make the change.
2. Add or update tests when the change affects behavior.
3. Run the relevant checks locally.
4. Review your diff to make sure it is clear and intentional.

Useful commands:

```bash
make test-unit
make lint
make typecheck
make check
```

If you are changing a parser, tool, or API route, check the surrounding tests in `tests/unit/` and follow the existing pattern.

## 6. Prepare your pull request

When your change is ready, push your branch and open a pull request.

Before you mark the PR ready for review:
- fill out the PR template completely
- link the related issue in the description
- summarize what changed and why
- include the tests you ran
- mention any known limitations or follow-up work

The repository PR template lives in [.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md).

## 7. Expect review and iterate

Review feedback is part of the process. If a maintainer requests changes:

1. Read the feedback carefully.
2. Update the code or docs as needed.
3. Push a new commit or amend the existing one.
4. Re-run the relevant checks.

Once the review is complete and CI passes, your PR can be merged.

## 8. Recommended contributor checklist

Use this checklist before submitting:

- [ ] I read the issue and understood the expected outcome
- [ ] I set up the local environment successfully
- [ ] I tested my change locally
- [ ] I added or updated the relevant tests
- [ ] I followed the project’s branch and commit conventions
- [ ] I filled out the PR description completely
