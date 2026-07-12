# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/128

**Issue title:** Add a dependency vulnerability scan to the CI pipeline

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3 *(as labeled)*

**Problem summary:**
The CI pipeline (`.github/workflows/ci.yml`) currently runs linting, type
checking, unit tests, integration tests, and a frontend test job, but none
of these steps check whether any Python or JavaScript dependency has a
known security vulnerability. A dependency with a published high-severity
CVE could be merged and shipped without anyone noticing. A successful fix
adds a new CI job that runs `pip-audit` against the Python dependencies and
`npm audit --audit-level=high` against the frontend dependencies, and fails
the build if either tool reports a high-severity (or worse) finding — so
vulnerable dependencies get caught at PR time instead of after merge.

**Scope reasoning:**
- *Do I understand it?* Yes, as I confirmed directly by reading `ci.yml`: there
  is no audit/security-scan step in any existing job (`lint`, `typecheck`,
  `test-unit`, `test-integration`, `frontend`).
- *Am I the right fit?* Yes, due to the following: comfortable with GitHub Actions syntax and
  both audit tools; no unfamiliar subsystem (rag/, agent/, safety/) is
  involved.
- *What's the scope?* One file and job at hand, with no cross-module reasoning
  required.
- *What's the impact?* Real, as it prevents shipping known-vulnerable deps.
- *Time cost?* This issue estimates 3–5 hours, which I'm treating that as a rough
  starting point, not a guarantee due to unknowns discussed below.

**Tier note (honesty over label-matching):** This issue is labeled
`tier-3`, but per the tier table (one file touched, no multi-module
understanding needed, 3–5 hour estimate), the actual scope reads closer to
Tier 1/2. I'm keeping the tier box checked as labeled since that's what the
tracker assigns, but flagging the mismatch explicitly rather than silently
inflating or deflating my own effort estimate to match the label.

**Known unknowns — resolved during investigation:**
- **Resolved:** `pip-audit` has no built-in severity-threshold flag
  (`--fail-on`/`--severity` do not exist). Confirmed via `pypa/pip-audit`
  GitHub issues #654 and #670, where this exact feature has been requested
  and remains unimplemented as of this writing. By default `pip-audit`
  exits non-zero on *any* finding. To honor the issue's "fail on
  high-severity" requirement, the CI step requests `-f json` output and
  filters for `HIGH`/`CRITICAL` with `jq` before deciding whether to fail
  the build. Documenting this as a deliberate design choice, not a
  workaround for something I forgot to check.
- **Resolved:** `pip-audit` is not currently installed locally (`command
  not found`) and is not listed in `pyproject.toml`'s `[project.optional-
  dependencies].dev` list. Decision: install it as an explicit CI-only step
  (`pip install pip-audit`) rather than adding it to `pyproject.toml`, to
  keep the diff scoped to the CI workflow file only, per the issue's
  "Relevant files: .github/workflows/ci.yml" scope.
- **Open, needs a decision before PR:** `docs/CONTRIBUTING.md` lists `ci`
  as a valid **commit type**, but its scope list (`ingestion`, `rag`,
  `agent`, `safety`, `api`, `frontend`) has no scope for CI/infra changes,
  and the branch-type list also omits `ci`. There's a real gap here I
  can't resolve by reading the docs alone. I'll either 
  (a) use `ci: add dependency vulnerability scan` with no scope, or
  (b) ask in the PR description / a maintainer comment which convention they'd prefer.
  Noting this explicitly rather than guessing silently.

**Branch name:** `feat/128-dependency-vulnerability-scan`

*(`CONTRIBUTING.md`'s branch-type list is `fix`, `feat`, `test`, `docs`,
`refactor`, `perf`, `chore` — no `ci` type, even though `ci` is a valid
**commit** type. Choosing `feat` over `chore` because this adds new
CI capability visible to contributors (a new required check), not just
internal tooling maintenance.*

**Setup confirmation:** [ ] Can confirm the app runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger