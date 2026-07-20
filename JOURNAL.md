## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Tier reasoning:** The issue is localized and seems appropriate for the time frame.
The issue description is clear with reproducible steps and describe well what "done"
state looks like. The relevant files are also pointed out along with the unit tests.
There are quite a few others working on this issue, but it is okay given the time constraints.

**Problem summary:**
The skill extractor is failing to extract JavaScript and TypeScript in its 
language detection function. The detector is able to detect some keywords still if
provided in a certain way, but otherwise it is unable to extract the mentions of
filenames from the text and is missing some extensions (jsx, tsx). The code resides only within
`ingestion/parsers/skill_extractor.py` under `extract_skills()` and `_detect_languages()`.
It is also largely missing a whole lot of JavaScript and TypeScript keywords.
With a successful fix, the parser should recognize the filenames if mentioned in text,
and several keywords aside from "import" and "require" should be detected.

**Branch name:** fix/148-javascript-and-typescript-failed-skill-parser

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger