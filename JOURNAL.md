## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
Sandhya Rimal reviewed PR #370 and approved with no changes requested.

**How you responded:**
Since Sandhya approved with no changes requested, no code changes or reply were needed — I moved forward with marking the PR ready for review.

---

### Reflection

**What was harder than you expected?**
Understanding the existing `phone_us` regex logic was harder than I expected. The pattern already handled several phone number formats, so I had to trace through how it matched (and failed to match) parenthesized numbers with a space separator, like `(555) 123-4567`, before I could safely extend it without breaking the formats that already worked.

**What did you learn about working in a large codebase?**
Working inside `pathreview` instead of my own project meant I couldn't just rewrite the regex from scratch — I had to respect the existing pattern structure and naming conventions so the fix stayed consistent with the rest of `test_pii_scrubber.py`. It also meant paying closer attention to regression risk: a small regex change could silently break other passing tests, so I ran the full suite before and after (5 failed/20 passed → 1 failed/25 passed) rather than just checking that my new test passed.

**How did AI tools help — and where did they fall short?**
AI was useful for reasoning through regex edge cases and drafting the new test case, `test_parenthesized_phone_with_space_separator`. Where it fell short was validating that my change actually addressed issue #146 correctly in context — I still had to manually trace through real phone number examples and compare against the existing test failures to confirm the fix was targeted rather than overly broad.

**What would you do differently if you started over?**
I'd document my Check-in 2 entry with more detail the first time around — specifically, describing what each test actually verifies rather than just listing test file and test names, and writing out a plain-language summary of the fix. I know now that vague documentation costs real points even when the underlying code and review are solid.

**What are you most proud of from this module?**
Taking the test suite from 5 failed/20 passed to 1 failed/25 passed, and getting the PR approved by Sandhya Rimal with no changes requested — it confirmed the fix was correct and well-scoped, not just passing my own new test.