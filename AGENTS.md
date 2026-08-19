# Repository instructions

Version: 0.1.0
Last updated: 2026-08-20

## Purpose

This repository defines a tool-agnostic reference architecture for scalable AI
skill libraries. Keep every example synthetic and portable. Do not copy private
agent configuration, machine paths, integrations, prompts, task identifiers,
credentials, or environment inventories into this repository.

## Sources of truth

- `spec/` defines normative contracts and terminology.
- `schemas/` contains machine-readable representations of those contracts.
- `governance/promotion-policy.yaml` is a non-executable reference checklist
  for configurable architecture-level promotion and rollback gates.
- `examples/` contains synthetic conformance fixtures.
- `src/skillref/` implements deterministic validation and compilation.
- Generated files must name their source digest and must not become a second
  hand-edited source of truth.

## Required invariants

- Keep installed/cache, registered, eligible, prompt-visible,
  router-retrievable, inspected, activated, and conditionally loaded states
  distinct.
- Apply supported profile, lifecycle, and permission denials before search or
  model ranking. Trust and compatibility gates require verified adapter inputs.
- Use deterministic code for schemas, exact routing, permissions, state
  transitions, digests, compilation, redaction, and any implemented gates.
- Use model judgment only for semantic interpretation, ranking, overlap review,
  and qualitative evaluation.
- Never claim that lower token use proves better outcomes. Compare task success,
  verification, corrections, latency, and privacy against a simpler baseline.
- Treat vendor-specific syntax as an adapter, not as a portable core contract.

## Development

```bash
uv sync --locked
uv run skillref validate .
uv run python -m unittest discover -s tests -v
```

Run `uv run skillref check-public-surface .` before publication-related changes.
Run `git diff --check` before committing.

## Change discipline

- Keep changes scoped to the affected contract, implementation, tests, and
  documentation.
- Add or update negative tests for policy, privacy, conflict, and lifecycle
  boundaries.
- Preserve generated evidence on failure; do not rewrite a failed or incomplete
  result as passing.
- Do not describe the reference promotion checklist as an executable gate.
- Public visibility, releases, packages, and external publication are separate
  actions requiring an evidence-backed readiness gate.
