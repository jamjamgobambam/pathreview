## Week 7 — Issue selection

***Issue link:*** https://github.com/ascherj/pathreview/issues/153
***Issue title:*** Faithfulness checker crashes when a context chunk has text: None
***Tier:*** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

***Problem summary:***
The faithfulness checker component crashes when evaluating retrieved context chunks if a chunk's text field is set to `None`. When iterating through context chunks, the checker attempts string operations directly without first validating whether the text attribute contains a non-null string value. A successful fix will add defensive checks or fallback handling to handle `None` values gracefully, preventing runtime exceptions during evaluation in the RAG pipeline.

***Branch name:*** fix/153-faithfulness-checker-null-chunk-text
***Setup confirmation:*** [x] App runs locally at localhost:5173
***Cohort ledger:*** [x] Issue added to cohort ledger