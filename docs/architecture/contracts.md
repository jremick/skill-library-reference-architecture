# Contract map

This page explains the responsibilities of the canonical contracts. Exact
fields, requirement levels, and validation rules are defined in `spec/` and
`schemas/`.

These responsibilities are normative for an implementation that claims the
corresponding conformance class. They are not all implemented by the alpha
reference CLI. In particular, a trust or compatibility decision requires
adapter-supplied verified attributes in the canonical input; the current
compiler does not independently discover or attest those attributes.

| Contract | Responsibility | Must not decide |
| --- | --- | --- |
| Skill manifest | Portable identity, description, triggers, compatibility, provenance, risk, permission requirements, resources, conflicts, and evaluation references. | Current user permission or runtime activation. |
| Registry | Exact manifest URI and digest, registration lifecycle, and optional cache/install observations. | Skill descriptions, triggers, permissions, conflicts, or other semantic manifest fields. |
| Router map | Stable domains, child IDs, exact aliases, precedence, fallbacks, and expected positive/negative intents. | Hard permission overrides. |
| Profile/permission filter | Deterministic allow/deny decisions over profile, trust, lifecycle, compatibility, and permission attributes. | Semantic ranking inside the allowed set. |
| Activation lifecycle | Valid state transitions, conflict resolution, version pinning, conditional resource loading, deactivation, and cache scope. | Outcome verification criteria. |
| Progressive-disclosure rules | What remains metadata-only, what enters primary instructions, and the condition for loading each named resource. | Whether a disallowed skill becomes eligible. |
| Conflict contract | Exact conflicts, precedence, composition constraints, and escalation behavior for semantic overlap. | Silent merging of incompatible instructions. |
| Version contract | Independent schema, skill, registry, compiler, and adapter versions plus immutable digests. | Compatibility claims not backed by tests. |
| Telemetry contract | Privacy-safe events for routing, activation, cost, outcome, verification, correction, and rollback. | Collection of raw sensitive content by default. |
| Evaluation contract | Datasets, baselines, repetitions, metrics, gates, evidence retention, and claim limits. | Promotion without configured passing evidence. |

## Relationship rules

1. A manifest owns skill identity and semantics; the registry locates the exact
   manifest digest and records registration lifecycle.
2. A router map references skill identifiers. A retrieval index or compiled
   bundle projects manifest fields through the registry and carries every
   source digest.
3. A profile/permission filter reduces the candidate set before a model can
   rank it.
4. Activation pins the inspected version and its policy decision.
5. Telemetry records transitions without becoming the lifecycle source of
   truth.
6. Evaluation consumes immutable fixtures and emitted evidence. A governed
   runtime may use evaluated evidence in a promotion decision; the repository's
   promotion policy is a non-executable reference checklist.
7. Generated adapters and router surfaces are reproducible outputs, not
   hand-edited contract copies.

## Versioning recommendation

Use independent versions for independently changing contracts. During initial
development, pre-1.0 versions communicate instability. Apply Semantic
Versioning only after the public compatibility surface has been declared; the
[SemVer specification](https://semver.org/) explicitly requires a declared
public API.

See the canonical [contract relationship diagram](../diagrams/src/registry-schema-relationships.mmd).

The current deterministic routing evaluator covers candidate selection,
rejection, and exposure only. Lifecycle transitions, resource loading,
execution, outcome verification, and behavioral quality require evidence from
the named host runtime.
