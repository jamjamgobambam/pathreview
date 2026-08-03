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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [Note and summarize reproduction steps](https://github.com/nathnet/pathreview/commit/3d9f87ad6b215d3dbc393537c7d4d6fc4367ae5d)

**Reproduction summary:**
I followed the step-by-step production code provided in the issues in my local python interpreter.
The issues are as described with the SkillExtractor only extracting JavaScript and TypeScript
if provided in a certain way (filename, and import statements). But the extractor fails to detect
mentions of filenames or other JS/TS keywords inside the text itself.

**Reproduction note:**
First I went over to issue [#148](https://github.com/ascherj/pathreview/issues/148) to read through the issue again.
I then took the `steps to reproduce` section and went over to my terminal and started with `py`.
After the Python intepreter is up, I pasted the reproduction steps line-by-line:
```
from ingestion.parsers.skill_extractor import SkillExtractor
e = SkillExtractor()
print(e.extract_skills('Wrote index.js using const arrow functions and async/await callbacks'))
print([d.name for d in e.extract_skills('Built app.tsx and types.ts with strict TypeScript interfaces')])
print([d.name for d in e.extract_skills('Built app.tsx and types.ts with strict TypeScript interfaces', 'test.ts')])
print([d.name for d in e.extract_skills('Built app.tsx and types.ts with strict TypeScript interfaces and import tests')])
```
The results are as described in the issues. The first print statement returns an empty list despite 
a clear mention of "index.js", "const", "arrow functions", "async/await callbacks". The second print also
returns only "React" as the detected skill despite the presence of "app.tsx", "types.ts", and 
"TypeScript interfaces" in the message. This indicates that the skill extractor is unable to parse
JavaScript and TypeScript related keywords from the text. The third and fourth print statement confirms that
the `_detect_languages()` is called and can parse if the filename is provided. This shows that
the extractor is working, but not covering all the extraction cases.

**PLAN.md link:** [view PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** [Loom video](https://www.loom.com/share/5cd041826f92401cbc701dcc4a884bf1)

**Blockers or open questions:**
- Should the JS/TS keyword only trigger one of the languages or both?
- Should I implement the minimum keyword matches before we declare a language skill detected?

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Step 1 of the plan is complete. Added regex-based scanning of text content for `.js`, `.jsx`, `.ts`, `.tsx` file extension mentions in `_detect_languages()` (`skill_extractor.py` lines 178-181). Updated the `lang` determination logic to also consider text-based TypeScript signals, not just the `filename` parameter. Added two new tests: `test_js_extension_in_text` and `test_ts_extension_in_text`.

**Next steps:**
- Step 2: Expand JS/TS keyword detection to use more of `JS_TS_KEYWORDS` (`const`, `let`, `var`, `export`, `function`) and fix the `require` regex from `\s+` to `\b`.
- Step 3: Add TypeScript-specific text patterns (`typescript`, `interface`, generic types) for text-based TypeScript detection.
- Step 4: Add Dockerfile keyword and docker-compose detection to `_detect_tools()`.
- Step 5: Run all four target tests and verify no regressions.

**Blockers:**
Leading the capstone project effort for WEB103, which includes implementing features, conducting code reviews, and coordinating with teammates to keep the project on track. This is taking up a significant portion of my available time this week.

**Existing failures:**
- Aside from the targets in `test_skill_extractor.py`, there's one more failing test: `test_database_technology_detection`
- 19 mypy errors on function missing a type annotation in `test_skill_extractor.py`

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** `fix/148-javascript-and-typescript-failed-skill-parser`

**What you built:**
Extended `_detect_languages()` in `skill_extractor.py` to detect JavaScript and TypeScript from text content — scanning for `.js`/`.jsx`/`.ts`/`.tsx` file extension mentions, JS keywords (`const`, `let`, `var`, `export`, `function`, `class`, `async`, `await`, `require`), and TypeScript-specific patterns (`interface`, type annotations, generic types, the word "typescript"). Also extended `_detect_tools()` to detect Docker from Dockerfile instructions (`FROM`, `RUN`, `EXPOSE`, etc.) and docker-compose structure, without requiring the word "docker" to appear explicitly.

**Tests added or updated:**
Added 7 new tests to `tests/unit/test_skill_extractor.py`: `test_js_extension_in_text`, `test_ts_extension_in_text`, `test_js_keywords_in_text`, `test_javascript_keyword_in_prose`, `test_typescript_keyword_in_prose`, `test_typescript_type_annotations`, and `test_docker_filename_in_prose`. All 4 originally failing tests now pass. The only remaining failure is `test_database_technology_detection`, a pre-existing bug in the test itself (references `skill_names` before it's defined).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]