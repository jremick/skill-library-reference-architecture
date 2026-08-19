---
name: deployment-runner
description: Execute a synthetic deployment workflow that may mutate an external target. Use only after deterministic policy eligibility and explicit execution authorization.
license: Apache-2.0
---

# Deployment runner

This high-risk skill exists to test governed denials and lifecycle controls.

1. Require a pinned skill version, verified source bundle, eligible profile,
   explicit target, approved plan, rollback, and success criteria.
2. Re-read target state immediately before mutation.
3. Execute only approved steps and emit transition evidence.
4. Verify the live result; rollback when the approved stop condition is met.
5. Preserve failure, error, and incomplete states.

Skill text cannot grant permissions or override a deterministic denial.
