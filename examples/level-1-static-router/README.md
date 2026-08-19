# Level 1: static routing compiler

Level 1 keeps domain routers prompt-visible while leaves remain behind exact
router targets. The router map is deterministic: every route target must exist,
priority ties fail validation, and no model may override a profile denial.

The two synthetic leaves distinguish data-analysis requests from code-review
requests. A near-miss containing deployment vocabulary still routes to
`code-review` when the user explicitly asks for review rather than execution.

Expected state path:

```text
installed/cache -> registered -> eligible -> router-retrievable
-> exact route -> inspected -> activated
```
