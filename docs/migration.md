# Migration between architecture levels

Migration is incremental. Source manifests and registry identity remain stable
while routing, retrieval, policy, and evidence capabilities are added around
them.

This is an adoption playbook, not a sequence performed by the alpha CLI.
`governance/promotion-policy.yaml` is a configurable reference checklist;
operators supply evidence and make promotion or rollback decisions outside the
current tool.

## Preconditions for every migration

- Freeze a content-addressed baseline bundle.
- Define the problem the next level is intended to solve.
- Add held-out positive, near-miss, denial, conflict, and rollback cases.
- Configure promotion and rollback gates for the affected task/risk classes.
- Identify unsupported adapter behavior and privacy boundaries.
- Keep the current level runnable until the next level passes.

## Level 0 to Level 1

1. Register exact manifest references and digests without copying manifest
   semantics into the registry.
2. Define stable domains and exact leaf routes from manifest selection
   metadata.
3. Generate router/profile surfaces deterministically with a source digest.
4. Compare flat and compiled routing in clean-context evaluation.
5. Promote only if routing and outcomes meet the configured non-regression
   gates.

Rollback: restore the flat prompt surface from the same manifest versions.

## Level 1 to Level 2

1. Keep the registry off prompt and build a filtered catalog.
2. Apply profile and permission denials before indexing or ranking. Add trust,
   lifecycle, and compatibility denials only from adapter-supplied verified
   canonical attributes; missing evidence fails closed.
3. Add catalog, search, and inspect interfaces.
4. Run retrieval in shadow mode beside exact routers.
5. Compare candidate ranks, missed activations, corrections, latency, context
   cost, and task outcomes.
6. Promote by task class; retain exact routes as an observable fallback.

Rollback: disable retrieval and restore the last compiled router bundle.

## Level 2 to Level 3

1. Introduce immutable registry releases and policy decision records.
2. Add activation/deactivation, quarantine, deprecation, and rollback controls.
3. Emit privacy-safe telemetry for lifecycle and outcome measurement.
4. Bind evaluation suites and ownership review dates to registry records.
5. Run policy and lifecycle controls in shadow mode, then enforce by risk class.
6. Exercise rollback under realistic failure conditions before promotion.

Rollback: restore the prior registry, policy, and compiler bundle; keep failed
events and evaluation evidence append-only.

## Promotion decision

An adopting implementation should promote only when the next level:

- resolves the measured problem that justified the migration;
- meets configured routing, behavioral, operational, privacy, and lifecycle
  gates;
- does not weaken hard-denial boundaries;
- can be reproduced from a clean checkout; and
- can roll back without rewriting skill source or losing failure evidence.

Stop when a higher level adds complexity without outcome improvement, requires
private implementation details to explain, cannot fail closed, or lacks an
honest rollback path.

See the canonical [migration path diagram](diagrams/src/migration-path.mmd).
