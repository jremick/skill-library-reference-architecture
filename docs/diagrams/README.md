# Diagram index

The Mermaid files in `src/` are canonical and human-editable. SVG files in
`rendered/` are generated review artifacts. If a rendered file differs from its
source, regenerate the SVG rather than editing it.
`render-manifest.json` binds each checked-in render to its source bytes so CI
detects stale or swapped output.

| Diagram | Files | Purpose | Text equivalent |
| --- | --- | --- | --- |
| Context-loading lifecycle | [Source](src/context-loading-lifecycle.mmd) · [SVG](rendered/context-loading-lifecycle.svg) | Separates caching, installation, registration, eligibility, visibility/retrieval, inspection, activation, resource loading, execution, and verification. | Cached bytes may become an installed package, which may then be registered by exact manifest digest. A policy-eligible candidate can be visible or retrievable, inspected, conflict-checked, version-pinned, activated, optionally given named resources, executed, verified, and deactivated. Denied or failed transitions remain explicit. |
| Architecture levels | [Source](src/architecture-levels.mmd) · [SVG](rendered/architecture-levels.svg) | Compares the capability added at each level. | Level 0 loads a flat eligible set; Level 1 compiles domain routers; Level 2 filters and retrieves from an off-prompt catalog; Level 3 adds policy, telemetry, evaluation, lifecycle controls, and rollback. Promotion requires local evidence at every gate. |
| Routing decision flow | [Source](src/routing-decision-flow.mmd) · [SVG](rendered/routing-decision-flow.svg) | Shows deterministic and semantic decisions in safe order. | Validation and policy filtering happen before exact routing or semantic search. The model can rank only eligible records. Deterministic conflict, version, and authority checks precede activation. |
| Registry and schema relationships | [Source](src/registry-schema-relationships.mmd) · [SVG](rendered/registry-schema-relationships.svg) | Shows canonical inputs, generated views, runtime records, and evidence. | Schemas validate manifests, the registry, router map, and profile. Those inputs produce content-bound catalog, compiled, and adapter views. Policy constrains activation. Runtime transitions emit redacted telemetry consumed by evaluation and promotion policy. |
| Evaluation loop | [Source](src/evaluation-loop.mmd) · [SVG](rendered/evaluation-loop.svg) | Shows baseline comparison, gates, and retained failure evidence. | Versioned held-out cases run against a simpler baseline and the candidate. Deterministic aggregation checks configured gates. Passing evidence permits scoped promotion; failing evidence causes hold, rollback, or quarantine and becomes a future regression fixture. |
| Migration path | [Source](src/migration-path.mmd) · [SVG](rendered/migration-path.svg) | Shows incremental promotion and independent rollback. | Each level remains runnable. A measured problem motivates the next level, which runs in shadow mode and must pass configured gates. Any failure returns to the last known-good level without rewriting skill source. |

## Rendering

Use the repository's chosen Mermaid renderer or the project diagramming wrapper.
The renderer must not add semantic content that is absent from the source.
Review SVGs at their intended display size and keep text alternatives in this
index current.
