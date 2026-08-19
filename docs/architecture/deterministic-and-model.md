# Deterministic code and model judgment

The architecture uses code for decisions that must be reproducible and models
for decisions that depend on meaning. Mixed decisions keep a deterministic
outer boundary and record the model's ranked evidence.

The lists below allocate responsibilities in the normative architecture; they
are not a claim that the alpha CLI implements every item. Trust and host
compatibility become deterministic filter inputs only after an adapter supplies
verified attributes in canonical form.

## Deterministic responsibilities

- discover and parse manifests;
- validate schemas, paths, IDs, versions, and content digests;
- apply profile, trust, permission, lifecycle, and compatibility denials;
- compile exact routers and adapter outputs;
- resolve declared aliases, dependencies, and hard conflicts;
- enforce lifecycle state transitions and immutable version pins;
- calculate token, latency, rate, and aggregate evaluation metrics;
- redact or reject sensitive telemetry fields;
- detect source/generated-output drift; and
- evaluate release, promotion, quarantine, and rollback gates.

## Model responsibilities

- interpret user intent when exact routing is insufficient;
- rank policy-eligible candidates by semantic relevance;
- identify possible semantic overlaps not declared in metadata;
- recommend a primary skill and compatible companion skills;
- judge qualitative output against a bounded rubric; and
- explain ambiguous evaluation or migration findings.

## Hybrid boundary

The safe order is:

1. deterministic validation and eligibility filtering;
2. deterministic exact-match routing when available;
3. semantic retrieval or ranking over the remaining set;
4. deterministic conflict and version checks;
5. bounded model selection with candidate evidence;
6. deterministic activation recording and hard policy enforcement; and
7. deterministic verification where possible, plus rubric-based review where
   meaning or usability requires judgment.

A model cannot override a hard denial. Model-generated scores, tests, or
explanations are evidence inputs, not independent acceptance gates. When the
model and deterministic state disagree, the deterministic policy boundary wins
and the discrepancy is recorded for review.

## Alpha reference implementation

The current CLI validates repository structures, compiles a profile-filtered
catalog, and evaluates deterministic routing selection, rejection, and
exposure. It does not attest trust, verify host compatibility, load or execute
resources, operate the lifecycle state machine, collect runtime telemetry,
evaluate behavioral outcomes, or execute release and promotion gates.
