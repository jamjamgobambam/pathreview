## Solution plan

**Issue:** [Add a dependency vulnerability scan to the CI pipeline] - [https://github.com/ascherj/pathreview/issues/128]

### Understand

What is the root cause of this issue? What behavior is expected vs. actual?

- .github/workflows/ci.yml has no job that scans dependencies for known vulnerabilities. It runs lint, typecheck, unit tests, integration tests, and frontend tests with no calls for pip-audit or npm audit.
- EXPECTED: every PR into main and every push to main runs a dependency scan and fails the build if high/critical vulnerabilities are found.
- ACTUAL: a PR can introduce a vulnerable dependency and CI stays green, since nothing checks. I confirmed this isn't hypothetical: npm audit currently finds 11 vulnerable frontend packages and pip-audit finds 2 known vulnerabilities in the resolved Python deps (chromadb, ecdsa), none of which show up anywhere in CI output today.

### Map

Which files, functions, or modules are involved?
List the specific files you expect to touch.

- .github/workflows/ci.yml: add a new job (e.g. security-scan) with steps for pip-audit and npm audit.
- pyproject.toml: add pip-audit to [project.optional-dependencies].dev so it's installable the same way other dev tools are.
- Possibly frontend/package.json: no dependency change needed, since npm audit ships with npm itself, but might add an npm run audit script for consistency with how frontend lint/test scripts are invoked in CI.
- No application code (api/, core/, ingestion/, etc.) is touched, this is CI-config only, matching what I noted in JOURNAL.md.

### Plan

What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Add pip-audit to the dev dependency group in pyproject.toml.
2. Add a new security-scan job to ci.yml that runs on the same pull_request/push triggers as the rest of CI, with a Python step (pip-audit .) and a Node step (npm audit in frontend/).
3. Decide and encode a failure threshold, for example: fail the job on high/critical findings only, rather than failing on every low-severity advisory, so the job doesn't become permanently red/noisy.
4. Make findings visible in the PR: either job logs are enough, or mirror the pattern already used in eval.yml (actions/github-script posting a PR comment) to summarize vulnerabilities directly on the PR.
5. Add/update a test or doc note confirming the job exists and runs, like a note in docs/CONTRIBUTING.md, plus update JOURNAL.md/PLAN.md per the course process.

### Inputs & outputs

What does your fix take as input? What should it produce or change?

- Input: the repo's current dependency manifests: pyproject.toml; and frontend/package-lock.json at the commit being built.
- It should produce/change: a CI job result (pass/fail) plus a human-readable report of any vulnerabilities found, such as severity, package, advisory ID, or fix version if availablel; surfaced in the Actions log and ideally as a PR comment/annotation.

### Risks & unknowns

What could go wrong? What are you still unsure about?

- What could go wrong is that there could be no fix available for the ecdsa and chromadb CVE issues found with the backend audit. There could also be noise from the vulnerability database over time, so a previously-clean PR could start failing CI without any code change. Severity threshold tunes to a point where it is too strict, fails on low, which creates noise, OR could be too relaxed, and misses real high severity risks. Finally, Transitive vs. direct deps: several current findings (ecdsa, esbuild, postcss) are transitive, not direct — fixing them may require bumping a direct dependency rather than something in dependencies directly.

### Edge cases

What inputs or states should your fix handle gracefully?

- No vulnerabilities found (clean run): job should pass quickly and clearly, not just silently.
- pip-audit/npm audit network/service failure" should this fail CI or soft-fail with a warning?
- A dependency with a known vuln but no available fix (already observed with ecdsa/chromadb): needs an explicit allowlist/ignore path so it doesn't block every future PR forever.
- New vulnerability disclosed after a PR was already reviewed/approved but before merge: the scan should still run on the final push to main, not just at PR-open time.
