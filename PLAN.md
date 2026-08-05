## Solution plan

**Issue:** [issue title and link]

Bias detector patterns are too narrow to match common phrasings #151
https://github.com/ascherj/pathreview/issues/151

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

`detect_bias` in `bias_detector.py` uses a set of regex patterns (`DISMISSIVE_PATTERNS`, `DEMOGRAPHIC_PATTERNS`) to detect bias in a provided text. The patterns are written such that they require near-exact phrase adjacency (fixed word order, inconsistent plural nouns, one verb per concept). 

As such, natural paraphrases will not be detected by the existing patterns. For example, "bootcamp graduates lack rigor" is detected, but not "the candidate only attented a bootcamp, so this project lacks sufficient rigor". 


### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

1. `bias_detector.py` - file containing the `detect_bias` method
2. `DISMISSIVE_PATTERNS`, `DEMOGRAPHIC_PATTERNS` - regex patterns referenced by `detect_bias`. I'll modify the regex patterns here. 
3. `test_bias_detector.py` - file containing the unit tests with different biased and non-biased texts. I'll add a unit test for the bug reporter's natural rephrasing following existing patterns. I'll also rerun the entire set of tests to make the fix passes all of them. 


### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Review the failing unit tests in `test_bias_detector.py` to identify how the existing regex patterns are failing

2. Modify the patterns in `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` to catch the failing patterns as well as other potential refinements. 

3. Add an additional unit tests into `test_bias_detector.py` with the bug reporter's natural rephrasing 

4. Rerurn the entire set of tests in `test_bias_detector.py` to make the fix makes all the test pass. Note, I'm skipping running the entire test suite as `detect_bias` is only referenced by `test_bias_detector.py`.  


### Inputs & outputs
What does your fix take as input? What should it produce or change?

The fix preserves the existing behavior as documented in docstring for `detect_bias`, i.e., 
- Input: text
- Output: Tuple of `(is_biased, reason)`


### Risks & unknowns
What could go wrong? What are you still unsure about?

I'm "loosening" the regex patterns to catch rephrasings. However this could generate more false-positives and false-negatives. For example, I could trigger a false-positive for "The bootcamp training was solid, so this project doesn't lack rigor." 

On a larger note, regex patterns are deterministic pattern matching and as limited compared to a natural language classifier. For example, an approach that uses connectors (e.g., `so|because|since`) to allow triggers words to be further apart in a sentence may not be exhaustive (e.g., misses `given|given that`). 

We'll have to monitor the degree of false-positives and false-negatives to keep refining the patterns, and potentially even consider implementing a different classifier approach (e.g., LLM classifier). 


### Edge cases
What inputs or states should your fix handle gracefully?

1. **Unrelated co-occurrence.** Widening a pattern to match "bootcamp" and "lacks rigor" anywhere in the text risks matching two unrelated observations that happen to co-occur, not an actual dismissive claim. 

Example: "Your resume lists a bootcamp certificate under Education. The system design write-up lacks the rigor expected for this level of role."

2. **Broadening trigger words.** Adding additional trigger words (e.g., `missing`, `gap`) may make it more likely to trigger false-postives. 

Example: "Your resume is missing details on international education."
    




