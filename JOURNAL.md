## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `extract_skills()` function in `ingestion/parsers/skill_extractor.py` fails to correctly identify JavaScript and TypeScript in submitted text. JavaScript-related content returns no detections at all, while TypeScript content (even when explicitly mentioning `.ts`/`.tsx` files and the word "TypeScript") is only partially detected as "React," missing the TypeScript skill itself. This suggests the language-detection patterns for the JS/TS family are missing or broken, while similar detection for Python, DevOps, and database skills works correctly. A successful fix would update the detection logic so JavaScript and TypeScript are properly recognized, with the related failing unit tests passing.

**Branch name:** fix/148-js-ts-skill-detection

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [will fill in after pushing]

**Reproduction summary:**
Ran `pytest tests/unit/test_skill_extractor.py -k "test_javascript_detection or test_text_with_typescript_files" -v` locally and confirmed both tests fail. `test_javascript_detection` fails because `require('fs')` has no space after `require`, so the detection regex `\b(import|require)\s+` never matches. `test_text_with_typescript_files` fails because TypeScript syntax (`export interface`, `export class`, `Promise<User>`) isn't recognized by any TS-specific pattern, and no false-positive React match occurs in this case since the text doesn't mention `.tsx`/`.jsx`.

Test output:
```
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_text_with_typescript_files - assert False
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_javascript_detection - assert False
2 failed, 16 deselected in 2.05s
```

**PLAN.md link:** [will fill in after pushing]

**Walkthrough video (recommended):** [optional]

**Blockers or open questions:**
Still need to confirm whether `test_devops_tool_detection` and `test_docker_compose_detection` failures (mentioned in the original issue) share the same root cause or are separate — haven't reproduced those yet.