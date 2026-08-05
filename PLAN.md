# Solution plan

**Issue:** [Bias detector patterns are too narrow to match common phrasings](https://github.com/ascherj/pathreview/issues/151)

## Understand

> What is the root cause of this issue? What behavior is expected vs. actual?

The root cause is that `bias_detector` performs an exact-sequence check on the
passed phrase — it only flags bias when the word sequence matches the keywords in
a pattern phrase, which is not an effective approach. The expected behavior is
that the bias detector can detect biased phrases *without* requiring the exact
phrase, such as "bootcamp graduates lack rigor." Currently, it cannot detect bias
in phrases that carry a similar meaning — for example: "The candidate only
attended a bootcamp, so this project lacks the rigor of a formal CS education."

## Map

> Which files, functions, or modules are involved? List the specific files you
> expect to touch.

- `safety/bias_detector.py` — the `BiasDetector` class and its `detect_bias` method.
- `tests/unit/test_bias_detector.py` — the unit tests that use the class and method.

Both are involved because the tests rely on the definition and function from the
`BiasDetector` class.

## Plan

> What are the steps to fix this issue? Break it into 3–5 concrete sub-tasks.

**Solution:** Replace the rigid phrase-regexes with a subject + negative-predicate
co-occurrence check.

### Step 1 — Build three vocabulary lists from the failing tests

Turn the failing-test inputs into keyword lists instead of full phrases. For example:

- **Educational subjects:** bootcamp, coding bootcamp, self-taught, online course,
  graduates, developers, programmers, education, attendance
- **Demographic subjects:** young, old, aged, immigrant, international, foreign,
  from poor / rich / working-class background
- **Negative predicates:** can't / cannot / won't / will not, struggle,
  lack / lacks / missing, insufficient / inadequate, not equal / comparable,
  means inadequate

Keep the subjects split into lists because the reason string differs per
category (see Step 3).

### Step 2 — Rewrite `detect_bias` to check co-occurrence, not sequence

Lowercase the text once, then:

- If a **demographic subject** AND a **negative predicate** both appear →
  return `(True, "Demographic assumptions detected")`.
- Else if an **educational subject** AND a **negative predicate** both appear →
  return `(True, "Dismissive language about educational background")`.
- Else → return `(False, "")`.

This drops the requirement that words sit in an exact order. Keep the
`tuple[bool, str]` signature and both existing reason strings unchanged.

### Step 3 — Protect against false positives

The 6 "not flagged" tests act as guardrails. The critical design rule that keeps
them passing: predicates must be negative verbs/adjectives, never object nouns.
For example, "fundamentals" must NOT be a trigger word — otherwise "your bootcamp
background shows strong fundamentals" would be wrongly flagged. The signal is
`bootcamp` + `lack` co-occurring, not the noun alone. This correctly keeps clean,
neutral, and balanced mentions unflagged:

- "bootcamp project demonstrates good practices" → subject present, no negative predicate → not flagged
- "resume shows bootcamp attendance" → factual, no predicate → not flagged
- "bootcamp attendance means inadequate training" → subject + predicate → flagged

### Step 4 — Verify against the full suite until all 32 pass

Run `tests/unit/test_bias_detector.py`. Target: the 9 failing tests pass and the
23 that already pass stay green (especially the "not flagged" guardrails).
Iterate on the word lists if any regress. Also keep emitting the
`logger.warning("bias_detected", ...)` event so `safety/monitoring.py` monitoring
stays intact.

## Inputs & outputs

> What does your fix take as input? What should it produce or change?

My fix still takes a text string as input and produces a 2-tuple
`(is_biased, reason)` as output. Only the internal detection logic changes — it
replaces the rigid `DISMISSIVE_PATTERNS` / `DEMOGRAPHIC_PATTERNS` sequence regexes
with a co-occurrence check over three keyword lists (educational subjects,
demographic subjects, and negative predicates) to evaluate whether the keyword
combination signals bias.

## Risks & unknowns

> What could go wrong? What are you still unsure about?

It's possible the three keyword lists are not comprehensive enough, which could
produce an incorrect evaluation, since users may provide topics outside of the
keyword lists.

## Edge cases

> What inputs or states should your fix handle gracefully?

My fix should handle the following cases gracefully:

- When no input text is provided.
- When topics unrelated to education are provided.
- When there are typos in the provided text.
