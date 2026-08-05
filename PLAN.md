## Solution plan

**Issue:** [#152 — Faithfulness checker can never mark short claims as supported](https://github.com/ascherj/pathreview/issues/152)

**Branch:** `fix/152-faithfulness-checker-can-never-mark-short-claims-as-supported`
**Reproduction commit:** `0eb6989`

---

### Understand

**Expected:** a short claim that the retrieved context plainly supports (e.g. `"Knows Python"`
against `"The candidate knows Python."`) should score 1.0.

**Actual:** it scores 0.0. Some short claims score 0.5, which is neither correct nor an honest
failure.

The issue text points at the overlap threshold, but reproduction found **three independent
causes**, all in `rag/evaluator/faithfulness_checker.py`:

**1. Tokenization ignores punctuation (lines 78–79).**
`_is_supported` builds token sets with bare `.split()`, which splits on whitespace only.
`"The candidate knows Python."` tokenizes to `{the, candidate, knows, python.}` — period
attached — so `python` never matches `python.`. A claim that is *verbatim* in the context
scores 0.0 because of one character.

Punctuation appears on the **claim** side too: `"Python, JavaScript, and Docker"` yields
`python,` and `javascript,`. Any fix must therefore normalize **both sides symmetrically**.
Verified: stripping only the context side leaves the repo's own `test_multiple_context_chunks`
still failing (`n=1`); stripping both sides gives `n=3`.

**2. The support threshold is an absolute constant (line 88).**
`len(meaningful_overlap) >= 2` ignores claim length. A two-token claim must match *100%* of its
tokens; a claim with one meaningful token can never be supported at all. Meanwhile a long claim
gets many chances to hit two matches incidentally — so the same constant causes false negatives
on short claims and false positives on long ones.

**3. Claims are filtered by character count (line 63).**
`len(s.strip()) > 10` drops any sentence of 10 characters or fewer. `"Uses Rust"` (9 chars) is
discarded while `"Great at Go"` (11 chars) survives — the difference is spelling length, not
substance, and it systematically penalizes short technology names (Go, Rust, C, R, SQL). Worse,
a dropped claim does not score 0; if *all* claims are dropped, `check()` returns the 0.5 neutral
default (line 31), silently reporting "half faithful" for something it never evaluated.

**Corroboration:** on an unmodified tree, `tests/unit/test_faithfulness_checker.py` already has
4 failures, and 3 are this bug — `test_partial_support_returns_middle_score`,
`test_multiple_context_chunks`, `test_multiple_claims_varying_support`. These were written by
the maintainer and encode the intended behaviour, so they are the primary acceptance criteria.

---

### Map

**Files I expect to touch:**

| File | Change |
|---|---|
| `rag/evaluator/faithfulness_checker.py` | The fix. All three causes live here. |
| `tests/unit/test_faithfulness_short_claims.py` | Added in `0eb6989`; adjust the two contested cases (see Risks). |
| `tests/unit/test_faithfulness_checker.py` | **Unplanned.** One `xfail` marker — see Risk 4. |

**Functions involved (all in `FaithfulnessChecker`):**

- `_extract_claims` (lines 51–64) — cause 3, the character-count filter
- `_is_supported` (lines 66–88) — causes 1 and 2, tokenization and threshold
- `check` (lines 12–49) — no logic change; extend logging only

**Files I expect NOT to touch:**

- `rag/evaluator/eval_suite.py` — consumes the score via `.check()`; signature unchanged
- `scripts/run_evals.py` — still a `TODO` stub, so there are no recorded baselines to invalidate
- `core/`, `api/` — `grep` finds no importers of `EvalSuite` outside `rag/evaluator/`, so this
  score is not currently gating any user-facing path. Blast radius is limited to the evaluator
  and its tests.

---

### Plan

**Tier 1 — the fix (justified by tests the maintainer wrote):**

1. **Add a shared `_tokenize(text) -> set[str]` helper.** Lowercase, whitespace split, strip
   *edge* punctuation only (`.,;:!?()[]"'`), drop stop words and empties. Call it identically on
   claim and context.
   *Edge-only* is the critical detail: `re.findall(r'[a-z0-9]+', ...)` would shatter `C++` and
   `C#` both into `c` (making them match each other), split `Node.js` into `node`+`js`, and
   `CI/CD` into `ci`+`cd`. Verified: edge-stripping preserves all of these while still fixing
   `Python.` → `python`. Hoisting the stop-word set to a module constant also stops it being
   rebuilt on every call.

2. **Replace the character filter with a word count.** `len(s.strip()) > 10` becomes
   `len(t.split()) >= 2`. Keeps `"Uses Rust"`, still drops `"Nope"` and empty split artifacts.
   Fold the triple `s.strip()` evaluation into a single walrus binding.

3. **Replace the absolute threshold with a proportional one.** `len(overlap) >= 2` becomes
   `len(overlap) / len(claim_tokens) >= 0.3`. **Added during implementation** — see Risk 1, whose
   original premise turned out to be false.

4. **Make discarded input visible.** Log the pre-truncation claim count and the number of
   fragments dropped. Currently `claims_count` is logged *after* `claims[:10]`, so it caps at 10
   and truncation is invisible in the logs.

5. **Verify against the maintainer's tests, not just mine.** Success = the 3 pre-existing
   failures in `test_faithfulness_checker.py` go green, the 3 guardrails in
   `test_faithfulness_short_claims.py::TestExistingBehaviourPreserved` stay green, and no
   currently-passing test regresses.

**Deliberately out of scope** — recorded so the omission is a decision, not an oversight:

- `claims[:10]` truncation (see Risk 3)
- `test_none_context_chunk_text` — a real `TypeError` crash on `{"text": None}`, but a separate
  robustness bug. Worth its own issue.
- Negation / semantic faithfulness (see Risk 2)

---

### Inputs & outputs

**Input (unchanged):** `check(feedback: str, context_chunks: list[dict]) -> float`, where each
chunk is expected to carry a `"text"` key.

**Output (unchanged):** a float in `[0.0, 1.0]` — the fraction of extracted claims judged
supported. No signature, return type, or range change, so `EvalSuite` needs no modification.

**What changes is the value.** Scores move *upward only*: normalization can add token matches,
never remove them, and the relaxed claim filter admits claims that were previously invisible.
Concretely, `"Knows Python"` vs `"The candidate knows Python."` goes 0.0 → 1.0.

**Internal contract introduced:** claim and context always pass through the same tokenizer; edge
punctuation is removed, interior punctuation is preserved. This is the invariant to state in the
PR — it is testable, and it explains *why* `test_multiple_context_chunks` starts passing.

---

### Risks & unknowns

**1. ~~The threshold change is a judgment call, not a bug fix — and I am not making it yet.~~
RESOLVED DURING IMPLEMENTATION — the premise below was wrong; I adopted ratio `0.3`.**

> **Correction.** This section argued for deferral on the grounds that *"no maintainer test
> demands it."* That is false. `test_multiple_claims_varying_support` — feedback
> `"Python expert. Knows Rust. Skilled with Docker."` against a context naming Python and Docker
> — expects two of three claims supported, and **both supported claims overlap on exactly one
> token**. Under `>= 2` it scores 0.0 and the test stays red no matter how good the tokenizer is.
> My 10-case table below classified this as a case `>= 2` passes; re-deriving the token sets by
> hand shows it does not. The error was in my labelling, not in the measurement.
>
> With that corrected, the choice was not "adopt my opinion or wait" but "satisfy a maintainer
> test or ship a red one". Re-measured, the window of ratios that satisfies **every** test in the
> suite is `(0.17, 0.33]`:
>
> | claim / context | ratio | required |
> |---|---|---|
> | `expert in Rust systems programming` / Python+JS context | 0.17 | unsupported |
> | `Skilled with Docker` / Python+Docker context | 0.33 | supported |
> | `strong Python skills … Django` / Python+Django context | 0.38 | supported |
>
> `0.3` sits inside that window with margin on both sides. The two tests I had marked `xfail`
> were awaiting exactly this decision, so their markers are gone and they now pass as ordinary
> tests. The overfitting concern below still stands as a caveat — the window is narrow and
> derived from a small suite — so the ratio is a named module constant (`_SUPPORT_RATIO`) with
> the window recorded in a comment, not an inline literal.
>
> **Still true and unchanged:** loosening the threshold moves a safety metric toward false
> positives. See Risk 2 — this PR fixes false negatives only.

*Original reasoning, retained:*

Measured against 10 labelled cases (the repo's own tests plus the #152 cases), with tokenization
fixed but the threshold varied:

| Rule | Result |
|---|---|
| `>= 2` (unchanged) | **8/10** — fails only the two cases I invented |
| proportional, ratio 0.5 | 9/10 — breaks `repo: long supported` |
| proportional, ratio 0.4 | 9/10 — breaks `repo: long supported` |
| proportional, ratio 0.34 / 0.3 / 0.25 | 10/10 |
| `min(2, len(claim_tokens))` | 8/10 |

The tokenizer fix alone satisfies **every case the maintainer's tests demand**. The only two
still failing are `#152 paraphrase` (`"Knows Python"` vs `"proficient in Python"`) and
`#152 one-token` — both of which assert *my* opinion that one keyword match should ground a
two-word claim. That is a design decision the maintainer may reasonably reject.

Three different ratios fit all ten cases equally well, on a set I wrote myself — that is
overfitting, not validation. And loosening the threshold pushes a safety metric toward false
positives, the more expensive direction.

~~**Action:** mark those two tests `xfail(strict=False)` and ask on the issue: *should
`"Knows Python"` count as supported when the context says `"proficient in Python"`?* Adopt a
ratio only if the answer is yes, using their number.~~ — superseded by the correction above. The
question is still worth asking on the issue, but as a request to confirm `0.3`, not as a blocker.

**2. This fix does not reduce false positives, and the PR must not claim it does.**
Token overlap cannot detect negation. Verified — all three score **1.0** today, and still will
after Tier 1:

| claim | context |
|---|---|
| "The candidate has production Kubernetes experience" | "The candidate has **no** Kubernetes experience whatsoever." |
| "Tests are comprehensive" | "Tests are comprehensive **nowhere**; coverage is 4%." |
| "The project is well documented" | "The project is **poorly** documented" |

There is already a maintainer test for this — `test_common_words_filtered_in_overlap`
(line 210) — with no `assert` and the comment *"This depends on implementation."* Someone knew.
Fixing it means NLI or an LLM judge, i.e. a rewrite, not this PR. Tier 1 fixes false
**negatives** only.

**3. `claims[:10]` — observed, not addressed.** With `max_tokens: 2000`
(`rag/generator/review_generator.py:21`) a review can run 75–100 sentences, but only the first
10 are scored — truncation, not sampling, so it is biased toward the opening, where LLM reviews
are most hedged and least checkable. Demonstrated: appending **100 fabricated sentences** to
supported feedback leaves the score at **1.00**. Unfaithful content is free after sentence 10.
Adjacent to #152 and in the same method, but a scoring-semantics question rather than a
token-matching one. Filing as a follow-up issue rather than widening this PR.

**4. `test_partial_support_returns_middle_score` is unsatisfiable as written — found during
implementation.** I listed it as one of the three pre-existing failures the fix would turn green.
It will not, and no threshold can make it:

```
feedback = "The developer shows Python expertise and Kubernetes knowledge."   # ONE sentence
assert 0.2 < score < 0.8
```

`check()` returns `supported / len(claims)`. One sentence means one claim, so the score is
exactly `0.0` or `1.0` — it can never land strictly inside `(0.2, 0.8)`. Partial credit would not
rescue it either: the claim overlaps the context on 1 of 6 meaningful tokens (`python`), so a
ratio-valued score would be `0.17`, still under the lower bound. The fixture needs a second
sentence, or the assertion needs to be a set-membership check.

This is a test bug, not a symptom of #152. **Action:** `xfail(strict=False)` with the arithmetic
recorded in the reason, and raise it on the issue — rewriting a maintainer's assertion to make my
PR green is not my call.

**5. Unresolved before I write code:**
- ~~Which characters belong in the strip set.~~ **Decided:** the ASCII list plus the unicode
  characters LLM output routinely emits — curly quotes, en/em dashes, ellipsis. Edge-stripping
  them cannot damage a token, since none of them are interior to a real identifier.
- Hyphenated compounds. `"art"` vs `"state-of-the-art"` stays a false negative under
  edge-stripping — the compound remains one token. Substring matching would catch it, but only
  by also matching `rust` inside `trusted` (7 false positives across 8 negative cases when
  tested). Accepting the false negative.
- Whether the 17-word stop list is adequate. `has`, `with`, `this`, `their` are all absent and
  all contribute meaningless overlap.

---

### Edge cases

Handled today and must not regress:

| Input | Current behaviour | After fix |
|---|---|---|
| `feedback=""` | 0.0 | unchanged |
| `context_chunks=[]` | 0.0 | unchanged |
| both empty | 0.0 | unchanged |
| chunk missing `"text"` key | `.get("text", "")` → 0.0 | unchanged |
| context of 1000 repeated words | set dedups to 1 token | unchanged |
| feedback of 100+ sentences | capped at 10 claims | unchanged (see Risk 3) |
| same input twice | deterministic | unchanged |

New or newly relevant:

| Input | Required behaviour |
|---|---|
| `{"text": None}` | **Currently raises `TypeError`** (line 34). Out of scope — separate issue. |
| Claim that is only punctuation (`"..."`) | Tokenizes to empty set → unsupported, not a crash |
| Claim that is only stop words | Unsupported — guardrail test exists |
| Single-word claim (`"Nope"`) | Dropped by the word-count filter |
| No claims survive extraction | Returns 0.5 neutral — must be **logged**, since it is otherwise indistinguishable from a genuine 0.5 score |
| Tech tokens: `C++`, `C#`, `Node.js`, `CI/CD`, `k8s`, `3.11` | Survive tokenization intact |
| Mixed case, tabs, newlines, repeated spaces | Normalized identically on both sides |
