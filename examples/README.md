# Synthetic conformance examples

These examples demonstrate the four architecture levels with invented skills,
inputs, profiles, and policy decisions. They contain no production inventory,
private prompt, account identifier, integration, or machine-specific path.

Each level is deliberately self-contained so it can be validated and compared
with the next level without relying on a vendor adapter:

- `level-0-flat` exposes a small eligible set directly.
- `level-1-static-router` compiles deterministic domain routers.
- `level-2-retrieval` filters a registry before search and inspection.
- `level-3-governed` adds lifecycle, digest, telemetry, and rollback evidence.

The examples illustrate contracts; they do not prescribe universal skill-count,
token, latency, or accuracy thresholds. Promotion requires evidence from the
target library and its own configured policy.

## Portable core and adapters

The `SKILL.md` files use only portable `name`, `description`, and `license`
frontmatter. Reference-architecture metadata lives in adjacent manifests.
Vendor placement and optional vendor fields live under `../adapters/` and are
not written back into the portable skill.

## Conditional resources

The table-analysis examples contain a chart reference that is loaded only when
the user requests a chart. Merely registering, retrieving, inspecting, or
activating the skill does not load that reference.

## Safety fixtures

The Level 2 read-only profile denies the mutating `deployment-runner` before
retrieval. The Level 3 fixtures show stale-source and generated-profile drift as
fail-closed conditions. These are synthetic conformance cases, not proof that a
particular runtime enforces the same boundary.
