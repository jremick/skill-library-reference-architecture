# Normative terminology

This specification uses **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and
**MAY** as requirement terms. A conforming implementation documents every
deliberate deviation from a **SHOULD** requirement.

## Objects

- **Skill**: a versioned unit of procedural capability with one manifest, one
  primary instruction entry point, and zero or more conditionally loaded
  resources.
- **Manifest**: the canonical source for a skill's identity and semantics,
  including its triggers, risk, permission requirements, resources, conflicts,
  and evaluation suites.
- **Registry**: an index of manifest locations, content digests, and lifecycle
  status. It does not own or duplicate skill semantics.
- **Router map**: a portable routing topology that groups skill identifiers,
  declares exact rules, and configures optional retrieval. It never grants
  permission.
- **Profile**: a fail-closed set of grants and denials. A profile decides which
  skills and capabilities are eligible before search or model ranking.
- **Compiled bundle**: a derived, content-bound projection for a particular
  registry, router map, and profile. It MUST name all source digests and MUST
  NOT be hand-edited as a second source of truth.
- **Telemetry event**: a privacy-bounded observation about routing, activation,
  execution, verification, or evaluation. Telemetry is evidence, not policy.
- **Evaluation case**: a controlled input and expected routing and outcome
  contract. Evaluation results are evidence, not skill semantics.

## Lifecycle and exposure states

The following states are distinct. Implementations MUST NOT collapse one state
into evidence for another.

| State | Meaning |
|---|---|
| `cached` | Bytes are locally or remotely cached, but not necessarily installed. |
| `installed` | The skill package is available to the runtime. |
| `registered` | A registry entry identifies an exact manifest and digest. |
| `eligible` | The active profile and policy permit consideration of the skill. |
| `prompt-visible` | Skill metadata is placed directly in model context. |
| `router-retrievable` | The skill is absent from the initial prompt but may be returned by an allowed router or catalog. |
| `retrieved-candidate` | Retrieval returned the skill for the current run. |
| `inspected` | The runtime loaded sufficient manifest or instruction content to make an activation decision. |
| `activated` | The skill's primary instructions govern the current work. |
| `conditionally-loaded` | A named reference, script, template, asset, or evaluation resource was loaded because its declared condition was met. |
| `executing` | An allowed skill-directed operation is in progress. |
| `verified` | Declared verification for that operation completed successfully. |

`prompt-visible` and `router-retrievable` are exposure modes, not synonyms for
installation, inspection, or activation. A denial is applied before either
exposure mode can make a skill a candidate.

## Architecture levels

- **Level 0 — flat/simple**: a small catalog with metadata discovery, explicit
  activation, and conditional resources.
- **Level 1 — static routing compiler**: domain routers and exact rules compile
  a bounded visible surface from canonical manifests.
- **Level 2 — filtered catalog retrieval**: deterministic policy filtering is
  followed by search, candidate inspection, and exact activation.
- **Level 3 — retrieval-served and governed**: retrieval is the primary skill
  delivery path and is paired with policy, telemetry, evaluation, lifecycle,
  drift, promotion, and rollback controls.

The levels describe operating architectures, not maturity badges. Promotion
thresholds are local policy inputs derived from a measured simpler-level
baseline; skill counts are never universal promotion thresholds.
