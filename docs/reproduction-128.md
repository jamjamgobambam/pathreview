# Reproduction notes — Issue #128

**Issue:** [Add a dependency vulnerability scan to the CI pipeline](https://github.com/ascherj/pathreview/issues/128)

**Issue type:** Feature / security gap (not a runtime application bug)

**Date reproduced:** 2026-07-28

---

## Expected vs actual

| | Behavior |
|---|---|
| **Expected** | CI runs `pip audit` (Python) and `npm audit` (JavaScript) and **fails the build on high-severity findings**. |
| **Actual (upstream `main`)** | `.github/workflows/ci.yml` runs lint, typecheck, unit tests, integration tests, and frontend tests only. There is **no** dependency vulnerability scan. |

---

## How this was reproduced

Because #128 is a missing CI gate (not a UI bug), reproduction is:

1. Inspect the workflow on `main` (the baseline the course fork tracks).
2. Confirm no audit jobs/steps exist.
3. Confirm the relevant file named by the issue is exactly `.github/workflows/ci.yml`.

### Commands used

```bash
# On branch main (or: git show main:.github/workflows/ci.yml)
git show main:.github/workflows/ci.yml | rg -n "audit|pip audit|npm audit|vulnerability" || true

# List job names on main
git show main:.github/workflows/ci.yml | rg -n "^  [a-z].*:$"
```

### Observed results

- Search for `audit`, `pip audit`, `npm audit`, and `vulnerability` in `main`'s `ci.yml` returns **no matches**.
- Jobs present on `main`: `lint`, `typecheck`, `test-unit`, `test-integration`, `frontend`.
- Issue body names **Relevant files:** `.github/workflows/ci.yml` and asks for `pip audit` + `npm audit` failing on high-severity findings — that behavior is absent on `main`.

### Evidence snippet (jobs on `main` only)

```yaml
# Jobs on main (abbreviated): lint, typecheck, test-unit,
# test-integration, frontend — then file ends.
# No dependency-audit-python / dependency-audit-frontend jobs.
```

---

## Local verification path (for Week 9)

On a machine with the project venv and Node installed, contributors can preview the same checks CI should run:

```bash
# Python (after make setup / pip install -e ".[dev]")
python -m pip install --upgrade pip
pip audit

# Frontend
cd frontend && npm ci && npm audit --audit-level=high
```

These commands are **not** required to prove the gap exists (the missing CI steps already prove it), but they are the intended local parity for refining severity policy in Week 9.

---

## Where the fix lives

| Area | Path |
|---|---|
| Primary change | `.github/workflows/ci.yml` |
| Optional docs | `docs/SETUP.md` or CONTRIBUTING (local audit commands) |
| Optional Make target | `Makefile` (`make audit`) — only if maintainers accept extra scope |

A draft of the audit jobs already exists on this working branch from Week 7 exploration. Week 8–9 work is to **finalize policy** (severity thresholds, pinning, pre-existing advisories) and land a clean PR — not to re-discover the gap.

---

## Conclusion

The issue is **reliably reproduced**: upstream CI has no automated Python/JS dependency vulnerability scanning. The gap is localized to `.github/workflows/ci.yml` and matches the issue description.
