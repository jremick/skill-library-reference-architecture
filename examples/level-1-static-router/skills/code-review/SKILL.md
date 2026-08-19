---
name: code-review
description: Review a supplied code change for correctness, safety, and missing tests without modifying or deploying it. Use when the requested outcome is findings.
license: Apache-2.0
---

# Code review

Review only the supplied change and the directly affected contracts, callers,
and tests available in the task context.

1. Establish the intended behavior before judging the implementation.
2. Look for reproducible correctness, data-loss, security, and reliability
   failures.
3. Check whether tests cover the behavior that matters, including negative and
   boundary cases.
4. Report actionable findings in severity order with precise locations.
5. Separate verified defects from risks that need more evidence.

Do not edit, deploy, merge, or publish. If no actionable defect is found, say so
and list any material verification that was unavailable.
