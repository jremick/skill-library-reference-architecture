# Architecture guide

This directory explains the reference architecture for maintainers of AI skill
libraries. The architecture is tool-agnostic: portable contracts live in
`spec/`, machine-readable forms live in `schemas/`, and provider-specific
placement or syntax belongs in `adapters/`.

These pages are explanatory. If explanatory text conflicts with a normative
contract, the contract wins.

The contracts describe responsibilities for a conforming implementation. The
alpha reference CLI implements validation, profile-filtered compilation, and
deterministic routing evaluation for selection, rejection, and exposure. It
does not operate a host lifecycle, load or execute skill resources, attest host
compatibility or trust, collect operational telemetry, evaluate behavioral
outcomes, or make promotion decisions.

## Read this first

- [Overview](overview.md) describes the purpose, boundaries, and evidence model.
- [Architecture levels](levels.md) describes Levels 0 through 3 and the gates
  between them.
- [Context-loading lifecycle](context-loading-lifecycle.md) defines the states
  between installation and verified execution.
- [Contract map](contracts.md) shows how the manifest, registry, router,
  profile, lifecycle, telemetry, and evaluation contracts fit together.
- [Deterministic code and model judgment](deterministic-and-model.md) assigns
  responsibility at each decision boundary.
- [Evidence and sources](evidence-and-sources.md) records the current primary
  sources, inference limits, and project recommendations.

Related guidance:

- [Compatibility](../compatibility.md)
- [Evaluation](../evaluation.md)
- [Migration](../migration.md)
- [Security model](../security-model.md)
- [Diagram index](../diagrams/README.md)

## Core invariants

1. Installed or cached material is not necessarily registered, eligible,
   visible, retrieved, inspected, activated, or loaded.
2. Profile and permission denials are applied before search or model ranking.
   Trust and compatibility denials require adapter-supplied, verified canonical
   attributes; they must not be inferred from unverified metadata.
3. Retrieval is an optimization that must beat a simpler baseline on outcomes,
   not merely on token use.
4. Thresholds are locally configured from measurements. Skill counts and
   context percentages are not universal architecture boundaries.
5. Vendor syntax is an adapter concern, not a portable contract.
