# Contributing

Contributions are welcome during public alpha when they keep the architecture
portable, evidence-led, and safe to inspect publicly.

## Development setup

```bash
uv sync --locked
uv run skillref validate .
uv run python -m unittest discover -s tests -v
```

## Expectations

- Keep examples synthetic. Do not submit private prompts, inventories,
  integrations, credentials, task identifiers, real customer data, or
  machine-specific absolute paths.
- Treat `spec/` and `schemas/` as canonical contracts. The governance policy is
  a non-executable reference checklist. Generated bundles must be reproducible
  and content-bound by digest.
- Apply permission and profile filtering before retrieval or model ranking.
- Add positive and near-miss negative fixtures for routing changes.
- Add deterministic tests for exact policy, lifecycle, parsing, or generation
  changes. Label model-judged evaluation as advisory unless calibrated.
- Document breaking changes to schemas, CLI behavior, adapter assumptions, or
  generated output.
- Update relevant docs and Mermaid sources with architecture changes.

## Pull requests

Explain the problem, the affected contract, verification performed, residual
risk, and rollback path. Small focused changes are easier to review than mixed
refactors.

By submitting a contribution, you agree that it is licensed under Apache-2.0,
the repository's license.
