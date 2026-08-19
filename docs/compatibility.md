# Compatibility

Compatibility is a tested claim about a named contract and adapter version. It
is not implied by sharing a file extension or directory name.

The alpha CLI does not make a host-compatibility claim. A compatibility or
trust filter can be enforced only after an adapter supplies the relevant
verified attributes as canonical inputs; the compiler does not discover or
attest them on its own.

## Portable core

The portable core should preserve:

- a manifest with stable identity and a useful selection description;
- primary Markdown instructions;
- named scripts, references, assets, and examples;
- progressive-disclosure conditions;
- compatibility and risk metadata;
- immutable versions or digests; and
- expected evaluation cases.

The [Agent Skills specification](https://agentskills.io/specification) is the
baseline packaging reference. This project adds registry, policy, lifecycle,
telemetry, and evaluation contracts around that baseline; those additions are
reference-architecture contracts, not claims about the upstream standard.

## Adapter boundary

An adapter may translate:

- discovery locations and naming rules;
- manifest fields or provider metadata;
- tool and permission syntax;
- how instructions enter model context;
- how supporting resources are resolved;
- activation and execution evidence; and
- provider-specific lifecycle events.

An adapter must not silently change skill meaning, widen permissions, or report
an unsupported lifecycle state as verified. Unsupported fields remain explicit.

GitHub currently documents project skills in `.github/skills`, `.claude/skills`,
or `.agents/skills`, plus selected personal locations. That is current evidence
for one ecosystem, not a portable path rule. See
[GitHub's Agent Skills documentation](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills).

## Compatibility statuses

| Status | Meaning |
| --- | --- |
| Native | The adapter preserves the contract without transformation beyond location or syntax. |
| Translated | A documented mapping preserves tested behavior but changes representation. |
| Partial | Some fields or lifecycle states are unsupported and named explicitly. |
| Experimental | The mapping exists but lacks the required held-out or runtime evidence. |
| Unsupported | The adapter refuses the operation rather than approximating it. |

## Minimum compatibility evidence

The following is required before an adapter claims the corresponding host
compatibility. It is not evidence already produced by the reference CLI.

For each adapter and supported level:

1. validate synthetic positive and negative fixtures;
2. compile the same source twice and compare content-bound outputs;
3. confirm hard denials remain outside model-visible retrieval results;
4. verify resource loading and activation states separately;
5. run held-out behavioural cases in the named runtime when available;
6. record provider version and test date; and
7. preserve partial, skipped, or unavailable runtime checks as limitations.

## Claim limits

Schema validity proves structure, not behavioral parity. A clean compile proves
reproducibility, not correct routing. A provider accepting an adapter output does
not prove that it will select or execute the skill correctly. Compatibility
claims therefore name the exact evidence layer they cover.

Likewise, the deterministic routing evaluator covers selection, rejection, and
exposure only. Resource loading, lifecycle transitions, execution, and
behavioral outcomes require evidence captured in the named host runtime.
