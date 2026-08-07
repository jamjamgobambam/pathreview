## Solution plan

**Issue:** [Write a contributor onboarding guide that walks through a complete issue → PR lifecycle](https://github.com/ascherj/pathreview/issues/121)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The gap is not a runtime bug but a documentation gap: the repository already has setup and contribution guidance, but those instructions are spread across several files and do not give a new contributor a clear walkthrough of how to understand the codebase, move from an issue to a branch, and prepare a pull request. The expected behavior is a single onboarding path that explains the repo structure, local workflow, and contribution expectations end to end.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

I expect to review and update the following files:
- [README.md](README.md)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- [docs/SETUP.md](docs/SETUP.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [api/main.py](api/main.py)
- [agent/orchestrator.py](agent/orchestrator.py)
- [ingestion/pipeline.py](ingestion/pipeline.py)

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Review the current docs and application entry points to identify where contributor guidance is missing or fragmented.
2. Draft a contributor onboarding guide that explains the issue-to-PR lifecycle, local setup, repo navigation, and validation steps.
3. Link the new guide from the existing documentation entry points so a first-time contributor can discover it quickly.
4. Update the project journal with the Week 8 reproduction summary and the plan link.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

Input: the existing repository docs, the current setup instructions, the main runtime entry points, and the issue context.

Output: a clearer contributor-facing onboarding path in the documentation that helps a new contributor understand the project structure and the expected contribution workflow.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- The repository workflow may evolve as new tools or services are added, so the guide must stay aligned with the current setup commands.
- Some contributor steps depend on external services such as Docker, PostgreSQL, Redis, and OpenRouter, so the documentation needs to reflect the current environment assumptions accurately.
- Because this is a documentation task rather than a code bug, the main risk is over- or under-explaining the project without making the guide practical for a first-time contributor.

### Edge cases
What inputs or states should your fix handle gracefully?

- Contributors using macOS, Windows, or Linux may need slightly different setup instructions.
- Fresh clones may not have environment variables or Docker services running yet.
- Contributors who are unfamiliar with the API, agent, ingestion, and frontend layers may need a simple map of where to start reading.
