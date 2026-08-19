# Canonical contracts

The JSON Schemas in `schemas/` are the machine-readable contracts. This file
defines ownership, ordering, and behavior that JSON Schema alone cannot prove.

## Ownership and derivation

| Concern | Canonical owner |
|---|---|
| Skill identity, triggers, permissions required, resources, conflicts, risk, evaluation links | Skill manifest |
| Manifest location, manifest digest, registration lifecycle | Registry |
| Routing topology, exact aliases, retrieval configuration | Router map |
| Eligibility, permission grants, denials, exposure modes | Profile |
| Runtime projection | Derived compiled bundle |
| Observed behavior and outcomes | Telemetry events |
| Controlled expectations and scored results | Evaluation cases and evaluation output |

An implementation MUST reject a registry entry that copies semantic manifest
fields such as descriptions, domains, triggers, permissions, or conflicts.
Catalog indexes and compiled router bundles MAY project those fields, but MUST
be marked as derived and content-bound to the registry, manifest, router, and
profile digests used to create them.

## Skill manifest

`skill-manifest.schema.json` defines a portable skill. Identifiers and versions
are immutable for published content. Changing the bytes behind an existing
identifier and version is invalid.

The manifest:

- MUST declare positive and negative trigger examples;
- MUST identify a primary entry point and every conditional resource;
- MUST declare required capabilities and resource scopes, even when both are
  empty;
- MUST declare risk and side-effect characteristics;
- MUST declare hard conflicts, supersession, and companion relationships; and
- MUST link at least one evaluation suite.

Every synthetic manifest maintained by this repository MUST declare
`Apache-2.0`. External manifests MAY declare another applicable license; the
framework does not relicense downstream content.

Resource paths are relative POSIX paths. A runtime MUST prevent traversal and
MUST load only the named resource whose `loadWhen` condition is satisfied.
Scripts and other executable resources remain subject to profile grants.

## Registry

`registry.schema.json` is a registry of exact manifest references. Each entry
binds a skill identifier to a manifest URI and SHA-256 digest. The identifier
in the referenced manifest MUST equal the registry entry identifier.

Lifecycle states are `draft`, `active`, `deprecated`, and `retired`.
Deprecated entries SHOULD name a replacement when one exists. Retired entries
MUST NOT be selected for new work. The registry may record cache, installation,
and registration observations, but those observations remain distinct.

## Router map

`router-map.schema.json` groups skill identifiers without granting access.
Before exact rules, keyword rules, or retrieval run, a runtime MUST intersect
router candidates with the active profile. Denials override grants.

Exact aliases are deterministic. Keyword and semantic ranking are candidate
generation only; a selected candidate still requires inspection and an
activation decision. Retrieval limits and score thresholds are configuration,
not claims of universal quality.

## Profile and permissions

`profile.schema.json` is fail-closed: `defaultDecision` is always `deny`, and
`denialsOverrideGrants` is always `true`. Selectors determine which skills a
rule addresses. A grant then authorizes only the named capabilities, resource
scopes, resource roles, and exposure modes. An empty grant permission list
grants no corresponding permission.

A denial without a `permissions` object denies every use of matching skills. A
denial with `permissions` removes only the named permissions. The most specific
grant never overrides a matching denial. Unknown skills, capabilities, scopes,
roles, risk levels, or trust tiers are denied.

## Activation lifecycle

`activation-transition.schema.json` records one allowed state transition. A
runtime MUST emit separate evidence for visibility, retrieval, inspection,
activation, conditional loading, execution, and verification. It MUST NOT infer
successful verification from successful execution.

Every activation pins the skill identifier, version, and manifest digest. A
conditioned resource load additionally pins its resource path and digest when
one is declared. Invalid transitions fail closed and preserve the prior state.

## Progressive disclosure

The portable loading order is:

1. Filter registry entries by profile, trust, and permission.
2. Expose bounded metadata or search the eligible catalog.
3. Inspect the selected manifest and primary instruction body.
4. Resolve deterministic conflicts and permission requirements.
5. Activate one primary skill version.
6. Load only resources whose declared conditions are met.
7. Execute permitted operations and verify the outcome.

Deep, implicit reference chains are non-conforming. A resource MAY link to a
child resource only when that child is also declared in the manifest and the
runtime continues to enforce load conditions and bounds.

## Conflict resolution

Resolution order is deterministic:

1. Apply profile denials and lifecycle exclusions.
2. Reject declared hard conflicts.
3. Prefer a non-deprecated skill over a skill it supersedes.
4. Honor an explicit user selection only when policy permits it.
5. Use model judgment to rank remaining semantic overlaps.
6. If ambiguity remains material, request clarification or decline activation.

Companion skills MAY be activated only if each is independently eligible and
the runtime identifies one primary skill. Model judgment cannot override a
hard conflict or denial.

## Versioning

`schemaVersion` versions each contract family. Schema major-version changes
may be breaking. Skill `version`, registry `registryVersion`, router `version`,
and profile `version` version their respective content independently.

Compiled bundles MUST record source digests. Released artifacts are immutable.
An implementation MAY use Semantic Versioning after it declares a stable
compatibility surface; pre-stable versions MUST NOT imply guarantees that the
repository has not made.

## Telemetry

`telemetry-event.schema.json` permits identifiers, decisions, bounded metrics,
verification state, and privacy metadata. It deliberately has no fields for raw
prompts, secrets, resource contents, tool arguments, or tool results. Producers
MUST minimize and redact before persistence and SHOULD use opaque or
one-way-derived run and session identifiers. Schema conformance does not prove
that an identifier is anonymous or that an upstream producer redacted its
source correctly.

Telemetry labels are a closed set of low-cardinality dimensions with enumerated
values. Implementations MUST NOT add free-form label keys or values as an escape
hatch for prompts, personal data, secrets, arguments, results, or error text.
Non-synthetic events MUST declare the redaction policy version and method, set
`redacted` and `dataMinimized` to true, and keep `rawContentCaptured` false.
Persistence is local-first; `approved-private` storage requires a separately
reviewed data boundary and does not authorize public or third-party export.

Token savings alone are never success evidence. Evaluation and promotion
consider task outcome, verification, corrections, latency, privacy, policy
behavior, and cost against the simpler-level baseline.

## Evaluation

`eval-case.schema.json` defines synthetic or approved controlled inputs,
expected routing, policy, activation, outcome, and verification. Evaluation
suites SHOULD contain positive, negative, near-miss, overlap, denial, drift,
and rollback cases and SHOULD run from clean context with repeated trials where
model judgment is involved.

The system under test MUST NOT generate its own independent acceptance result.
When a promotion evaluator is implemented, deterministic assertions decide its
hard gates; separately configured qualitative review MAY score semantics or
output quality. FAIL, ERROR, and INCOMPLETE are preserved as distinct outcomes.

## Promotion and rollback

`governance/promotion-policy.yaml` is a reference checklist for maintainers and
future evaluators. The current `skillref` CLI does not execute it, aggregate its
metrics, or authorize a promotion, publication, release, or rollback. A passing
schema, routing evaluation, or repository validation result is therefore not a
public-alpha acceptance decision.

Public-alpha acceptance remains an external review that binds the exact source,
policy, dataset, evaluator, and evidence digests. Any future automated evaluator
MUST implement the checklist explicitly, compare against a configured simpler
baseline, preserve FAIL, ERROR, and INCOMPLETE, and refuse to pass unset
thresholds or missing evidence. Public visibility, tagging, packaging, and
release remain separate actions even after acceptance.
