# Reproduction — Issue #128: Add a dependency vulnerability scan to the CI pipeline

**Issue:** https://github.com/ascherj/pathreview/issues/128
**Type:** Feature gap (no automated dependency vulnerability scanning in CI)
**Date reproduced:** 2026-07-27
**Environment:** macOS (Darwin 24.6.0), Node v22.12.0 / npm 10.9.0, Python 3.13 (.venv)

## What's missing and where

The CI pipeline in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) defines five jobs:
`lint`, `typecheck`, `test-unit`, `test-integration`, and `frontend`. **None of them run a
dependency vulnerability scan.** There is no `pip-audit` for Python dependencies and no
`npm audit` for the frontend dependencies anywhere in the repo.

Confirmed by searching the CI config, Makefile, and manifests:

```
$ grep -rin "pip-audit\|npm audit\|vulnerab\|safety\|trivy\|snyk" \
    .github/ Makefile pyproject.toml frontend/package.json
# → no matches (only an unrelated mypy path line)
```

`pip-audit` is not installed in the toolchain (`pyproject.toml [dev]` does not list it),
and the Makefile has no audit/security target.

## Proof the gap matters — real vulnerabilities slip through today

Because CI never scans dependencies, known-vulnerable packages currently pass CI unnoticed.
Running the audit tools locally surfaces them immediately.

### Frontend — `npm audit`

```
$ cd frontend && npm audit
...
ws  8.0.0 - 8.20.1
Severity: high
ws: Uninitialized memory disclosure  (GHSA-58qx-3vcg-4xpx)
ws: Memory exhaustion DoS           (GHSA-96hv-2xvq-fx4p)

react-router 6.0.0 - 7.17.0
Severity: moderate  (open redirect + SSR hydration advisories)

11 vulnerabilities (1 low, 4 moderate, 5 high, 1 critical)
```

### Python — `pip-audit`

```
$ pip install pip-audit && pip-audit
Found 2 known vulnerabilities in 2 packages
Name     Version  ID
-------- -------  ---------------
chromadb 1.5.9    PYSEC-2026-311
ecdsa    0.19.2   PYSEC-2026-1325
```

## Conclusion

The issue is real and reproducible: **13 known vulnerabilities (11 JS + 2 Python), including
1 critical and 5 high on the frontend, currently pass through CI undetected** because no
vulnerability-scanning step exists. The fix is to add scanning jobs/steps to
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (and optionally a `make audit`
target) that run `pip-audit` and `npm audit` and fail the build on high-severity findings.
See [`PLAN.md`](../PLAN.md) for the solution plan.

## Resolution

A `security-scan` job was added to [`.github/workflows/ci.yml`](../.github/workflows/ci.yml),
mirrored locally by `make audit`. It gates the build as follows:

- **Frontend:** `npm audit --omit=dev --audit-level=high` fails on high+ severity in
  **production** dependencies. Today those are clean (the remaining `react-router` finding
  is moderate). The high/critical advisories surfaced above all live in the **dev-only**
  build/test chain (`vite`, `vitest`, `esbuild`, `postcss`, …) and only have fixes behind
  breaking major upgrades (vite 8 / vitest 4, which also need Node 20+); they are reported
  by a separate non-blocking step and tracked for a future toolchain bump.
- **Python:** the two fixable advisories were resolved by pinning security floors in
  [`pyproject.toml`](../pyproject.toml) (`aiohttp>=3.14.3`, `cryptography>=50.0.0`). The two
  with **no patched release** are ignored via a reviewed, commented allowlist:

  | Advisory | Package | Reason ignored |
  | --- | --- | --- |
  | `PYSEC-2026-311` | `chromadb` | No patched release available upstream. |
  | `PYSEC-2026-1325` | `ecdsa` | No patched release; `ecdsa` is transitive (Minerva side-channel). |

  Revisit the allowlist (`PIP_AUDIT_IGNORE` in the [`Makefile`](../Makefile) and the matching
  flags in CI) whenever an upstream fix ships.
