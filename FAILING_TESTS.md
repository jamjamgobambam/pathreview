# Failing Unit Tests Summary

**Command:** `make test-unit` (`pytest tests/unit -m unit`)
**Date:** 2026-07-22
**Result:** **53 failed, 375 passed** (428 collected)

Failures are grouped by module below, with the assertion/error and the likely root cause.

---

## `test_review_service.py` — 13 failures (largest cluster)

All fail with `AttributeError: 'coroutine' object has no attribute 'first'` / `'all'` at
[core/services/review_service.py:47](core/services/review_service.py#L47) and [:65](core/services/review_service.py#L65).

**Root cause:** a DB `execute()` result is used without `await` — the coroutine is never awaited before `.first()` / `.all()` is called (async/await bug in the service, not the tests).

- `test_get_review_returns_review_for_correct_owner`
- `test_get_review_returns_none_for_wrong_user`
- `test_get_review_with_valid_uuid`
- `test_get_review_verifies_ownership`
- `test_get_review_uses_select_and_join`
- `test_list_reviews_returns_paginated_results`
- `test_list_reviews_page_2_returns_correct_offset`
- `test_list_reviews_returns_tuple`
- `test_list_reviews_default_pagination`
- `test_list_reviews_custom_page_size`
- `test_list_reviews_counts_total`
- `test_list_reviews_returns_reviews_list`
- `test_list_reviews_ordered_by_created_at`

---

## `test_bias_detector.py` — 9 failures

All assert `False is True` — the detector is not flagging text it should. Bias/assumption
detection appears to be returning no matches.

- `test_dismissive_bootcamp_language_detected`
- `test_bootcamp_lacks_rigor_detected`
- `test_demographic_assumption_age_detected`
- `test_coding_bootcamp_variant`
- `test_developer_vs_programmer_distinction`
- `test_multiple_bias_indicators`
- `test_negative_educational_claim`
- `test_rich_poor_assumption`
- `test_assumption_vs_observation`

---

## `test_pii_scrubber.py` — 5 failures

**Root cause:** US phone numbers are not being redacted (`'[REDACTED]' in 'Call me at (555) 123-4567'` fails). The phone-number regex/pattern is missing or not matching.

- `test_us_phone_number_redaction`
- `test_us_phone_formats`
- `test_detect_phone_pii` — `assert 0 > 0` (no PII detected)
- `test_phone_at_start_of_text`
- `test_mixed_pii_and_text` — `'Python'` missing because phone text was partially mangled (`for [REDACTED]ications`)

---

## `test_resume_parser.py` — 5 failures

Parser returns empty/incorrect structure.

- `test_parse_single_column_resume_text` — `assert (False or False)`
- `test_parse_resume_no_work_experience` — `assert False`
- `test_parse_markdown_resume` — markdown `#` not stripped (`'#' not in ...` fails)
- `test_detect_sections` — `assert 0 > 0` (no sections detected)
- `test_strip_markdown_syntax` — `assert not True`

---

## `test_skill_extractor.py` — 5 failures

- `test_text_with_typescript_files` — `assert False`
- `test_javascript_detection` — `assert False`
- `test_devops_tool_detection` — `assert False`
- `test_docker_compose_detection` — `assert False`
- `test_database_technology_detection` — `UnboundLocalError: cannot access local variable 'skill_names'` at [test_skill_extractor.py:138](tests/unit/test_skill_extractor.py#L138) (variable used before assignment)

---

## `test_faithfulness_checker.py` — 4 failures

- `test_partial_support_returns_middle_score` — `assert 0.2 < 0.0` (score is 0.0 when a middle value expected)
- `test_multiple_claims_varying_support` — `assert 0.2 < 0.0`
- `test_multiple_context_chunks` — `assert 0.0 > 0.5`
- `test_none_context_chunk_text` — `TypeError: sequence item 0: expected str instance, NoneType found` at [rag/evaluator/faithfulness_checker.py:34](rag/evaluator/faithfulness_checker.py#L34) (a `None` context chunk is joined without a guard)

---

## `test_readme_parser.py` — 2 failures

Both `assert 0 > 0` — parser extracts nothing.

- `test_parse_standard_readme`
- `test_extract_heading_hierarchy`

---

## `test_tech_detector.py` — 2 failures

Both `assert 'JavaScript' == 'Python'` — excluded directories are still being scanned, so `node_modules`/build artifacts skew the detected primary language.

- `test_node_modules_excluded`
- `test_build_directory_excluded`

---

## Single-failure modules — 6 failures

| Test | Error | Likely cause |
|------|-------|--------------|
| `test_batch_processor.py::test_empty_chunks_list_returns_empty` | `assert ('Empty chunks list' in '' ...)` | expected log/message not emitted for empty input |
| `test_keyword_search.py::test_empty_index` | `ZeroDivisionError: division by zero` | no guard for empty index (division by doc count) |
| `test_output_parser.py::test_json_array_fallback` | `AttributeError: 'list' object has no attribute 'items'` at [rag/generator/output_parser.py:64](rag/generator/output_parser.py#L64) | code assumes a dict but got a JSON array |
| `test_prompt_defense.py::test_whitespace_variations_detected` | `assert False is True` | whitespace-obfuscated injection not detected |
| `test_readme_scorer.py::test_readme_with_all_quality_signals` | `assert 51 > 100` | scoring caps/weights produce too low a score |
| `test_relevance_scorer.py::test_query_with_partial_overlap` | `assert 1.0 < 0.9` | partial overlap scored as perfect (1.0) |
| `test_resume_parser` (counted above) | — | — |
| `test_security.py::test_verify_with_wrong_hash_format` | `passlib.exc.UnknownHashError: hash could not be identified` | wrong-format hash not caught/handled gracefully |
| `test_structural_chunker.py::test_document_with_no_headings` | `assert 0 >= 1` | headingless docs produce 0 chunks (the branch issue #149) |

---

## Notes / themes

1. **`review_service` async bug** accounts for 13 of 53 failures — a single missing `await` fix likely clears the whole cluster.
2. **PII phone redaction** (5) and **bias detection** (9) look like missing/broken pattern matching.
3. **`structural_chunker` headingless docs** matches the current branch `fix/149-structural-chunker-drops-headingless-docs` — this is the issue under active work.
4. A `KeyError: '__import__'` appears in captured output (prompt-defense sandbox eval) but is trapped, not a test failure.
