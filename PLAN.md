# Solution plan

**Issue:** Faithfulness checker can never mark short claims as supported —
https://github.com/ascherj/pathreview/issues/152

### Understand

The faithfulness checker scores generated feedback by splitting it into claims
(sentences) and measuring how many are "supported" by the retrieved context.
Reproduced locally against commit `ef14e1f`:

- `check("Knows Python. Knows SQL.", [{"text": "python expert"}, {"text": "sql expert"}])`
  returns `0.0`, even though both claims are fully backed by the context.
- `_is_supported("Knows Python", "python expert")` returns `False`.
- `pytest tests/unit/test_faithfulness_checker.py` shows the three tests named
  in the issue failing: `test_partial_support_returns_middle_score`,
  `test_multiple_context_chunks`, `test_multiple_claims_varying_support`.

There are three root causes, all in `_is_supported()` / `check()`:

1. **Rigid threshold.** `_is_supported()` returns `True` only when a claim and
   the context share **at least two** non-stopword tokens
   (`len(meaningful_overlap) >= 2`). Short or single-keyword claims can share at
   most one meaningful token with their support, so they are always unsupported.
2. **Punctuation-blind tokenization.** Tokens come from `claim.lower().split()`,
   which keeps punctuation. `"Python,"` and `"JavaScript,"` never match the
   context's `python` / `javascript`, so even multi-skill claims under-count
   their overlap.
3. **Binary, not graded, scoring.** `check()` counts each claim as fully
   supported or not, so a single claim that is partially grounded (e.g. Python
   supported but Kubernetes not) can only score `0.0` or `1.0`, never the
   mid-range value the tests expect.

**Expected vs. actual:** a short, grounded claim should count as supported and
partially grounded feedback should produce a mid-range score. Actual output is
`0.0` for these cases.

### Map

Files I expect to touch:

- `rag/evaluator/faithfulness_checker.py` — primary fix. Specifically
  `FaithfulnessChecker._is_supported()` (threshold + tokenization) and
  `FaithfulnessChecker.check()` (graded per-claim scoring). May add a small
  private tokenizer helper (e.g. `_tokenize()`) and reuse it in both places.
- `tests/unit/test_faithfulness_checker.py` — verify the three target tests pass;
  possibly add a couple of cases for short-claim support and comma-separated
  skills.
- `tests/unit/test_issue_152_reproduction.py` — reproduction tests added this
  week; they should go green once the fix lands.

Not in scope: `test_none_context_chunk_text` fails too, but that is the
`text: None` crash tracked separately as issue #153, not #152.

### Plan

1. **Normalize tokenization.** Add a helper that lowercases and extracts word
   tokens with a regex (`re.findall(r"[a-z0-9]+", text)`), then removes
   stopwords. Use it for both claim and context so `"Python,"` matches `python`.
2. **Make support length-aware.** Replace the fixed `>= 2` rule in
   `_is_supported()` with a rule that scales to claim length — a claim counts as
   supported when a sufficient share of its meaningful tokens appear in the
   context, with a floor so a 1–2 keyword claim can still be supported. Keep the
   `bool` return type for direct callers.
3. **Grade the score in `check()`.** Compute a per-claim support ratio (fraction
   of meaningful claim tokens found in the context) and average across claims, so
   partially grounded feedback lands in the middle of the range instead of
   snapping to 0.0/1.0.
4. **Reconcile the two paths.** Tune the threshold and ratio so both the direct
   `_is_supported()` True/False tests and the `check()` score-range tests pass
   together, then run `make test-unit` and `make check` (ruff + black + mypy).

### Inputs & outputs

- **Input:** `check(feedback: str, context_chunks: list[dict])` where each chunk
  has a `"text"` string; `_is_supported(claim: str, context: str)`.
- **Output:** `check()` returns a `float` faithfulness score in `[0.0, 1.0]`
  (ratio of supported/grounded claims). `_is_supported()` returns `bool`.
- **Change:** internal scoring/threshold logic only. No public signatures change,
  no new dependencies, no API/DB changes.

### Risks & unknowns

- **Threshold tension.** The direct `_is_supported()` tests constrain the
  threshold (e.g. `test_specialized_technical_terms` must be `True`,
  `test_is_supported_without_keywords` must be `False`) while the `check()`
  range tests constrain the graded scoring (a single partially-grounded claim
  must land in `0.2–0.8`). Finding one formula that satisfies both is the main
  unknown; I'll iterate against the full test file.
- **Regression risk from tokenization.** Stripping punctuation changes overlap
  counts for currently passing tests (e.g. `test_feedback_fully_supported_by_context`,
  `test_common_words_filtered_in_overlap`); I must re-run the whole file, not
  just the three targets.
- **Stopword list.** The current stopword set is small; comma-joined lists and
  words like "has"/"with" may need handling to avoid inflating overlap.
- **Scope boundary.** Whether to also add a one-line `None` guard for the #153
  crash or leave it to that issue's owner — leaning toward leaving it out to keep
  the PR focused on #152.

### Edge cases

- Short claims with a single meaningful token ("Knows Python.").
- Comma/"and"-separated skills ("Python, JavaScript, and Docker experience").
- Fully unsupported feedback — must stay near `0.0` (don't over-credit).
- Fully supported feedback — must stay near `1.0` (don't under-credit).
- Case-insensitive matching and repeated tokens.
- Empty feedback or empty context — keep returning `0.0`.
- Context chunk missing the `"text"` key — keep handling gracefully.
- Very long feedback/context — keep runtime reasonable (set-based overlap).
