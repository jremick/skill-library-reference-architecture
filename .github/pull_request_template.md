## Summary

Describe the problem, the chosen architecture level, and the smallest change that solves it.

## Validation

- [ ] `uv run skillref validate .`
- [ ] `uv run python -m unittest discover -s tests -v`
- [ ] `uv run skillref check-public-surface .`
- [ ] Documentation and generated diagrams are current.

## Contract and safety review

- [ ] Schema or compatibility changes are identified and versioned.
- [ ] Examples and fixtures are synthetic and contain no private inventories, prompts, secrets, machine paths, or proprietary configuration.
- [ ] Permission, profile, retrieval, and activation boundaries fail closed where required.
- [ ] Security and privacy effects are described, including any new dependency or external data flow.
- [ ] Breaking changes and migration steps are documented.
