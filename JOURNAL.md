## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In `ingestion/parsers/resume_parser.py`, `_detect_sections()` builds its header
patterns with `^` and `\n` anchors immediately followed by the section name,
allowing no leading whitespace. PDF text extraction frequently preserves
indentation before each line, so headers like `    Experience` never match any
of the four patterns and `detected_sections` is returned as an empty list,
losing all structural metadata for the resume. The same rigid anchoring also
affects `_strip_markdown()`, where `^#+\s+` fails to strip indented markdown
headers. A successful fix inserts `\s*` after each `^`/`\n` anchor (and in the
markdown-header regex) so indented headers are recognized, restoring accurate
section detection for PDF-sourced resumes.

**Branch name:** fix/147-resume-section-detection-fails-on-text-with-leading-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger