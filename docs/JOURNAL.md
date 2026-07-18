## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The skill extraction logic in the ingestion pipeline does not reliably recognize JavaScript and TypeScript skills from resume or project text. In particular, ingestion/parsers/skill_extractor.py misses common indicators such as JavaScript and TypeScript filenames, require() calls, TypeScript interfaces, typed parameters, and other language-specific syntax. As a result, relevant skills may be omitted even when the submitted text clearly demonstrates experience with those languages. A successful fix would expand the detection logic so these common patterns are recognized while avoiding incorrect language classifications.

**Is This Issue Right for Me?**

***Can I explain what this issue is asking for in my own words?***
The the skill detection logic (code) in the ingestion pipeline does not properly detect 
TypeScript or JavaScript. The skill detection code needs to recognize TypeScript and JavaScript. TypeScript samples have to also not be detected only as 'React', but as TypeScript (especially for just pure TypeScript samples).

***Do I understand which part of the app is affected?***
This affects the ingestion part of the app

***Do I understand what "done" looks like?***
As stated above, the skill detection logic should detect JavaScript text as JavaScript. TypeScript text should also be detected as TypeScript and not only as React, especially if it is a pure TypeScript sample.

**Branch name:** fix/148-skill-extractor-js-ts-detection

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger