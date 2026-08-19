# Architecture levels

The levels are capability bundles, not maturity badges. A reliable Level 0
library is preferable to a Level 3 platform whose retrieval or policy behavior
has not been validated.

This page defines architecture-level responsibilities. It is not a feature
matrix for the alpha `skillref` CLI. In particular, resource loading,
activation, execution, runtime telemetry, behavioral evaluation, and promotion
must be implemented and evidenced by the adopting host.

## Level 0: flat and simple

All eligible skill metadata is available directly to the runtime. When a skill
is selected, its primary instructions are loaded; named supporting resources
are loaded only when their documented conditions are met.

Use Level 0 while the catalog remains comprehensible, its context cost stays
inside the local budget, and held-out evaluation does not show material routing
or collision failures.

Required controls:

- portable manifests;
- schema and content validation;
- explicit progressive-disclosure conditions;
- basic version and ownership metadata; and
- a clean-context behavioural baseline.

## Level 1: static routing compiler

A deterministic compiler produces a small always-visible core plus stable
domain routers. Routers name or point to exact leaf skills. Manifests remain
the source of skill semantics, the registry remains the source of exact
manifest references and lifecycle status, and generated surfaces carry source
digests.

Use Level 1 when domains are stable and compiled routing reduces irrelevant
context or collisions without increasing missed activations.

Additional controls:

- canonical registry and router map;
- deterministic profile compilation;
- exact leaf activation;
- generated-output drift detection; and
- flat-versus-router evaluation.

## Level 2: filtered catalog retrieval

The full catalog remains off prompt. Deterministic profile and permission
filters reduce the eligible set before keyword, embedding, model, or hybrid
retrieval. Trust and compatibility filters join that boundary only when an
adapter supplies verified attributes as canonical inputs. The runtime inspects
shortlisted candidates before activating a pinned skill version.

Use Level 2 when static router surfaces become costly, domains overlap, the
catalog changes frequently, or Level 1 misses its configured routing objectives.

Additional controls:

- fail-closed eligibility filter;
- catalog, search, and inspect interfaces;
- candidate evidence and ranked-result telemetry;
- semantic-overlap and denial tests; and
- router-versus-retrieval evaluation.

## Level 3: retrieval-served and governed

Only core policy and discovery primitives need to be always visible. Skills are
served through a versioned registry with policy decisions, lifecycle controls,
telemetry, evaluation gates, drift detection, staged promotion, and rollback.

Use Level 3 for dynamic or multi-tenant catalogs, multiple trust boundaries,
high-risk actions, frequent change, or regulated operational requirements. A
Level 3 design should first run in shadow mode and beat the Level 2 baseline.

Additional controls:

- policy decision records and immutable skill versions;
- controlled activation and deactivation;
- evaluation-backed promotion and quarantine;
- privacy-preserving operational telemetry;
- release gates and rollback bundles; and
- incident and lifecycle procedures.

## Configurable promotion evidence

No skill count, token count, or context percentage automatically selects a
level. Each implementation configures evidence gates appropriate to its task
and risk classes, including:

- capability-metadata share of usable context;
- routing precision, recall, and Hit@k;
- task success and verification completion;
- false, missed, and unnecessary activation rates;
- user correction and reroute rates;
- collision and policy-denial leakage rates;
- latency and token cost;
- catalog drift, stale ownership, and rollback recovery; and
- operational burden of the proposed level.

For an adopting implementation, promotion requires evidence that the next
level improves the outcomes that motivated the change. Lower token use alone
is insufficient. The repository's promotion policy is a reference checklist;
the alpha CLI does not execute it.

## Rollback rule

Every level remains independently runnable. A deployment can restore a prior
content-addressed registry/compiler bundle or return to the preceding level
without rewriting skill source. Failed promotion evidence is retained as a
failed result rather than being reclassified as a pass.
