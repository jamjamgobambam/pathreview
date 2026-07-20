## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/148](https://github.com/ascherj/pathreview/issues/148)

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The skill extractor is missing JavaScript and TypeScript in cases where the text clearly shows JS or TS work. The current implementation relies too much on filename hints and a narrow set of import patterns, so it misses common syntax like `const`, `require(...)`, `export interface`, and `.tsx` references in prose. A successful fix should make JS/TS detection reliable on resume and repository text while keeping the rest of the extractor behavior stable. This issue is a good fit because the affected code lives in `ingestion/parsers/skill_extractor.py` and the scope is small enough to understand and verify locally.

**Branch name:** fix/148-skill-extractor-js-ts-detection

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Selection notes:**
I checked the issue against the project layout and the branch naming rules in `docs/CONTRIBUTING.md`. The issue is narrow, reproducible, and centered in a single parser module, which keeps it realistic for Week 7. It also passed the "right for me" scope check because I already validated the local environment and confirmed the affected area before making the fix.