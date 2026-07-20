# Solution plan

**Issue:** [Add a dependency vulnerability scan to the CI pipeline (#128)](https://github.com/jamjamgobambam/pathreview/issues/128)

## Understand

**Root cause:** `.github/workflows/ci.yml` runs five jobs :`lint`,
`typecheck`, `test-unit`, `test-integration`, `frontend`, and none of them
check whether any installed dependency (Python or JavaScript) has a known
security vulnerability. This isn't a bug in existing code; it's a missing
capability. Confirmed by reading the entire file: no `pip-audit`, `npm
audit`, `safety`, or equivalent step exists anywhere.

**Expected vs. actual behavior:**
- Expected: a PR that introduces or retains a dependency with a known
  high-severity CVE should fail CI before merge.
- Actual: nothing checks this. Confirmed with real data, not a
  hypothetical — running `pip-audit .` against this repo's actual
  `pyproject.toml`-declared dependencies found two unfixed
  vulnerabilities (`chromadb` pre-auth RCE, `ecdsa` timing attack), and
  `npm audit` against `frontend/` found 11 real vulnerabilities including
  1 critical and 2 high. All of this currently ships silently.

## Map

Files touched:
- **`.github/workflows/ci.yml`** — add one new job, `security-audit`.
  This is the only file the issue names, and the only file this change
  touches. No other file needs modification.

Files read (not touched) during investigation:
- `pyproject.toml` — confirmed `pip-audit` is not currently a declared
  dev dependency; confirmed which packages are in scope for the Python
  audit (`fastapi`, `sqlalchemy`, `chromadb`, `openai`, etc.)
- `frontend/package.json` — confirmed no existing audit-related
  dev-dependency conflicts
- `docs/CONTRIBUTING.md` — read for branch/commit conventions; found a
  real gap (see Risks below)

## Plan

1. Add a `security-audit` job to `ci.yml` that installs `pip-audit`
   ad hoc (not added to `pyproject.toml`, to keep the diff scoped to the
   CI file only) and runs `pip-audit .` scoped to this project's declared
   dependencies — not the whole environment (bare `pip-audit` was
   confirmed, by testing, to sweep in unrelated devcontainer tooling).
2. In the same job, add an `npm audit --audit-level=high` step for
   `frontend/`, reusing the existing `setup-node` caching pattern already
   used in the `frontend` job.
3. Decide and implement an explicit `--ignore-vuln` policy for `pip-audit`
   findings that have no fix and are judged low-risk (currently: the
   `ecdsa` Minerva timing attack, PYSEC-2026-1325), with the reasoning
   documented inline in `ci.yml`, not just in this plan.
4. Deliberately do **not** add the `chromadb` RCE (PYSEC-2026-311) to the
   ignore-list, even though doing so would make the job pass cleanly.
   Document this decision and its consequence (CI will fail on `main`
   immediately after merge) in the PR description as a flagged follow-up,
   not something quietly worked around.
5. Verify the job's actual pass/fail behavior locally before opening the
   PR — already done: confirmed both commands exit non-zero with the
   real, current findings, and confirmed the ecdsa ignore correctly
   suppresses only that one finding.

## Inputs & outputs

- **Input:** the CI runner's recently-installed Python and Node dependency
  sets, resolved at job runtime from `pyproject.toml` and
  `frontend/package-lock.json`.
- **Output:** a new required-looking check (`security-audit`) appearing
  in the GitHub PR checks list. Non-zero exit on either sub-step fails
  the whole job. No code behavior changes — this is CI configuration
  only, not application logic.
- **Known limitation on output:** as a fork contributor, I don't have
  admin access to configure branch protection rules on the upstream repo.
  Adding this job makes the check *appear*, but whether it's marked
  **required** (blocking merge) vs. advisory is a maintainer-side setting that
  I can't control or verify from here. 

## Risks & unknowns

- **Resolved during investigation, not assumed:** `pip-audit` has no
  `--fail-on`/severity-threshold flag, and separately, its JSON output in
  the version this project resolves (2.10.1) has no `severity` field at
  all on findings — confirmed against this repo's actual output, not the
  tool's docs. This makes `npm audit`-style severity filtering impossible
  for the Python side; the policy is fail-on-any-finding plus an explicit,
  documented ignore-list instead.
- **Real, unresolved, and intentionally not fixed here:** `chromadb`
  1.5.9 has an unfixed pre-auth code-injection/RCE vulnerability
  (PYSEC-2026-311 / CVE-2026-45829) in a direct RAG-subsystem dependency.
  Fixing this is out of scope for #128 (the issue asks for scanning
  capability, not remediation of every finding), but merging this PR
  as-is will make CI fail on `main` immediately. This needs to be
  surfaced explicitly to a maintainer/instructor, not buried in a commit
  message.
- **Accepted, documented risk:** `ecdsa` 0.19.2's Minerva timing attack
  (PYSEC-2026-1325 / CVE-2024-23342) has no fix; maintainers have stated
  side-channel attacks are out of scope for their project. Explicitly
  ignored via `--ignore-vuln`, with the reasoning recorded in `ci.yml`
  itself so it isn't a silent suppression.
- **Open, needs a decision before PR:** `docs/CONTRIBUTING.md` lists `ci`
  as a valid commit type but has no matching scope (`ingestion`, `rag`,
  `agent`, `safety`, `api`, `frontend` — no `ci`/`devops`/`infra`), and no
  `ci` branch type either. I'll use `ci: add dependency vulnerability
  scan` with no scope for the commit, and flag the gap in the PR
  description rather than guessing at an undocumented convention.
  Investigation needed: ask the maintainer directly, or check if any
  merged PR in the repo's history has set a precedent.
- **Time-based unknown:** vulnerability databases (OSV, PyPI advisory)
  update continuously. The exact findings reported today (chromadb,
  ecdsa, the 11 npm findings) could differ by the time this PR is
  reviewed — new CVEs could appear, or upstream releases could resolve
  some findings independently. The reproduction evidence in this plan is
  a snapshot, not a permanent guarantee.

## Edge cases

- **Lockfile drift:** if `frontend/package-lock.json` is out of sync with
  `package.json`, `npm ci` (strict mode) fails *before* the audit step
  even runs — the job would show red for a reason unrelated to
  vulnerabilities. Worth being able to distinguish this failure mode from
  an actual audit finding when reading CI logs.
- **New CVE disclosed between PR open and merge:** the audit re-runs on
  every push, so a newly disclosed CVE in an unrelated dependency could
  make a previously-green PR go red without any code change — expected
  behavior for a security gate, but worth documenting so it isn't
  mistaken for a broken CI job.
- **`pip-audit`/`npm audit` network failure:** both tools query external
  vulnerability databases (PyPI Advisory DB via OSV; npm registry). A
  transient network failure in the CI runner would fail the job for a
  reason unrelated to actual vulnerabilities. Not something this PR can
  fully prevent, but worth a clear job name (`security-audit`) so a
  flaky-vs-real failure is easier to triage from the Actions log alone.
- **Branch-protection non-enforcement:** as noted in Inputs & Outputs,
  even a correctly failing job may not actually block a merge if the
  check isn't marked required upstream, an edge case in the *process*,
  not the code, but relevant to whether this issue is meaningfully
  "done" once merged.