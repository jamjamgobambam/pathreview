## Solution plan

**Issue:** #151 - Bias detector patterns are too narrow to match common phrasings (link: https://github.com/ascherj/pathreview/issues/151)

### Understand
Right now the regex patterns in `bias_detector.py` are too strict. They only catch exact phrases like "bootcamp graduates lack rigor" but miss natural variations like "The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education." The detector needs to recognize the same bias expressed in different ways. We need to make the patterns more flexible to catch these variations without creating too many false positives.

### Map
Files I expect to touch:
- `safety/bias_detector.py`: The `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` lists where the regex patterns are defined
- `tests/unit/test_bias_detector.py`: Where the failing tests already exist that show what patterns we need to catch

### Plan
1. Look at the 9 failing tests to understand what patterns aren't being caught right now
2. For each failing test, identify the key phrase or structure and generalize it into a more flexible regex
3. Update the `DISMISSIVE_PATTERNS` list to catch variations like "bootcamp...lacks rigor" even if the words aren't consecutive
4. Update the `DEMOGRAPHIC_PATTERNS` list similarly for age-based and background-based assumptions
5. Run the tests to make sure all 9 failures pass and the 23 passing tests still pass
6. Run `make check` to make sure linting and types are clean

### Inputs & outputs
The `detect_bias()` method takes a string of feedback text and returns a tuple of `(is_biased: bool, reason: str)`. Currently it misses variations of the same bias. After the fix, it should catch both the exact phrases AND natural variations of those phrases. The function doesn't change its signature or behavior for unbiased text, instea it just becomes more accurate at detecting biased language.

### Risks & unknowns
The main risk is making patterns too loose and creating false positives. For example, if we make the patterns too broad, we might flag neutral mentions of bootcamps. I'm also not sure exactly how much flexibility we can add to the regex without breaking the existing passing tests. We'll need to be careful with the word order and required keywords.

### Edge cases
What if someone says "bootcamp education can be rigorous", which is positive, not biased. We need to make sure our patterns don't catch positive mentions. What if the bias is expressed across multiple sentences? The patterns need to work within a single feedback text string. What if someone combines two different biases in one sentence?