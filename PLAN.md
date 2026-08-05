# Solution Plan

**Issue:** Skill extractor fails to detect JavaScript and TypeScript

**Issue link:** https://github.com/ascherj/pathreview/issues/148

## Understand

The skill extractor currently misses JavaScript and TypeScript when analyzing resume or repository text. The existing implementation relies on a limited set of filename hints and import patterns, causing it to overlook common JavaScript and TypeScript syntax such as `const`, `require()`, `export interface`, and `.tsx` references.

**Expected behavior:**
The extractor should correctly identify JavaScript and TypeScript whenever they are clearly represented in the input while continuing to detect other supported technologies.

**Actual behavior:**
JavaScript and TypeScript are omitted from the extracted skill list even though they appear in the input.

---

## Map

Files I expect to review or modify:

* `ingestion/parsers/skill_extractor.py`
* `tests/unit/test_skill_extractor.py`

I may also inspect any helper functions or configuration files used by the skill extraction logic if necessary.

---

## Plan

1. Review the current JavaScript and TypeScript detection logic in the skill extractor.
2. Identify why common JavaScript and TypeScript syntax is not being recognized.
3. Update the detection patterns to include additional language indicators while avoiding false positives.
4. Run the existing unit tests and verify that JavaScript and TypeScript are detected correctly.
5. Confirm that existing skill detection behavior for other technologies remains unchanged.

---

## Inputs & Outputs

**Input**

Resume or repository text containing technologies such as JavaScript, TypeScript, React, `.js`, `.ts`, `.tsx`, `const`, `require()`, or `export interface`.

**Output**

The extracted skill list should correctly include JavaScript and TypeScript along with any other supported technologies found in the text.

---

## Risks & Unknowns

* Expanding detection patterns may introduce false positives if the matching becomes too broad.
* There may be shared helper functions that also require updates.
* I need to confirm the project's preferred approach for balancing broader detection with precision.

---

## Edge Cases

* Different capitalization (JavaScript, javascript, JAVASCRIPT)
* `.js`, `.ts`, and `.tsx` file references
* Text containing both JavaScript and TypeScript
* Resumes mentioning React together with JavaScript or TypeScript
* Existing detection for other languages and frameworks should continue to work correctly without regression.
