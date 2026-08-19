# Level 2: filtered retrieval

Level 2 keeps leaf metadata off-prompt. A deterministic profile filter runs
before search; only eligible records can become candidates. The model may rank
the remaining records, inspect a candidate, and activate an exact version.

The `read-only` profile grants the explanatory `deployment-review` skill and
denies the mutating `deployment-runner`. The runner must be absent from search,
top-k, inspection, and activation—not merely blocked at execution time.

Expected state path:

```text
installed/cache -> registered -> policy-eligible -> router-retrievable
-> retrieved candidate -> inspected -> activated -> optional resource load
```

Search scores and top-k sizes are configured evaluation inputs, not universal
defaults. The same held-out cases should compare this level with Level 1.
