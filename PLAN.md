## Solution plan

**Issue:**  
Issue title: Bias detector patterns are too narrow to match common phrasings  
Link: https://github.com/ascherj/pathreview/issues/151

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The root cause is that the regex patterns in `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` are too narrow: they require near-exact phrase sequences (specific word order, specific adjacent phrasing) and don't account for plural forms or natural rewordings of the same bias. As a result, the current behavior under-detects: genuinely biased phrasings that don't match the exact regex shape return `(False, "")` instead of being flagged. This shows up as false negatives, not false positives; the tests that check clean/neutral text (e.g. `test_positive_bootcamp_mention_not_flagged`, `test_clean_feedback_not_flagged`) already pass, so the detector isn't over-flagging anywhere, it's only missing real bias it should catch.

### Map
Which files, functions, or modules are involved?

This problem is localized to one file, `safety/bias_detector.py`, within the `safety` package. The area to change is the `BiasDetector` class, specifically the `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` regex lists that `detect_bias()` iterates over. `tests/unit/test_bias_detector.py` is also involved, both as the primary way this bug is currently observed (9 failing tests) and as a file I may need to extend with additional test cases once patterns are updated.

### Plan
What are the steps to fix this issue?

1. Review the 9 currently failing tests together with the issue description, and group them by the type of phrasing gap causing the failure (e.g. bias split across two clauses, different word order, missing plural forms, indirect framing).
2. For each phrasing gap, update the relevant pattern in `DISMISSIVE_PATTERNS` or `DEMOGRAPHIC_PATTERNS` to cover that shape of phrasing, and sanity check it in Python against the related failing example plus a couple of similar phrasings I come up with myself, so the fix isn't too narrowly tied to just the exact test strings.
3. Run the scoped test file (`pytest tests/unit/test_bias_detector.py -v`) after each change and confirm the failure count decreases and the relevant test(s) now pass, without breaking any previously passing test.
4. Repeat steps 2 to 3 for the remaining phrasing gaps until all 9 target tests pass.
5. Add new test cases covering the extra phrasings I tried in step 2, then do a final run of `make test-unit` to confirm no regressions in the previously passing tests for this file.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

`detect_bias()` takes a single string (feedback text) as input and returns a `tuple[bool, str]`: whether bias was detected, and a reason string. The input space doesn't change; it's still arbitrary feedback text. What changes is the pattern matching logic inside `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS`, so that more true positive phrasings correctly return `(True, "<reason>")` with the correct reason string ("Dismissive language about educational background" or "Demographic assumptions detected"), while text that's currently correctly identified as clean continues to return `(False, "")`.

### Risks & unknowns
What could go wrong? What are you still unsure about?

The main risk is overcorrection: widening the patterns too aggressively could start flagging legitimate, non-biased text; several tests exist specifically to guard against this (`test_positive_bootcamp_mention_not_flagged`, `test_neutral_bootcamp_mention_not_flagged`, `test_clean_feedback_not_flagged`, `test_comparative_without_bias`, and especially `test_assumption_vs_observation`, which distinguishes a factual observation from a biased assumption in very similar wording). Any change needs to keep all of these passing, not just the 9 currently failing ones. There is also a risk of writing patterns too specific to the exact wording in the failing tests, rather than the general phrasing the issue describes, so I plan to check any new pattern against a couple of self-written variants too, not just the test examples themselves. Broader patterns can also become harder to read and maintain over time, and patterns using `.*` (like the existing immigrant/international one) can risk poor performance on certain inputs, though this is unlikely to matter much given feedback text is short. I'm also unsure how much of the underlying design intent behind the two categories (dismissive vs. demographic) I fully understand yet, which makes it harder to judge how broad is "broad enough" versus overreaching. Finally, it's not possible to cover every real world phrasing of bias; the goal is reasonable coverage of the patterns this issue and its tests specify, not exhaustive coverage of every possible rewording.

**Update after implementation:** the risks predicted above were largely confirmed. While fixing the two clause-split phrasings quoted directly in the issue (bias spanning two clauses via a connector like "so" or "they likely"), the natural fix used an unbounded `.*` between the trigger and the claim — the same construction already used elsewhere in the file (the immigrant/international pattern) and already flagged above as a performance/precision risk. Testing this with adversarial inputs confirmed two real false-positive classes: (1) the wildcard could bridge across sentence boundaries into unrelated text (e.g. "The candidate did a bootcamp. Separately, the documentation lacks rigor."), which was fixed by bounding the wildcard to `[^.!?]*` so it cannot cross sentence-ending punctuation; and (2) negated or reported claims (e.g. "is not lacking rigor," "the reviewer said X, but I disagree") still match, since regex has no concept of negation, attribution, or stance — only literal phrasing. (2) was deliberately left unaddressed: reliably detecting negation or reported speech would require substantial special-casing or a fundamentally different approach (NLP/LLM-based classification), which is out of scope for this narrow-pattern fix. This is documented as a known limitation in the PR description rather than fixed here.

### Edge cases
What inputs or states should your fix handle gracefully?

Empty strings and whitespace only strings should continue to return `(False, "")`, matching `test_empty_text` and `test_whitespace_only`. Detection should remain case insensitive, matching `test_case_insensitive_detection`. The hardest edge case is distinguishing a factual observation from a biased assumption when the wording is very similar (`test_assumption_vs_observation`). This needs careful handling so the fix doesn't just get more permissive and start conflating "states a fact" with "makes a biased claim." Related to this, text that reports or quotes someone else's biased statement (e.g. disagreeing with a biased opinion rather than stating it) is a case worth being careful with, along with negated bias statements (e.g. "bootcamp graduates aren't lacking in rigor") which should likely not be flagged even though they contain similar wording to a biased phrase. Where a phrasing is genuinely ambiguous between these cases, I'll need to decide whether to lean toward not flagging (avoiding false positives) or flagging (avoiding false negatives), and document that choice as a design decision when it comes up.