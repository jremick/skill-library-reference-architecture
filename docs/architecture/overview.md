# Architecture overview

## Purpose

This project provides a reusable architecture for growing an AI skill library
without treating every installed skill as permanent model context. It supports
a path from a small flat library to a retrieval-served platform with policy,
telemetry, evaluation, lifecycle controls, and rollback.

Those capabilities describe the reference architecture, not the current CLI's
runtime coverage. The alpha CLI validates repository contracts, compiles a
profile-filtered catalog, and evaluates deterministic routing selection,
rejection, and exposure. Host lifecycle execution, resource loading, trust
attestation, compatibility verification, telemetry collection, behavioral
evaluation, and promotion remain responsibilities of a named host or adapter.

The intended audience is maintainers of personal, team, and platform skill
libraries; agent-runtime builders; and practitioners responsible for context,
security, evaluation, or governance.

## Scope

The architecture covers:

- portable skill packaging and progressive disclosure;
- registration, routing, retrieval, inspection, and activation;
- profile, trust, and permission filtering;
- conflict, dependency, version, and lifecycle handling;
- local-first telemetry and evaluation;
- migration between four independently usable architecture levels; and
- provider adapters and synthetic conformance examples.

It does not define a hosted marketplace, a general agent framework, a model
training system, an authentication product, or a replacement for tool
protocols. It also does not promise semantic parity across agent runtimes.

## Reference flow

```text
installed or cached
  -> registered
  -> policy-eligible
  -> prompt-visible or router-retrievable
  -> retrieved candidate
  -> inspected
  -> conflict-resolved and version-pinned
  -> activated
  -> conditionally loaded resources
  -> executed
  -> verified
  -> measured
```

Every arrow is an observable transition. A system may stop before any later
state without implying that the later state occurred.

## Evidence, inference, and recommendation

### Evidence

- The [Agent Skills specification](https://agentskills.io/specification)
  defines a minimal `SKILL.md`, optional scripts, references, and assets, and a
  progressive-disclosure model in which more detail is loaded when needed.
- [GitHub's Agent Skills documentation](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
  describes Agent Skills as an open standard and documents several supported
  project and personal locations. This confirms that ecosystem placement is
  not uniform.
- The [MCP client best-practices guide](https://modelcontextprotocol.io/docs/develop/clients/client-best-practices)
  documents progressive tool discovery and a catalog, inspect, execute pattern.
  It recommends configurable thresholds and presents a context percentage as
  an example rather than a law.
- OpenAI documents an
  [allowed-tools subset](https://developers.openai.com/api/docs/guides/function-calling)
  and Anthropic documents
  [deferred tool discovery](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool).
  These are provider-specific examples of late binding and filtered exposure.

### Inference

Tool discovery and skill activation are not identical. Tool-retrieval guidance
supports the feasibility of filtered catalogs and late loading, but does not by
itself prove that the same thresholds or retrieval methods work for procedural
skill instructions. The project therefore treats those patterns as hypotheses
to evaluate against skill-specific tasks.

### Recommendation

Start at the simplest level that meets measured requirements. Promote only
when a more complex level improves held-out task outcomes, policy enforcement,
or operational control enough to justify its latency and maintenance cost.

## Sources of truth

- `spec/`: normative terms and contracts.
- `schemas/`: machine-readable validation contracts.
- `governance/promotion-policy.yaml`: a configurable, non-executable reference
  checklist for local promotion and rollback decisions.
- `examples/`: synthetic conformance fixtures.
- `src/skillref/`: deterministic validation and compilation behavior.

Generated artifacts must identify their source digest. They are evidence of a
build, not a second source to edit by hand.

See [Evidence and sources](evidence-and-sources.md) for the dated source ledger
and claim limits.
