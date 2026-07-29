# Solution plan

**Issue:** [Add a dependency vulnerability scan to the CI pipeline](https://github.com/ascherj/pathreview/issues/128) (#128 · Tier 3 · `bug` · `devops`)

---

### Understand

**Root cause:** PathReview’s GitHub Actions workflow never invokes a dependency vulnerability scanner. Contributors and maintainers only learn about known CVEs in Python or JavaScript packages through ad-hoc local checks or after something is already in production.

**Expected:** On pull requests and pushes to `main`, CI runs:

- `pip audit` against installed Python dependencies (project + dev extras)
- `npm audit` against the frontend lockfile install
- Build **fails** when findings meet the agreed high-severity policy

**Actual (upstream `main`):** `.github/workflows/ci.yml` defines `lint`, `typecheck`, `test-unit`, `test-integration`, and `frontend` only. There are no audit jobs or steps. Reproduction notes: [`docs/reproduction-128.md`](docs/reproduction-128.md).

This is a **missing security gate**, not a broken application code path.

---

### Map

| File / area | Role |
|---|---|
| `.github/workflows/ci.yml` | **Primary** — add Python and frontend audit jobs (or steps) |
| `pyproject.toml` | Defines runtime + `[project.optional-dependencies] dev` that `pip audit` will see after `pip install -e ".[dev]"` |
| `frontend/package-lock.json` | Lockfile consumed by `npm ci` before `npm audit` |
| `frontend/package.json` | Frontend dependency set |
| `Makefile` | Optional: add `make audit` for local parity with CI |
| `docs/SETUP.md` / `docs/CONTRIBUTING.md` | Optional: document local audit commands |
| `docs/reproduction-128.md` | Reproduction record (Week 8) |
| `JOURNAL.md` | Module 3 progress |

**Functions / modules:** N/A for application Python/TS — the “module” under change is the GitHub Actions job graph.

Draft audit jobs already exist on this branch from Week 7 (`dependency-audit-python`, `dependency-audit-frontend`). Week 9 should treat them as a starting point and harden policy.

---

### Plan

Concrete sub-tasks for Week 9 implementation / PR:

1. **Rebase / sync with upstream `main`** and reconfirm the gap still exists; keep reproduction docs accurate.
2. **Finalize CI design in `.github/workflows/ci.yml`:**
   - Keep (or adjust) separate `dependency-audit-python` and `dependency-audit-frontend` jobs so failures are easy to diagnose.
   - Python: upgrade pip → `pip install -e ".[dev]"` → `pip audit`.
   - Frontend: `npm ci` → `npm audit --audit-level=high` (treats high **and** critical as blocking in npm’s semantics).
3. **Resolve severity / policy unknowns** by running audits locally and/or observing GitHub Actions on this branch:
   - If existing dependencies already fail the gate, document findings and choose a maintainer-acceptable approach (upgrade deps, narrow scope, or temporary documented exception — **not** silent `continue-on-error: true`).
   - Note: built-in `pip audit` does not mirror npm’s `--audit-level=high`; decide whether “any finding fails” is acceptable or whether a pinned `pip-audit` CLI with richer flags is needed.
4. **Add contributor-facing local parity** (small, optional-but-valuable): document commands in SETUP/CONTRIBUTING and/or a `make audit` target that wraps the same commands.
5. **Validate and open PR:** confirm new jobs appear in Actions; confirm existing lint/test jobs are unchanged; fill PR template; link #128; run whatever local checks remain in scope (`make audit` / documented commands). Do **not** expand into fixing unrelated baseline `make check` / `make test-unit` debt (182 lint / 53 unit failures) unless they block *this* PR.

---

### Inputs & outputs

**Inputs**

- Repository checkout on CI (or local clone)
- Python 3.11 environment + install of `.[dev]` from `pyproject.toml`
- Node 18 + `frontend/package-lock.json` via `npm ci`
- Advisory databases used by `pip audit` / `npm audit` (network on the runner)

**Outputs / changes**

- New CI jobs (or steps) that exit non-zero when the severity policy is violated
- Clear job names/logs so a failing PR shows *which* ecosystem failed
- Optional: documented local commands so contributors can reproduce CI before pushing
- No change to application runtime behavior at `localhost:5173`

---

### Risks & unknowns

| Risk / unknown | Why it matters | Investigation path |
|---|---|---|
| **Pre-existing advisories** | First time the gate runs, CI may fail on current deps and block all PRs | Run `pip audit` and `npm audit --audit-level=high` locally; inspect Actions logs on this branch |
| **`pip audit` severity filtering** | npm can filter with `--audit-level=high`; pip’s built-in audit is coarser | Check `pip audit --help` on CI Python; consider pinning `pip-audit` package if needed |
| **Tool / pip version on runners** | `pip audit` needs a sufficiently new pip | Explicit `pip install --upgrade pip` step (already drafted) |
| **Scope creep into Makefile / docs** | Issue names only `ci.yml`; extras need maintainer buy-in | Keep docs/`make audit` as a follow-up commit; drop if PR feedback rejects |
| **False sense of security** | Audits miss some vulns; lockfile vs unlocked installs differ | Document that this is a gate, not a full security program |
| **Unrelated baseline test/lint red** | Local `make check` / `make test-unit` already noisy upstream | Out of scope for #128; do not block the security-gate PR on fixing #158/#159-style suite issues |

---

### Edge cases

1. **Clean tree:** no advisories → both audit jobs pass; PR CI green for the new gate.
2. **High/critical npm advisory only:** frontend audit fails; Python may still pass — jobs should be independent so logs show which ecosystem broke.
3. **Python advisory of any severity (if using plain `pip audit`):** job fails even if npm is clean — document this asymmetry in the PR / SETUP notes.
4. **Moderate/low npm findings:** with `--audit-level=high`, should **not** fail the build; still visible in logs if npm prints them.
5. **Transient advisory DB / network errors on the runner:** job may fail for infrastructure reasons — prefer clear error output; avoid hiding failures with `continue-on-error`.
6. **Lockfile drift:** `npm ci` fails before audit if `package-lock.json` is inconsistent — that failure is correct and separate from vulnerability findings.
7. **Dev-only Python packages:** auditing `.[dev]` may flag tooling CVEs that do not ship in production — decide whether that is desired (stricter) or whether a prod-only install is preferred; default to issue wording (project deps as installed in CI, matching other jobs’ `pip install -e ".[dev]"`).

---

## Living document

This plan will be updated in Week 9 as CI runs reveal real advisory counts and as PR review feedback arrives. Supporting diagrams: [`docs/issue-128-context.md`](docs/issue-128-context.md).
