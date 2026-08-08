# Plan for Issue #153 — Faithfulness checker crashes when a context chunk has text: None

## Problem

The faithfulness evaluation path crashes when a context chunk is provided as a dictionary with an explicit text value of None.

The failure occurs in FaithfulnessChecker.check() before any scoring begins. The original context aggregation line:

    " ".join([chunk.get("text", "") for chunk in context_chunks])

returns None when the key "text" exists but holds a None value. Passing that None into " ".join(...) raises:

    TypeError: sequence item 0: expected str instance, NoneType found

## Goal

- Eliminate the crash for context chunks containing {"text": None}.
- Preserve identical faithfulness scoring behavior for all previously valid inputs.
- Keep the change minimal and localized to the evaluator boundary.
- Add explicit regression coverage so the issue cannot reappear.

## Approach

1. Reproduce
   Confirm the exact failure with:

       FaithfulnessChecker().check("Knows Python.", [{"text": None}])

2. Normalize defensively
   Update the text extraction in FaithfulnessChecker.check() from:

       chunk.get("text", "")

   to:

       (chunk.get("text") or "")

   so both missing keys and explicit None values are safely coerced to empty strings.

3. Add regression test
   Extend tests/unit/test_faithfulness_checker.py with a focused test that passes a context list containing {"text": None} and asserts:
   - the call completes without raising TypeError
   - a valid faithfulness result is still returned

4. Verify
   Run the relevant unit tests and confirm no regressions were introduced.

## Edge cases now handled

Input: {"text": "valid content"}
Old Behavior: Works
New Behavior: Works (unchanged)

Input: {"text": None}
Old Behavior: Crashes with TypeError
New Behavior: Treated as empty string

Input: {} (missing key)
Old Behavior: Treated as empty string
New Behavior: Treated as empty string

Input: {"text": ""}
Old Behavior: Treated as empty string
New Behavior: Treated as empty string

Input: Mixed list (some None, some valid)
Old Behavior: Crashes on first None
New Behavior: Safely joins only the valid text

## Why this approach

The evaluator is the narrow boundary where retrieved context becomes input for scoring. Performing the coercion there is the smallest possible change that:

- Protects every caller
- Leaves the core faithfulness logic completely untouched
- Makes the pipeline resilient to malformed upstream data without altering intended behavior on valid data