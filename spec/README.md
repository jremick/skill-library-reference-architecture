# Specification index

The prose contracts define behavior that cannot be expressed completely in
JSON Schema. The schemas define accepted document structure. Both are
normative.

| Contract | Prose | Machine-readable schema |
|---|---|---|
| Terms, states, and architecture levels | [`terminology.md`](terminology.md) | — |
| Skill manifest | [`contracts.md#skill-manifest`](contracts.md#skill-manifest) | [`../schemas/skill-manifest.schema.json`](../schemas/skill-manifest.schema.json) |
| Registry | [`contracts.md#registry`](contracts.md#registry) | [`../schemas/registry.schema.json`](../schemas/registry.schema.json) |
| Router map | [`contracts.md#router-map`](contracts.md#router-map) | [`../schemas/router-map.schema.json`](../schemas/router-map.schema.json) |
| Profile and permission filter | [`contracts.md#profile-and-permissions`](contracts.md#profile-and-permissions) | [`../schemas/profile.schema.json`](../schemas/profile.schema.json) |
| Activation transition | [`contracts.md#activation-lifecycle`](contracts.md#activation-lifecycle) | [`../schemas/activation-transition.schema.json`](../schemas/activation-transition.schema.json) |
| Telemetry event | [`contracts.md#telemetry`](contracts.md#telemetry) | [`../schemas/telemetry-event.schema.json`](../schemas/telemetry-event.schema.json) |
| Evaluation case | [`contracts.md#evaluation`](contracts.md#evaluation) | [`../schemas/eval-case.schema.json`](../schemas/eval-case.schema.json) |
| Promotion and rollback reference checklist | [`contracts.md#evaluation`](contracts.md#evaluation) | [`../governance/promotion-policy.yaml`](../governance/promotion-policy.yaml) (not executable) |
| Adapter and schema evolution | [`compatibility.md`](compatibility.md) | Adapter-specific |

Normative contracts define what an implementation must satisfy when it claims
the corresponding conformance class; they are not a feature claim for the
alpha CLI. The current CLI covers repository validation, profile-filtered
compilation, and deterministic routing selection, rejection, and exposure. It
does not provide host trust or compatibility attestation, resource loading,
lifecycle execution, telemetry collection, behavioral evaluation, or an
executable promotion controller.

All repository-owned synthetic manifests declare `Apache-2.0`. The manifest
schema permits other SPDX-style license declarations because downstream users
remain responsible for licensing their own skills.
