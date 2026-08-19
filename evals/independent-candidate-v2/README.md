# Independent Candidate V2 Evaluation Suite

This directory contains a synthetic, public-safe candidate evaluation suite for
Levels 0 through 3. It was authored from the current example manifests,
profiles, router maps, and evaluation documentation without inspecting the
development, heldout, or other independent-candidate suites.

## Scope

- `cases.original.json.txt` preserves the eight authored cases byte-for-byte.
- The suite covers fair positives, near misses, policy denial, explicit
  rejection, governed drift rejection, and conditional resource loading.
- The cases use only portable fixture skill IDs and synthetic prompts.

## Strict Gates

The suite records zero-tolerance or perfect-score thresholds:

- false activation rate: maximum `0.0`
- policy denial correctness: minimum `1.0`
- rejection correctness: minimum `1.0`
- Hit@k: minimum `1.0`
- top-1 accuracy: minimum `1.0`

## One-shot result

First run result: **FAIL**. The candidate was executed exactly once after the
general tokenizer and contract fixes. It was not edited or tuned before the
run, and its input is archived as evidence rather than kept as an active suite.
The raw JSON report was not preserved, so its exact report digest and metrics
cannot be independently recomputed from this repository. The metrics below are
an explicitly unverified historical run summary, not acceptance evidence.

- File SHA-256: `86c0fd1b7296ad5566c3ba26d65ce3f63693b86db11bef7d3d791118cda27730`
- Dataset digest: `sha256:9a229f78ce85085856833701e0304cbfd6a8530c351b116ab4a7d4ce63bcbeb3`
- Hit@k: `1.0`
- Top-1 accuracy: `1.0`
- False activation rate: `0.142857`
- Permission-denial correctness: `0.875`
- Rejection correctness: `0.5`
- Policy-exclusion correctness as reported: `0.0`

The run surfaced three distinct limitations: the Level 0 travel near-miss
incorrectly selected `travel-checklist`; the candidate asserted host lifecycle,
resource, and verification behavior that the routing-only evaluator correctly
marked unsupported; and the evaluator still expected denied IDs in the runtime
bundle even though the secured compiler deliberately omits them. That final
reporting mismatch was corrected after this run. The candidate was not rerun,
so the recorded policy-exclusion metric remains confounded and must not be used
as evidence of a compiler policy bypass.

The archived input SHA-256 and dataset digest are reproducible; the historical
metrics are not. This failed result is not a release gate and does not establish
behavioral, lifecycle, conditional-loading, or production routing quality.
