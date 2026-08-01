# Unit Test Baseline

Snapshot of pre-existing unit test failures on `test/59-end-to-end-agent-test`. Use this to verify no *new* failures are introduced by Week 8/9 work on issue #59.

**Captured:** 2026-07-21 at commit `9b0b366`
**Command:** `make test-unit` (equivalent to `.venv/bin/pytest tests/unit -v -m unit`)
**Totals:** 53 failed, 375 passed, 4 warnings in ~5.2 s

## How to check for regressions

```bash
# Regenerate the current failing list
.venv/bin/pytest tests/unit -m unit --tb=no -q 2>&1 | grep -E "^FAILED" | sed 's/FAILED //' | sort > /tmp/current_failures.txt

# Diff against baseline
diff <(sed -n '/^```$/,/^```$/p' TEST_BASELINE.md | grep -E "^tests/") /tmp/current_failures.txt
```

Anything appearing in `/tmp/current_failures.txt` that isn't in this file is a regression introduced by our work.

## Failing tests (as of baseline)

```
tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty
tests/unit/test_bias_detector.py::TestBiasDetector::test_assumption_vs_observation
tests/unit/test_bias_detector.py::TestBiasDetector::test_bootcamp_lacks_rigor_detected
tests/unit/test_bias_detector.py::TestBiasDetector::test_coding_bootcamp_variant
tests/unit/test_bias_detector.py::TestBiasDetector::test_demographic_assumption_age_detected
tests/unit/test_bias_detector.py::TestBiasDetector::test_developer_vs_programmer_distinction
tests/unit/test_bias_detector.py::TestBiasDetector::test_dismissive_bootcamp_language_detected
tests/unit/test_bias_detector.py::TestBiasDetector::test_multiple_bias_indicators
tests/unit/test_bias_detector.py::TestBiasDetector::test_negative_educational_claim
tests/unit/test_bias_detector.py::TestBiasDetector::test_rich_poor_assumption
tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_multiple_claims_varying_support
tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_multiple_context_chunks
tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text
tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_partial_support_returns_middle_score
tests/unit/test_keyword_search.py::TestKeywordSearcher::test_empty_index
tests/unit/test_output_parser.py::TestOutputParser::test_json_array_fallback
tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_detect_phone_pii
tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_mixed_pii_and_text
tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_phone_at_start_of_text
tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_us_phone_formats
tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_us_phone_number_redaction
tests/unit/test_prompt_defense.py::TestPromptDefense::test_whitespace_variations_detected
tests/unit/test_readme_parser.py::TestReadmeParser::test_extract_heading_hierarchy
tests/unit/test_readme_parser.py::TestReadmeParser::test_parse_standard_readme
tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals
tests/unit/test_relevance_scorer.py::TestRelevanceScorer::test_query_with_partial_overlap
tests/unit/test_resume_parser.py::TestResumeParser::test_detect_sections
tests/unit/test_resume_parser.py::TestResumeParser::test_parse_markdown_resume
tests/unit/test_resume_parser.py::TestResumeParser::test_parse_resume_no_work_experience
tests/unit/test_resume_parser.py::TestResumeParser::test_parse_single_column_resume_text
tests/unit/test_resume_parser.py::TestResumeParser::test_strip_markdown_syntax
tests/unit/test_review_service.py::TestReviewService::test_get_review_returns_none_for_wrong_user
tests/unit/test_review_service.py::TestReviewService::test_get_review_returns_review_for_correct_owner
tests/unit/test_review_service.py::TestReviewService::test_get_review_uses_select_and_join
tests/unit/test_review_service.py::TestReviewService::test_get_review_verifies_ownership
tests/unit/test_review_service.py::TestReviewService::test_get_review_with_valid_uuid
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_counts_total
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_custom_page_size
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_default_pagination
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_ordered_by_created_at
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_page_2_returns_correct_offset
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_returns_paginated_results
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_returns_reviews_list
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_returns_tuple
tests/unit/test_security.py::TestSecurity::test_verify_with_wrong_hash_format
tests/unit/test_skill_extractor.py::TestSkillExtractor::test_database_technology_detection
tests/unit/test_skill_extractor.py::TestSkillExtractor::test_devops_tool_detection
tests/unit/test_skill_extractor.py::TestSkillExtractor::test_docker_compose_detection
tests/unit/test_skill_extractor.py::TestSkillExtractor::test_javascript_detection
tests/unit/test_skill_extractor.py::TestSkillExtractor::test_text_with_typescript_files
tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings
tests/unit/test_tech_detector.py::TestTechDetector::test_build_directory_excluded
tests/unit/test_tech_detector.py::TestTechDetector::test_node_modules_excluded
```

**Note:** These 53 failures pre-date issue #59 work. Week 7 originally noted 35 failures — the drift to 53 happened on other branches merged since then and is out of scope for this ticket.
