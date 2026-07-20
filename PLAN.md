## Problem Summary Statement

**Issue:** #146 — PII scrubber fails to redact parenthesized US phone numbers  
**Component:** Safety Layer (`safety`)

### Problem Overview
The PII (Personally Identifiable Information) scrubbing module in the safety layer currently fails to detect and redact US phone numbers that use parenthesized area codes (e.g., `(123) 456-7890`, `(123)456-7890`, or `+1 (123) 456-7890`). 

Because the existing pattern matcher expects unparenthesized digits separated by standard delimiters (hyphens, dots, or spaces), parenthesized phone numbers pass through the safety pipeline unredacted, exposing raw user contact information.

### Objective
* Update the phone number pattern matching logic in the safety module to recognize parenthesized area codes and flexible spacing.
* Ensure the updated pattern avoids false positives on arbitrary parenthesized text.
* Add dedicated unit tests covering parenthesized phone number formats to prevent regressions.