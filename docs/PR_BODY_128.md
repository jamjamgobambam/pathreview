## Summary

Adds blocking CI jobs that scan Python runtime dependencies with pinned `pip-audit` and frontend production dependencies with `npm audit --omit=dev --audit-level=high`. This closes the missing security gate described in #128 without forcing a Vite/Vitest major upgrade into the same PR.

## Issue

Closes #128

## Changes

- Add `dependency-audit-python`: install runtime package (`pip install -e .`), pin `pip-audit==2.10.1`, fail on findings except two temporary `--ignore-vuln` IDs that currently have no fix versions (`PYSEC-2026-311` / `chromadb`, `PYSEC-2026-1325` / `ecdsa`).
- Add `dependency-audit-frontend`: `npm ci` then `npm audit --omit=dev --audit-level=high` (production deps only).
- Document local parity commands in `docs/reproduction-128.md` and `docs/SETUP.md`.
- Record Week 9 journal progress and the Option E policy decision in `PLAN.md` / `JOURNAL.md`.

## Testing

- [x] Local: `pip-audit --ignore-vuln PYSEC-2026-311 --ignore-vuln PYSEC-2026-1325` → exit 0 (2 ignored)
- [x] Local: `npm audit --omit=dev --audit-level=high` → exit 0 (2 moderate `react-router` findings only; non-blocking under `--audit-level=high`)
- [ ] GitHub Actions: confirm both new jobs appear and pass on this PR
- Pre-existing baseline noise (unchanged by this PR; docs/CI only): local `ruff check` reported ~182 issues; `pytest tests/unit` previously showed many failures/errors on this tree. This PR does not modify application Python/TS source. “Passes” here means no new application-suite failures introduced by the change set.

## Screenshots / Demo

N/A — CI configuration change. Evidence on branch: `_audit_scratch/option-e-verified.txt`, `_audit_scratch/npm-audit-omit-dev.txt`.

## Notes for Reviewers

- The earlier draft `pip audit` step is invalid here even after upgrading pip; the job installs/runs the separate `pip-audit` package.
- Python has no npm-style `--audit-level=high` in the CLI we used; fail-any plus two named temporary ignores is the closest mergeable policy.
- Frontend blocking gate is **production-scoped** on purpose. Full-tree `npm audit --audit-level=high` still fails today because of Vite/Vitest high/critical findings that require a semver-major (`npm audit fix --force` → Vite 8). That remediation should be a follow-up.
- React Router currently reports moderate advisories under production audit and does **not** fail `--audit-level=high`; still worth a follow-up upgrade.
- Please confirm whether temporary Python ignores + production-only npm scope are acceptable for merge; otherwise we can widen the gate after dep remediation lands.
