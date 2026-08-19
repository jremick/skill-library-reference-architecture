# Project harness

## Intent

Build a reusable, tool-agnostic reference architecture that helps maintainers
scale skill libraries without confusing physical availability, prompt exposure,
retrieval, activation, and execution.

## Good means

- Portable contracts remain separate from ecosystem adapters.
- Hard policy and lifecycle boundaries are deterministic and fail closed.
- Every architecture level is independently useful and reversible.
- Public examples contain no private environment material.

## Evidence

- Schema, cross-reference, conflict, privacy, and generated-digest tests.
- Held-out routing fixtures with positive and near-miss negative cases.
- Clean-clone quick-start verification.
- GitHub CI, metadata, security-setting, and visibility read-backs.

## Risks

- Duplicate sources of truth.
- Applying tool-retrieval results to skills without qualification.
- Vendor adapter drift.
- Sensitive telemetry.
- Complexity that does not beat the simpler-level baseline.

## Work mode

Scaffold first, then delivery and evaluation gates. Public visibility is a
separate publication action after the pre-public evidence gate passes. Tags,
releases, and packages are separately gated and remain out of scope for the
initial public-alpha publication.

## Rollback

Return to the previous immutable compiled bundle or preceding architecture level.
No destructive migration is required for Levels 0 through 3.
