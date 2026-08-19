# Level 0: flat library

Level 0 keeps a small, low-risk set prompt-visible. There is no router or search
layer: the host receives the eligible skill metadata and may activate either
leaf directly.

This baseline is appropriate only while measured context cost, collisions,
task success, and maintenance remain within the library's configured budgets.
The absence of a router is intentional, not an incomplete generated artifact.

Expected state path:

```text
installed/cache -> registered -> eligible -> prompt-visible -> activated
```
