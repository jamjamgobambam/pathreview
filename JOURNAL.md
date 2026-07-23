\# JOURNAL



\## Week 7 — Issue selection



\*\*Issue link:\*\* https://github.com/ascherj/pathreview/issues/147



\*\*Issue title:\*\* Resume section detection fails on text with leading whitespace



\*\*Tier:\*\* \[x] Tier 1  \[ ] Tier 2  \[ ] Tier 3



\*\*Problem summary:\*\*

The `\_detect\_sections()` method in `ingestion/parsers/resume\_parser.py` uses

regex patterns anchored to the very start of each line (e.g. `^Experience`),

but text extracted from PDFs often keeps its original indentation, so headers

like "Education:" appear with leading spaces. Because the anchored patterns

never match indented headers, `detected\_sections` comes back completely empty

for that input, and the resume content is never split into structured

sections. This also causes three unit tests in

`tests/unit/test\_resume\_parser.py` to fail. A successful fix would make the

matching tolerant of leading whitespace — for example by stripping/normalizing

lines before matching or allowing optional whitespace in the patterns — so

that sections are detected regardless of indentation and the failing tests

pass.



\*\*Is this right for me? — reasoning:\*\*

The problem is isolated to one method in one file, comes with a minimal

reproduction snippet, and already has failing unit tests that define exactly

what "fixed" looks like. No database, API, or frontend changes are involved,

so the scope is well contained and fits Tier 1.



\*\*Branch name:\*\* fix/147-resume-leading-whitespace



\*\*Setup confirmation:\*\* \[x] App runs locally at localhost:5173



\*\*Cohort ledger:\*\* \[x] Issue added to cohort ledger

