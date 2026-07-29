## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `extract_skills()` function in `ingestion/parsers/skill_extractor.py` fails to correctly identify JavaScript and TypeScript in submitted text. JavaScript-related content returns no detections at all, while TypeScript content (even when explicitly mentioning `.ts`/`.tsx` files and the word "TypeScript") is only partially detected as "React," missing the TypeScript skill itself. This suggests the language-detection patterns for the JS/TS family are missing or broken, while similar detection for Python, DevOps, and database skills works correctly. A successful fix would update the detection logic so JavaScript and TypeScript are properly recognized, with the related failing unit tests passing.

**Branch name:** fix/148-js-ts-skill-detection

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger