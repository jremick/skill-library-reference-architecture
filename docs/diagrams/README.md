# Diagram index

The Mermaid files in `src/` are canonical and human-editable. SVG files in
`rendered/` are generated review artifacts. If a rendered file differs from its
source, regenerate the SVG rather than editing it.
`render-manifest.json` binds each checked-in render to its source bytes so CI
detects stale or swapped output.

| Diagram | Files | Purpose | Text equivalent |
| --- | --- | --- | --- |
| Context-loading lifecycle | [Source](src/context-loading-lifecycle.mmd) · [SVG](rendered/context-loading-lifecycle.svg) | Separates inventory and policy, exposure, runtime disclosure, and outcomes. | Cached bytes may become an installed package, which may then be registered by exact manifest digest. A policy-eligible candidate can be visible or retrievable, inspected, conflict-checked, version-pinned, activated, optionally given named resources, executed, verified, and deactivated. Denied, review, failure, and incomplete states remain explicit. |
| Architecture levels | [Source](src/architecture-levels.mmd) · [SVG](rendered/architecture-levels.svg) | Compares the capability added at each level in a README-width progression. | Level 0 loads a flat eligible set; Level 1 compiles domain routers; Level 2 filters and retrieves from an off-prompt catalog; Level 3 adds policy, telemetry, evaluation, lifecycle controls, and rollback. Promotion requires local evidence, shadow comparison, and a last known-good rollback path. |
| Why this architecture | [Source](src/why-this-architecture.mmd) · [SVG](rendered/why-this-architecture.svg) | Shows when governed retrieval earns its complexity and what value it is intended to add. | A flat eligible set remains appropriate until measured context, overlap, permission, or routing pressure justifies more control. The governed path registers and filters skills, searches and inspects eligible candidates, activates a pinned skill, loads resources conditionally, and evaluates the outcome. The intended value is selective context, an explicit policy boundary, observable routing, and reversible migration. |
| Level 1 static routing in practice | [Source](src/level-1-static-routing-in-practice.mmd) · [SVG](rendered/level-1-static-routing-in-practice.svg) | Shows the most common static-router workflow from compilation through conditional resource loading. | Manifests, a registry, and a profile compile into a small prompt-visible set of domain routers. For a request, deterministic aliases and keyword rules select one off-prompt leaf. The runtime inspects and activates that exact skill and loads a named resource only when its condition is met. Ambiguous requests stop for clarification. |
| Level 2 filtered retrieval in practice | [Source](src/level-2-filtered-retrieval-in-practice.mmd) · [SVG](rendered/level-2-filtered-retrieval-in-practice.svg) | Shows policy filtering, off-prompt catalog search, candidate ranking, inspection, and exact activation. | Registry records are filtered by profile and permission policy before search or model ranking. A denied deployment runner never enters the candidate set. A thin prompt-visible interface searches the eligible off-prompt catalog, ranks a small set, inspects the deployment review skill, and activates its exact version. |
| Routing decision flow | [Source](src/routing-decision-flow.mmd) · [SVG](rendered/routing-decision-flow.svg) | Shows deterministic and semantic decisions in safe order. | Validation and policy filtering happen before exact routing or semantic search. The model can rank only eligible records. Deterministic conflict, version, and authority checks precede activation. |
| Registry and schema relationships | [Source](src/registry-schema-relationships.mmd) · [SVG](rendered/registry-schema-relationships.svg) | Shows canonical inputs, generated views, runtime records, and evidence. | Schemas validate manifests, the registry, router map, and profile. Those inputs produce content-bound catalog, compiled, and adapter views. Policy constrains activation. Runtime transitions emit redacted telemetry consumed by evaluation and promotion policy. |
| Evaluation loop | [Source](src/evaluation-loop.mmd) · [SVG](rendered/evaluation-loop.svg) | Shows baseline comparison, gates, and retained failure evidence. | Versioned held-out cases run against a simpler baseline and the candidate. Deterministic aggregation checks configured gates. Passing evidence permits scoped promotion; failing evidence causes hold, rollback, or quarantine and becomes a future regression fixture. |
| Migration path | [Source](src/migration-path.mmd) · [SVG](rendered/migration-path.svg) | Shows incremental promotion and independent rollback. | Each level remains runnable. A measured problem motivates the next level, which runs in shadow mode and must pass configured gates. Any failure returns to the last known-good level without rewriting skill source. |

The repository also includes a durable social preview [source](../../assets/social-preview.svg),
[upload-ready PNG](../../assets/social-preview.png), and
[content-binding manifest](../../assets/render-manifest.json). The committed PNG
is not evidence that the GitHub repository setting has been applied; verify
`usesCustomOpenGraphImage` after any settings change.

## Rendering

Use the repository's chosen Mermaid renderer or the project diagramming wrapper.
The renderer must not add semantic content that is absent from the source.
Review SVGs at their intended display size and keep text alternatives in this
index current.
