## Solution plan

**Issue:** Add a dependency vulnerability scan to the CI pipeline —
https://github.com/ascherj/pathreview/issues/128

### Understand

**Root cause.** The CI pipeline in `.github/workflows/ci.yml` runs `lint`,
`typecheck`, `test-unit`, `test-integration`, and `frontend` jobs. None of these
inspect third-party dependencies for *known* published vulnerabilities. There is
no `pip-audit` step for the Python dependency set and no `npm audit` step for the
frontend's `package-lock.json`. As a result, a Python package or npm module with
a published CVE can be merged into `main` with a fully green build.

**Expected vs. actual.**
- *Expected:* every pull request is automatically gated on a clean dependency
  scan. A newly introduced high-severity (or worse) advisory fails the build
  before merge.
- *Actual:* dependency advisories are never checked in CI. Reproduced locally:
  `pip-audit` reports **39 vulnerable packages / 188 advisories**, and
  `npm audit --audit-level=high` exits non-zero with **11 vulnerabilities
  (1 critical, 4 high)** — yet CI stays green.

### Map

Files I expect to touch:

- **`.github/workflows/ci.yml`** *(primary)* — add a new `dependency-scan` job
  (or two jobs / a matrix) that installs the project, runs `pip-audit` against
  the Python dependencies and `npm audit` against `frontend/package-lock.json`,
  and fails on a high-or-worse advisory.
- **`.github/audit-config/`** *(optional, new)* — a documented allow-list /
  ignore file (e.g. `pip-audit` `--ignore-vuln` IDs and an npm allow-list) so
  that pre-existing, unfixable-today advisories don't red-wall the pipeline on
  day one while still gating *newly introduced* ones.
- **`pyproject.toml`** *(maybe)* — add `pip-audit` to the `[dev]` optional
  dependencies so the tool version is pinned/reproducible rather than floating.
- **`README.md` / `docs/`** *(maybe)* — a short note documenting the scan, the
  chosen severity threshold, and how to update the allow-list.

No application code (Python or React) changes.

### Plan

1. **Add the npm scan.** New job `dependency-scan-frontend` (or a step in a
   combined job): `actions/setup-node@v4`, `cd frontend && npm ci`, then
   `npm audit --audit-level=high`. Confirm it fails the build against the
   current lockfile (already reproduced: 1 critical / 4 high).
2. **Add the Python scan.** New job `dependency-scan-python`: `setup-python@v5`,
   `pip install -e ".[dev]"` (mirroring existing jobs) plus `pip-audit`, then
   run `pip-audit` on the resolved environment, failing on the chosen threshold.
3. **Decide the day-one baseline.** The repo already has pre-existing high-sev
   advisories, so a naive scan reds the pipeline immediately. Choose and
   document one of: (a) upgrade the fixable packages, (b) an explicit,
   commented allow-list of advisory IDs to ignore, or (c) a severity threshold —
   and confirm the intended behavior against the issue. Default proposal:
   allow-list existing advisories + gate strictly on *new* high/critical ones.
4. **Wire it into the pipeline gate.** Ensure the new job(s) are required for the
   PR to pass (they run on the same `pull_request`/`push` triggers as the rest).
5. **Verify & document.** Re-run locally, push, confirm the job appears and
   behaves as intended on a PR, and add a short README/docs note on the
   threshold + how to update the allow-list.

### Inputs & outputs

- **Input:** the project's resolved dependency sets — the installed Python
  environment (from `pyproject.toml` / `pip install -e ".[dev]"`) and
  `frontend/package-lock.json` — plus the optional allow-list config.
- **Output:** a CI job that exits non-zero (fails the build) when a
  high-severity-or-worse advisory is present outside the allow-list, and exits
  zero on a clean scan. No changes to runtime/app behavior. Human-readable audit
  output in the CI logs for triage.

### Risks & unknowns

- **Pre-existing advisories fail day one.** Reproduced: both ecosystems already
  have high/critical findings. Need author sign-off on allow-list vs. upgrade
  vs. threshold before this can merge green. *(Primary open question.)*
- **The frontend fix is a breaking upgrade, not a patch.** The critical finding
  is a CVSS 9.8 RCE in `vitest@1.6.1` (GHSA-5xrq-8626-4rwp — arbitrary file
  read/execute while the Vitest UI server is listening). Remediating it (and the
  related `vite`/`vite-node`/`esbuild` highs) is *not* a clean `npm audit fix`:
  the dry run pulls in `vite@8`, a major version bump (46 packages added, 30
  changed) that can break the frontend build and tests. So "just upgrade" is
  itself a scoped task — the deps must be bumped deliberately and the frontend
  test suite re-run, not force-fixed. This is a concrete reason the allow-list
  path may be preferable for the initial gate, with the vite/vitest upgrade
  tracked as follow-up work. *(Note: the RCE is dev/test-time only — it requires
  the Vitest UI server to be running — so it is not exploitable in headless CI
  runs or in shipped app code.)*
- **Noise / flakiness.** Advisory databases update continuously, so a build that
  passed yesterday can fail today when a *new* CVE is published against an
  unchanged lockfile. Allow-list + clear failure messaging mitigates confusion.
- **`npm audit` scope.** By default it flags transitive/dev-only deps that may
  not be exploitable at runtime; `--omit=dev` or `--production` may be more
  appropriate — need to decide.
- **Tool availability/pinning.** `pip-audit` must be installed in CI; pin a
  version so results are reproducible.
- **Network dependency.** Both tools query remote advisory DBs; a registry
  outage could fail the job for reasons unrelated to the code.

### Edge cases

- **Clean scan** → job passes (exit 0), no false failure.
- **Only low/moderate advisories** below the threshold → job passes but surfaces
  them in logs.
- **A high/critical advisory that is on the allow-list** → job passes; allow-list
  entry documented with a reason/expiry.
- **A newly introduced high/critical advisory not on the allow-list** → job
  fails — the core behavior being added.
- **`npm ci` / `pip install` failure** (unrelated to advisories) → job fails
  loudly and distinguishably, not silently skipped.
- **Empty/absent lockfile or dependency set** → job errors clearly rather than
  falsely reporting "clean."
