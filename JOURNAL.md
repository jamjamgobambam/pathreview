## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber fails to redact US phone numbers that use the parenthesized format: (123) 456-7890. The phone number pattern in `pii_scrubber.py` is configured to match phone numbers with dashes (e.g., 123-456-7890), but it cannot detect phone numbers with parentheses around the area code. As a result, it leaves parenthesized phone numbers unredacted when `scrub()` is called and incorrectly omitted when `detect()` is called. A successful fix would recognize and redact phone numbers that contain either dashes or parentheses.

**Branch name:** fix/146-pii-scrubber-failing-redact

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/CarlLuidee/pathreview/blob/fix/146-PII-scrubber-failing-redact/tests/unit/test_pii_scrubber.py

**Reproduction summary:**
`tests/unit/test_pii_scrubber.py` was ran using pytest to reproduce and verify the relevant bugs in the code. `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, and `test_phone_at_start_of_text` are failing due to a pattern matching error, but additionally `test_mixed_pii_and_text` is also failing due to scrub() over-matching.

**PLAN.md link:** https://github.com/CarlLuidee/pathreview/blob/fix/146-PII-scrubber-failing-redact/PLAN.md

**Walkthrough video (recommended):** 
<!-- [link to your Loom video, ≤2 min — recommended, not graded] -->

**Blockers or open questions:**
<!-- [Anything you're still uncertain about going into Week 9, or leave blank] -->

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

Updated PII_PATTERNS in pii_scrubber.py to fix two bugs:
1. `phone_us` failed to match phone numbers with a space after the area code parenthesis (e.g. (555) 123-4567). It has been fixed by accepting `\s` as a valid separator alongside `-/.`.
2. `street_address` used an unbounded, case-insensitive middle group that could match suffix abbreviations (e.g. `Pl`) inside unrelated lowercase words (e.g. "applications"), corrupting nearby text. It has been fixed by bounding the address to 0–3 capitalized words and requiring a word boundary after the suffix.

Prevously failing tests: `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`, and `test_mixed_pii_and_text`.

**Next steps:**
- Re-run the 5 previously failing tests to confirm they now pass.
- Run the full `test_pii_scrubber.py` suite to check for regressions elsewhere.

**Blockers:**
<!-- [Anything slowing you down? Or leave blank.] -->

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/403

**Branch:** fix/146-PII-scrubber-failing-redact

**What you built:**
<!-- [1–3 sentences summarizing what your fix does and how it works] -->
The first fix updates the `phone_us` regex to accept whitespace and not just `-` or `.` as a separator. This update makes parenthesized phone numbers followed by a space, like (555) 123-4567, now match correctly. The second fix bounds the `street_address` regex to require capitalized words within a limited range and enforces a word boundary after suffix abbreviations, preventing substrings like "Pl" from falsely matching inside unrelated lowercase words such as "applications".

**Tests added or updated:**
<!-- [Which test files did you touch? What do they cover?] -->
- `test_pii_scrubber.py`: new regression test `test_street_regex_does_not_match_inside_words()` to test `street_address` abbreviations matching inside unrelated words

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
<!-- [What did reviewers comment on? Or note that no review came in.] -->
No feedback.

**How you responded:**
<!-- [What changes did you make, or what did you reply? If no feedback, leave blank.] -->

---

### Reflection

**What was harder than you expected?**
<!-- [Be specific — what part of the process, codebase, or workflow surprised you?] -->
I found the initial setup process to be the one that surprised me most. Making sure I have the requirements to run the code, installing extra dependencies, troubleshooting when something goes wrong, and then familiarizing myself with the unfamiliar codebase. But overall, once I got past that hurdle, the process was smooth.

**What did you learn about working in a large codebase?**
<!-- [What's different about contributing to someone else's production code vs. building your own project?] -->
I learned to effectively analyze and understand new and unfamiliar code using the techniques and workflows I have learned. Another is learning proper Git contribution protocols and etiquette so that my contributions meet expectations.

**How did AI tools help — and where did they fall short?**
<!-- [Where was AI assistance most useful this module? Where did you need to go beyond what AI could give you?] -->
AI tools helped me familiarize myself with a new codebase much faster than I would have if I were to do it myself. By asking AI to describe a function or a specific part of the code, I was able to gain a much clearer idea and reduce the risk of misinterpretation.

**What would you do differently if you started over?**
<!-- [Issue selection, planning, implementation, or process — anything you'd change?] -->
I would plan more and start working on projects much earlier so that I could have more time to polish my documentation. Also, over time, I had slightly inconsistent git commit conventions, so I would aim to rectify that and provide more consistent git commit descriptions.

**What are you most proud of from this module?**
<!-- [One thing — it doesn't have to be the PR itself.] -->
Submitting my first ever PR contribution in a large-scale project.