## Solution plan

**Issue:** [Add a dependency vulnerability scan to the CI pipeline (#128)](https://github.com/ascherj/pathreview/issues/128)

### Understand

**Root cause:** The CI pipeline in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) has
no job or step that scans third-party dependencies for known security vulnerabilities. Nothing
runs `pip-audit` (Python) or `npm audit` (JavaScript), so vulnerable packages are never flagged.

- **Expected:** On every pull request and push to `main`, CI checks both the Python and frontend
  dependency trees against known-vulnerability databases and **fails the build** when a
  high-severity (or worse) vulnerability is found.
- **Actual:** No such check exists. Running the tools locally today reveals **13 known
  vulnerabilities** (11 JS incl. 1 critical + 5 high; 2 Python) that pass CI undetected — see
  [`docs/reproduction-128.md`](docs/reproduction-128.md).

### Map

Files/modules involved:

- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — **primary change.** Add a
  `security-scan` job (or two: Python + frontend steps).
- [`pyproject.toml`](pyproject.toml) — add `pip-audit` to the `[project.optional-dependencies].dev`
  list so the tool is available in CI and locally.
- [`Makefile`](Makefile) — add an `audit` target (and fold it into `check`) so developers can run
  the same scan locally before pushing.
- [`frontend/package.json`](frontend/package.json) — optionally add an `audit` npm script for a
  consistent local command; the frontend job already has Node + `npm ci` available.
- [`docs/reproduction-128.md`](docs/reproduction-128.md) / [`README.md`](README.md) — document the
  new check and how to run/interpret it.

### Plan

1. **Python scan step.** Add `pip-audit` to `pyproject.toml` dev deps. Add a CI step (in a new
   `security-scan` job or the `typecheck` job) that runs `pip install -e ".[dev]"` then
   `pip-audit`. Configure it to fail on findings but allow a documented ignore-list for
   accepted/unfixable advisories.
2. **Frontend scan step.** Add a step running `cd frontend && npm audit --audit-level=high`, which
   exits non-zero when a high or critical vulnerability is present.
3. **Wire severity gating.** Ensure the job fails the build only at/above the agreed severity
   threshold (high), so pre-existing low/moderate noise doesn't block unrelated PRs on day one.
4. **Local parity.** Add `make audit` running both scans and reference it in the README so the CI
   result is reproducible locally.
5. **Handle the current backlog.** Decide per-vulnerability: bump the fixable ones
   (`npm audit fix`, pinning `ws`/`react-router`) vs. record an explicit, commented ignore entry
   for anything that can't be upgraded yet — so the new gate goes green intentionally.

### Inputs & outputs

- **Input:** The committed dependency manifests / lockfiles — `pyproject.toml` + the installed
  environment for `pip-audit`, and `frontend/package-lock.json` for `npm audit`. No runtime input.
- **Output:** A new CI check that (a) reports the list of vulnerable packages + advisory IDs in the
  job log, and (b) sets the job's exit status — green when no high+ vulnerabilities remain, red
  when one is introduced. Also a `make audit` command producing the same result locally.

### Risks & unknowns

- **Failing the build on existing vulns:** turning the gate on immediately red-lights every open PR
  because of the current 13 findings. Mitigation: fix what's fixable first (step 5) and/or start at
  the `high` threshold with a reviewed ignore-list, then tighten.
- **Transitive/unfixable advisories:** some findings (e.g. deep `esbuild`/`vite` chains, or a
  Python package with no patched release yet) may have no clean upgrade. Need an ignore mechanism
  (`pip-audit --ignore-vuln`, `npm audit --audit-level`) with a comment justifying each entry.
- **`npm audit` exit-code behavior:** `--audit-level` gates the exit code by severity; need to
  verify it actually fails CI on `high` in this npm 10 / Node 22 setup rather than just printing.
- **Advisory-DB noise / flakiness:** new advisories can appear and turn a previously-green `main`
  red with no code change. Acceptable for a security gate, but worth noting in the PR.
- **Unknown:** whether maintainers prefer a separate `security-scan` job (clearer, parallel) vs.
  appending steps to existing jobs — will confirm in the issue/PR before finalizing.

### Edge cases

- **Zero vulnerabilities:** job exits 0 and stays green (must not fail on an empty result).
- **Only low/moderate findings:** with a `high` threshold, these are reported but do **not** fail
  the build.
- **A high/critical is introduced by a new PR:** job fails and blocks the merge — the core goal.
- **Ignored/accepted advisory:** listed in the ignore-list → reported but non-blocking, and the
  entry is visible/commented so it doesn't hide silently.
- **Lockfile missing or out of sync** (`npm ci` / `pip-audit` can't resolve): job should fail
  loudly rather than skip the scan, so a broken manifest never yields a false green.
- **Tool/network failure** reaching the advisory database: surfaced as an error, not a silent pass.
