## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/64](https://github.com/ascherj/pathreview/issues/64)  
**Issue title:** Prompt injection defense doesn't sanitize newline characters in user-supplied resume text  
**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3  

**Problem summary:** The safety module's prompt injection defense mechanism fails to properly sanitize newline characters inside user-submitted resume text before sending context to the LLM. Attackers or unstructured text can use unescaped multiline breaks to break out of system instructions or inject unauthorized prompts. A successful fix will update the sanitization pipeline to escape or strip control characters (like `\n` and `\r`) in resume inputs while preserving semantic document structure, ensuring robust safety guardrails.

**Branch name:** fix/64-prompt-injection-newline-sanitization  
**Setup confirmation:** [X] App runs locally at localhost:5173  
**Cohort ledger:** [X] Issue added to cohort ledger