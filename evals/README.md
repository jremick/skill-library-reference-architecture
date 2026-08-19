# Evaluation suites

The evaluation corpus is synthetic. The bundled deterministic evaluator tests
only routing selection, explicit rejection, compiled exposure, and policy
exclusion. It does not execute skill instructions or observe a host runtime.

## Suite separation

- `development/` contains tuning-visible cases for Levels 0 through 3.
- `heldout/` contains cases that must leave the held-out set if they influence
  an implementation decision.
- `independent-candidate/` preserves the byte-stable failed first-run candidate
  and its original result. It is evidence of a discovered defect, not a pass.
- `independent-candidate-v2/` preserves a second byte-stable, one-shot candidate
  and its failed strict-gate result. It is archived evidence, not an active
  suite or independent acceptance pass.

The development and held-out suites are executable routing gates. Their cases
use `expected_decision` for selection or rejection and `expected_exposure` for
`prompt_visible` or `router_retrievable` membership. `must_not_skill_ids` are
hard exclusions.

## Current deterministic evaluator

`skillref evaluate` checks:

- selection of at least one expected skill;
- rejection with an empty candidate result;
- expected prompt-visible or router-retrievable exposure in the compiled
  bundle;
- absence of forbidden skills from top-k results; and
- optional assertions that named source-registered skills are absent from every
  rankable, routed, and exposed surface under the selected profile.

The evaluator reports activation, inspection, execution, conditional-resource,
outcome, qualitative-rubric, and verification expectations as unsupported and
fails the run. Those assertions need host evidence from a lifecycle or
behavioral evaluator; prompt wording is not evidence that a condition occurred.

Reports include the dataset digest and every compiled system's bundle, source,
and profile digests. Per-case results name the bundle used. Raw prompts are not
included in reports.

## Other deterministic checks

Repository validation and unit tests separately cover schema and reference
integrity, exact identifiers and digests, permission filtering, lifecycle
transition validity, telemetry shape, and privacy patterns. Passing those
checks does not turn an unexecuted lifecycle scenario into routing-evaluation
evidence.

## Behavioral and lifecycle evaluation

A host integration may additionally measure:

- inspected, activated, executed, and conditionally loaded resources;
- task outcome, verification, correction count, latency, and repeat variance;
- conflict, drift, rollback, and recovery behavior; and
- privacy or policy outcomes that require runtime observation.

Repeat non-deterministic trials and compare a higher architecture level with
the next simpler applicable baseline. Lower token use alone is not evidence of
better outcomes.

## Gates and promotion boundary

Suite thresholds configure only the metrics emitted by the current routing
evaluator. `governance/promotion-policy.yaml` is a reference checklist for a
maintainer or future orchestrator; the current CLI does not aggregate evidence
or issue promote, hold, quarantine, or rollback decisions.

## Claim limits

- Deterministic tests establish conformance only for the checked contracts and
  fixtures.
- Behavioral results apply only to the versioned synthetic case distribution.
- Model-judged results are advisory unless calibrated against independent human
  or deterministic labels.
- Self-generated fixtures are development evidence, not independent acceptance.
- Passing local tests does not establish real-world usefulness, security,
  accessibility, cross-ecosystem compatibility, or production reliability.
- A privacy scan checks for known patterns and synthetic canaries; it cannot
  prove that all sensitive information is absent.
- Telemetry conformance proves that expected fields and redaction rules were
  exercised, not that production instrumentation is complete or effective.

Reports must preserve unknown, incomplete, unsupported, and failed results and
bind their conclusions to the dataset and compiled systems that produced them.
