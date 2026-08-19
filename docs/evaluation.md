# Evaluation

Evaluation asks whether a skill architecture improves outcomes without
weakening policy, privacy, or reliability. Different claims require different
evidence; a routing result cannot establish runtime activation or task quality.

## Evidence model

### Evidence

The [Agent Skills evaluation guide](https://agentskills.io/skill-creation/evaluating-skills)
recommends testing in a clean context and comparing behavior with and without a
skill. The [MCP client best-practices guide](https://modelcontextprotocol.io/docs/develop/clients/client-best-practices)
documents multiple retrieval strategies and treats progressive-discovery
thresholds as configurable.

### Inference

Retrieval quality for descriptions does not prove behavioral quality for
procedural instructions. Lower prompt cost may coexist with worse selection,
execution, or verification.

### Recommendation

Use deterministic checks for exact assertions and independent, held-out tasks
for release evidence. Treat model-generated cases as development aids, not as
independent acceptance evidence for the same model and system under test.

## Evidence layers

| Layer | Observable evidence | Example measures |
| --- | --- | --- |
| Structural | Parsed contracts, references, and content digests. | Validation rate, digest stability, unresolved references. |
| Routing | Eligible compiled surface plus selected or rejected candidates. | Precision, recall, Hit@k, false activation, policy exclusion. |
| Exposure | Membership in prompt-visible or router-retrievable compiled sets. | Exposure correctness, prompt-visible bytes. |
| Lifecycle | Host-emitted state transitions and resource-load evidence. | Inspected, activated, executed, conditionally loaded, rollback result. |
| Behavioral | Task artifacts and independent verification. | Task success, rubric score, required checks completed, corrections. |
| Operational | Runtime measurements from a deployed or replayable system. | Latency, context share, cache churn, reroutes, recovery time. |

The bundled deterministic evaluator covers only routing, exposure, and
pre-ranking policy exclusion. It fails closed when a case asks it to establish
activation, inspection, execution, resource loading, an outcome, a qualitative
rubric, or external verification. A host adapter must emit and bind that
evidence separately.

## Dataset design

The checked-in development and held-out suites contain synthetic positive,
near-miss, rejection, exposure, and permission-exclusion cases across Levels 0
through 3. Each executable case declares expected skill IDs, forbidden skill
IDs, a profile, and an explicit routing decision or exposure when applicable.

Broader host-level suites should add:

- ambiguous and composition cases;
- hard-conflict and dependency cases;
- lifecycle denial, drift, quarantine, and rollback scenarios;
- conditional-resource evidence;
- adversarial descriptions and prompt-injection attempts;
- adapter parity cases; and
- outcome checks that do not depend solely on model self-report.

Keep development and held-out sets separate. Record the dataset, compiler,
bundle, source, profile, adapter, runtime, and model versions used. Repeat
non-deterministic trials and retain the distribution and failure examples.

## Experiment matrix

For a promotion candidate, compare the simplest meaningful baseline with the
candidate architecture and a rollback bundle. Policy and privacy gates should
remain zero tolerance unless a separately reviewed exception contract says
otherwise. Lower token use is supportive evidence only.

## Current CLI boundary

`skillref evaluate` applies per-suite routing thresholds and emits a
content-bound report. Each report includes:

- the canonical dataset digest;
- compiler version plus bundle, source, and profile digests for every system;
- per-case selection, rejection, exposure, and policy-exclusion observations;
- aggregate routing metrics; and
- explicit unsupported or failed expectations.

`governance/promotion-policy.yaml` is currently a non-executable reference
checklist. The CLI does not combine routing, lifecycle, behavioral, operational,
or privacy evidence into a promotion decision. A maintainer or future
orchestrator must perform that aggregation and preserve FAIL, ERROR, INCOMPLETE,
and unsupported results.

Automated checks do not establish usability, accessibility conformance,
qualitative excellence, security, or production reliability without
independent evidence appropriate to those claims.

See the canonical [evaluation loop diagram](diagrams/src/evaluation-loop.mmd).
