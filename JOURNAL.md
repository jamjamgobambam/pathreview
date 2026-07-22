# Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/153]

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [✓] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
There is a bug that occurs when the faithfulness checker receives a chunk of text, where the text is the key but the value is `None`. The broken behavior stems from `chunk.get("text", "")`​ because it only uses the empty string when the key is missing. However, if the key has the value `None`​, it returns `None`​ but later fails because `" ".join(...)` expects strings. A successful fix should result in the faithfulness checker being able to handle both missing and empty chunk text without crashing and continue with its evaluation.

**Branch name:** [fix/153-faithfulness-none-text]

**Setup confirmation:** [ ] App runs locally at localhost:5173
After opening the cloned repo in Git Bash, I attempted to start the Docker services with, `docker compose up -d`, and received the error message `bash: docker: command not found`. When I opened Docker Desktop directly, it reported that virtualization support was not detected.

**Cohort ledger:** [✓] Issue added to cohort ledger
