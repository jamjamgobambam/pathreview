## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/148](https://github.com/ascherj/pathreview/issues/148)

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The skill extractor is missing JavaScript and TypeScript in cases where the text clearly shows JS or TS work. The current implementation relies too much on filename hints and a narrow set of import patterns, so it misses common syntax like `const`, `require(...)`, `export interface`, and `.tsx` references in prose. A successful fix should make JS/TS detection reliable on resume and repository text while keeping the rest of the extractor behavior stable. This issue is a good fit because the affected code lives in `ingestion/parsers/skill_extractor.py` and the scope is small enough to understand and verify locally.

**Branch name:** fix/148-skill-extractor-js-ts-detection

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes:**
I checked the issue against the project layout and the branch naming rules in `docs/CONTRIBUTING.md`. The issue is narrow, reproducible, and centered in a single parser module, which keeps it realistic for Week 7. It also passed the "right for me" scope check because I validated the local environment, confirmed the app runs locally at `localhost:5173`, and verified the affected area before making the fix.

## Week 8 — Reproduction & Solution Planning

**Reproduction commit link:**
[Add the GitHub URL to the commit where you documented reproducing the issue.]

**Reproduction summary:**
I reproduced the issue by reviewing the failing unit tests referenced in the GitHub issue and testing the skill extractor with sample resume text containing JavaScript, TypeScript, and `.js`, `.ts`, and `.tsx` file references. The extractor failed to recognize JavaScript and TypeScript as skills, confirming the behavior described in the issue.

**PLAN.md link:**
https://github.com/nxxis/pathreview/blob/fix/148-skill-extractor-js-ts-detection/PLAN.md

**Walkthrough video (recommended):**
Not recorded yet. I plan to record it after finalizing my solution plan and reviewing the relevant code.

**Blockers or open questions:**
I want to verify whether the project expects JavaScript and TypeScript detection to rely only on explicit keywords or whether it should also recognize language-specific syntax such as `const`, `require()`, `export interface`, and common file extensions while avoiding false positives.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the skill extractor fix for issue 148 in `ingestion/parsers/skill_extractor.py` and added regression coverage in `tests/unit/test_skill_extractor.py`. The extractor now recognizes JavaScript and TypeScript from real-world syntax patterns instead of relying mostly on filenames and imports, and the affected unit tests pass.

**Next steps:**
Finish the PR submission details, keep the branch scoped to the issue fix, and document the validation status clearly in the PR description and journal.

**Blockers:**
The repo still has unrelated pre-existing failures in broader checks such as `make test-integration` and `make typecheck`, so I am keeping this PR scoped to the issue-specific fix and its direct validation.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/174

**Branch:** `fix/148-skill-extractor-js-ts-detection`

**What you built:**
I expanded the skill extractor so it detects JavaScript and TypeScript from common syntax patterns like `const`, `let`, `var`, `require(...)`, `export`, `interface`, and type annotations, while still preserving the existing extractor behavior for other technologies. I also added focused regression coverage for the reported JS/TS cases.

**Tests added or updated:**
I updated `tests/unit/test_skill_extractor.py`, which already contained the issue-focused regression cases, and confirmed they now pass against the new extractor logic. The suite covers Python import and type-annotation detection, TypeScript detection from `export interface` / typed members, JavaScript detection from `const` / `require(...)`, mixed-language text, React detection, PostgreSQL inference from client libraries, Dockerfile and Docker Compose patterns, filename-based detection, cloud tooling, empty-input handling, confidence scoring, and the `SkillDetection` dataclass structure. I also fixed one assertion typo in the PostgreSQL test so the file runs cleanly.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** none
