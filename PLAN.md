## Solution plan

**Issue:** [Faithfulness checker can never mark short claims as supported](https://github.com/ascherj/pathreview/issues/152)

### Understand

The faithfulness checker determines whether generated feedback is grounded in
retrieved context by comparing overlapping non-stopword tokens. The current
`_is_supported()` implementation requires at least two meaningful token matches
for every claim.

This causes short claims such as `Python expert` or `Skilled with Docker` to be
marked unsupported even when their main technical keyword appears directly in
the context. The current whitespace-based tokenization also leaves punctuation
attached to words, so tokens such as `Python,` do not match `Python`.

The expected behavior is for short, specific claims to be recognized as
supported when the context contains strong matching terms, while unrelated
claims and matches based only on common words should remain unsupported.

### Map

Files expected to change:

- `rag/evaluator/faithfulness_checker.py`
  - `FaithfulnessChecker._is_supported()`
  - Token normalization and meaningful-overlap logic

- `tests/unit/test_faithfulness_checker.py`
  - Existing failing tests for partial and short-claim support
  - Additional regression tests for punctuation and false-positive cases

The `check()` and `_extract_claims()` methods may be reviewed while testing, but
changes to claim extraction are outside the initial scope unless required to
satisfy Issue #152.

### Plan

1. Replace whitespace-only tokenization in `_is_supported()` with normalized
   token extraction so punctuation does not prevent valid matches.

2. Filter stop words before evaluating the overlap between the claim and
   context.

3. Introduce an adaptive support rule that allows a short claim to be supported
   by one specific meaningful token while keeping a stricter threshold for
   longer or less-specific claims.

4. Add or update unit tests covering:
   - A short supported technical claim
   - A short unsupported claim
   - Terms followed by punctuation
   - Matches containing only stop words or weak common words

5. Run `tests/unit/test_faithfulness_checker.py` and the broader unit test suite
   to confirm that the fix resolves Issue #152 without causing regressions.

### Inputs & outputs

Input:

- A generated feedback string containing one or more claims
- A list of retrieved context chunks
- Individual claim and context strings passed to `_is_supported()`

Current incorrect output:

- Short claims with one strong matching technical term return `False`
- Their overall faithfulness score can incorrectly become `0.0`

Expected output:

- Short, clearly grounded claims return `True`
- Unsupported claims still return `False`
- The final score reflects the proportion of supported claims and remains
  between `0.0` and `1.0`

### Risks & unknowns

- Allowing every single-token overlap may create false positives for vague words
  such as `project`, `experience`, or `developer`.

- Token normalization must not break specialized technical terms such as
  `PostgreSQL`, `C++`, `C#`, `.NET`, `Node.js`, or `CI/CD`.

- The exact distinction between a strong technical token and a weak generic
  token is not currently defined in the codebase.

- `_extract_claims()` ignores sentences of ten characters or fewer, which may
  affect short claims such as `Knows Rust`. This appears related but may be
  outside the direct scope of Issue #152.

- `test_none_context_chunk_text` currently fails because `None` is passed into
  `" ".join()`. This is an existing separate issue and will not be included in
  this fix unless maintainers confirm that it belongs in scope.

### Edge cases

- A claim and context share only stop words
- A claim shares one generic word but is otherwise unrelated
- A short claim contains one specific technical term
- Relevant terms include commas, periods, or other punctuation
- Matching terms use different capitalization
- The context is empty or contains no useful tokens
- Technical terms contain special characters
- Multiple context chunks collectively support a claim
