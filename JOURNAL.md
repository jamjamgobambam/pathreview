## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/153]

**Issue title:** [Faithfulness checker crashes when a context chunk has text: None]

**Tier:** [X ] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[The faithfulness checker was failing when processing context chunks that have a null or 'None' text value causing uncached crash during execution. This happens when the string operation are attempted on a non-string object in the evaluation pipline. fixing this requires adding a check or fallback to handle 'None' values befor processing the text chunk.]

**Branch name:** [fix/153-faithfulness-checker-none-crash]

**Setup confirmation:** ['Yes'] App runs locally at localhost:5173

**Cohort ledger:** ['Yes] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

***Reproduction commit link:*** [https://github.com/Mohammed-Jemal/pathreview.git
   697e058..7070ad7]

***Reproduction summary:*** Reproduced issue #153 by running `pytest tests/unit/test_faithfulness_checker.py`. The test `test_none_context_chunk_text` failed with `TypeError: sequence item 0: expected str instance, NoneType found` when passing `context_chunks = [{"text": None}]`.

***PLAN.md link:*** [https://github.com/Mohammed-Jemal/pathreview/blob/fix/153-faithfulness-checker-none-crash/PLAN.md]


***Blockers or open questions:***[I don't have question by now]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[Implemented defensive check '(chunk.get("text") or "")' in 'rag/evaluator/faithfulness_checker.py]' to prevent 'TypeError' when context chunks contain 'None' text values. verified that 'test_none_context_chunk_text' in tests/unit/test_faithfulness_checker.py' now passed.

**Next steps:**
[Run full project checks ('make check', make test_unit'), create a pull request against the main repository, and get peer feedback].

**Blockers:**
[first time i was expecting all the test to pass, but learned that was another bug that isn't related to fix/153. ]

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [fix/153-faithfulness-checker-none-crash]

**What you built:**
[Updated the context chunk text extraction in 'Faithfulnesschecker' to fall back to an string like ('""') whenever a chunk text field is explicityly set to 'None'. This prevents a TypeError error during joining the chunks]

**Tests added or updated:**
[tests/unit/test_faithfulness_checker.py, verified and the test_none_context_chunk_text' passed]

**Self-review confirmation:** [X ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** ["none"]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [ X ] No — still awaiting review

**Summary of feedback:**
[Until now reviewer feedback was not received.]

**How you responded:**
[ ]

---

### Reflection

**What was harder than you expected?**
[Tracing the dict.get('text',"") that means when the code behave explicitly 'None values were passed vs missing keys was more subtle than expected. Also identifying the testing/pytest code was harder to reproduce the and confirm bug] 

**What did you learn about working in a large codebase?**
[Working in a production style repository taught me how to navigate with different files and understanding the code, then handling the defencive check so refactoring does not break dependent evaluation piplines]

**How did AI tools help — and where did they fall short?**
[AI tools were great for quick isolation and used more to understand some logic in the code and mainly when i set up the requirement AI guide me step by step.]

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change? I might not go that much differently but for sure i select the issue first and then reproduce the bug, before i start implementation, to make sure the issue is correct. based on the output, i will dive directly into that file and understand the logic and some other related code.]

**What are you most proud of from this module?**
[I am most proud of understanding the logic and how I successfully pull request  and handled edge case, finally documenting the entire 4 week step by step development process ]