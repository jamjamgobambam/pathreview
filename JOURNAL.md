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
- **Resolved:(superseded, view below):** Initially assumed `pip-audit`
  would need JSON output + `jq` filtering to approximate severity
  thresholds. Real testing showed this was itself wrong in a more basic
  way: bare `pip-audit` audits the *entire installed environment*
  (confirmed it picked up unrelated Jupyter/Poetry devcontainer tooling,
  not this project's dependencies at all). Fixed by scoping to the project
  directory: `pip-audit .` (per official docs,it resolves dependencies
  from `pyproject.toml` when given a path). I confirmed the scoped run only
  reports on packages actually declared in `pyproject.toml`. 
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

**Cohort ledger:** [ ]  N/A - > tech fellow*

## Week 8 : Reproduction & solution planning
**Reproduction summary:**
Confirmed the gap is real, not assumed, by actually running both audit
tools against this repo's real dependencies. Scoped `pip-audit .` (bare
`pip-audit` was initially misleading. It audits the *entire installed
environment*, not just this project's deps; using `.` scopes it to
`pyproject.toml`) surfaced two real findings: `chromadb` 1.5.9 has an
unfixed pre-auth code-injection/RCE vulnerability (PYSEC-2026-311), and
`ecdsa` 0.19.2 has an unfixed Minerva timing-attack weakness the
maintainers have declared out of scope (PYSEC-2026-1325). `npm audit`
against `frontend/` found 11 real vulnerabilities including 1 critical
(`vitest`, CVSS 9.8) and 2 high (`form-data`, `ws`). Verified that a
draft CI job running `pip-audit . --ignore-vuln PYSEC-2026-1325` and
`npm audit --audit-level=high` both correctly exit non-zero right now —
confirming the tooling would actually catch what today's `ci.yml` misses
entirely.
**Blockers or open questions:**
Two real open questions carried into Week 9, not blockers exactly, but
decisions that need to be made before the PR is final: (1) whether to
flag the `chromadb` RCE to course staff/maintainer directly given its
severity, since fixing it is out of scope for #128 but leaving it
undocumented would be irresponsible; (2) `docs/CONTRIBUTING.md` has no
`ci` scope or branch-type entry, so the exact commit/branch convention for
this change is a judgment call rather than a documented standard — see
PLAN.md Risks section.
 