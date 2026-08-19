# Compatibility and adapters

The portable core is the set of contracts in `schemas/` plus the behavioral
requirements in `spec/`. Vendor syntax, filesystem placement, tool declaration
formats, model APIs, and authentication are adapter concerns.

## Conformance classes

- **Manifest reader** validates a manifest and loads only declared resources.
- **Registry compiler** verifies manifest identifiers and digests, then creates
  a derived, content-bound catalog.
- **Policy filter** applies a fail-closed profile before exposure or ranking.
- **Static router** implements Level 1 exact and domain routing.
- **Retrieval router** implements Level 2 candidate search and inspection after
  policy filtering.
- **Governed runtime** implements Level 3 transitions, telemetry, evaluation,
  promotion, drift detection, and rollback.

An implementation states the classes and schema major versions it supports. It
MUST NOT claim Level 2 or Level 3 conformance merely because a vendor runtime
offers generic search or telemetry.

The alpha `skillref` CLI targets repository validation, profile-filtered
registry compilation, and deterministic routing evaluation for selection,
rejection, and exposure. It does not claim manifest resource-loading, host
adapter, runtime activation, lifecycle execution, telemetry, behavioral
evaluation, promotion, or governed-runtime conformance.

## Adapter boundary

An adapter MAY translate portable fields into a host's native skill metadata,
tool allowlist, deferred-loading primitive, or directory layout. It MUST:

- preserve the portable skill identifier and version;
- preserve or record the source manifest digest;
- fail on a portable permission that the host cannot enforce;
- distinguish unsupported behavior from successful translation;
- never broaden a profile grant; and
- report any lossy mapping in machine-readable output.

Trust and host-compatibility decisions MUST use adapter-supplied verified
attributes represented as canonical policy inputs. A compiler MUST NOT infer a
grant from descriptive metadata or from the absence of those attributes.

Authentication material, local paths, account identifiers, private prompts,
and host inventories are runtime inputs and MUST NOT appear in portable
examples or compiled artifacts intended for distribution.

## Schema evolution

Readers MUST reject unknown schema major versions. They MAY accept a newer
minor version only when all unknown fields are safely ignored by the relevant
contract and the implementation records that compatibility decision. Writers
SHOULD emit the oldest schema version that expresses the required behavior.
