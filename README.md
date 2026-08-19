# Skill Library Reference Architecture

A tool-agnostic reference architecture for AI skill libraries that need to grow
without loading every capability into every model context.

> **Public alpha:** this repository is available for inspection and trial use.
> Its schemas and CLI may change; no release, tag, or package is published.

[![Validate](https://github.com/jremick/skill-library-reference-architecture/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/jremick/skill-library-reference-architecture/actions/workflows/validate.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Status: public alpha](https://img.shields.io/badge/status-public%20alpha-yellow.svg)](#current-status)

## What this is

This repository provides contracts, examples, diagrams, and a small reference
validator/compiler for managing skill libraries across four architecture levels:

| Level | Shape | Use it while |
| --- | --- | --- |
| 0 | Flat, simple skill set | The complete visible surface meets measured context and quality budgets. |
| 1 | Static domain routers and a deterministic compiler | Stable task domains compress the visible surface without increasing routing misses. |
| 2 | Filtered catalog, search, inspect, and exact activation | Metadata pressure or semantic overlap makes static routing insufficient. |
| 3 | Retrieval-served policy, telemetry, evaluation, and lifecycle controls | Dynamic catalogs, trust boundaries, or higher-risk actions require governed runtime controls. |

These are migration options, not a maturity contest. Promotion is driven by
configured evidence—context share, routing quality, permission complexity,
latency, drift, task outcomes, and rollback readiness—not a universal number of
skills.

The levels and contracts describe the target architecture for a conforming
implementation. They do not imply that the alpha `skillref` CLI implements a
host runtime. The current CLI validates repository documents, compiles a
profile-filtered catalog, and evaluates deterministic routing selection,
rejection, and exposure over synthetic cases. Host compatibility, trust
attestation, instruction or resource loading, activation, execution, telemetry
collection, behavioral outcomes, and promotion decisions require separate host
or adapter evidence.

## Core lifecycle

The reference model keeps these states distinct:

```text
installed/cache -> registered -> policy-eligible
                  -> prompt-visible OR router-retrievable
                  -> retrieved candidate -> inspected -> activated
                  -> conditional resource loaded -> executed -> verified
```

Installed does not mean visible. Inspected does not mean activated. Activating a
skill does not imply that every bundled reference, script, or asset was loaded
or executed.

## Quick start

Prerequisites: Git, [uv](https://docs.astral.sh/uv/), and Python 3.10 or newer.

```bash
git clone https://github.com/jremick/skill-library-reference-architecture.git
cd skill-library-reference-architecture
uv sync --locked
uv run skillref validate .
uv run python -m unittest discover -s tests -v
```

To compile a synthetic Level 2 profile after validation:

```bash
uv run skillref compile examples/level-2-retrieval \
  --profile standard \
  --output .artifacts/level-2-standard.json
```

Generated bundles are derived evidence. Edit manifests, registries, router maps,
or profiles instead of hand-editing compiled output.

## Documentation

- [Architecture](docs/architecture/README.md) — levels, contracts, and lifecycle.
- [Compatibility](docs/compatibility.md) — portable core and ecosystem adapters.
- [Security model](docs/security-model.md) — trust boundaries and fail-closed policy.
- [Evaluation](docs/evaluation.md) — deterministic routing checks and the
  evidence required for broader host evaluation.
- [Migration](docs/migration.md) — evidence-led movement between levels.
- [Specification](spec/README.md) — normative contract index.
- [Synthetic examples](examples/) — Level 0 through Level 3 fixtures.

## Deterministic controls and model judgment

In the normative architecture, deterministic code owns schema validation,
exact IDs and references, hard policy, conflict rules, lifecycle transitions,
digests, redaction, and release gates. Models may help interpret intent,
rerank already eligible candidates, review semantic overlap, and assess
qualitative output. Trust and compatibility filters are deterministic only
after an adapter supplies verified attributes as canonical inputs; the current
compiler does not independently attest either one.

The alpha CLI implements only a subset of those deterministic responsibilities.
Its routing evaluator measures selection, rejection, and exposure; lifecycle
execution and behavioral quality require evidence from the named host runtime.

A model decision cannot override a hard denial or convert missing evidence into
a passing result.

## Current status

This repository is in **public alpha** for inspection and trial use.
The following are expected to change before beta:

- Schema fields and compatibility rules.
- CLI command and report formats.
- Retrieval and routing-evaluation reference implementations.
- Adapter conventions as vendor products evolve.
- Telemetry event names while relevant external conventions remain unstable.

This repository does not claim that its examples prove real-world usability,
security, routing quality, or compatibility outside the tested fixtures.
`governance/promotion-policy.yaml` is a configurable reference checklist, not
an executable promotion engine or evidence that any deployment has passed its
gates.

A preserved one-shot independent candidate evaluation failed its strict gates:
it found a Level 0 false activation and included lifecycle/resource assertions
that the routing-only evaluator cannot establish. The development and held-out
suites pass, but they are not independent acceptance evidence. See the
[independent candidate record](evals/independent-candidate-v2/README.md) for the
unaltered input digest, recorded metrics, preservation limits, and claim limits.

There is no release, tag, package, stable compatibility promise, or host-runtime
implementation in this alpha.

## Community and support

- [Issues](https://github.com/jremick/skill-library-reference-architecture/issues) — reproducible bugs, documentation problems, and bounded architecture proposals.
- [Contributing](CONTRIBUTING.md) — setup, tests, privacy rules, and change expectations.
- [Security policy](SECURITY.md) — report vulnerabilities privately.

There is no guaranteed response time during alpha. General agent-tool support and
private environment troubleshooting are outside this repository's scope.

## License

Licensed under the [Apache License 2.0](LICENSE). Copyright 2026 Jarel Remick.
