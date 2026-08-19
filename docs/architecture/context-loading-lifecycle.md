# Context-loading lifecycle

The lifecycle prevents ambiguous claims such as "the skill is available" from
collapsing several different states.

This is the normative lifecycle and evidence vocabulary. The alpha CLI does
not drive or observe a host through these transitions. It can compile exposure
states and evaluate deterministic selection, rejection, and exposure, but
later states require host-produced evidence.

| State | Meaning | Required evidence |
| --- | --- | --- |
| Cached | Bytes are available in a local or remote cache but are not necessarily installed. | Cache observation and content digest. |
| Installed | The skill package is available to the runtime but is not necessarily registered. | Installation observation and package identity. |
| Registered | A validated registry record refers to the skill. | Registry ID and manifest digest. |
| Eligible | The available canonical policy inputs allow consideration. Profile and permission checks are core inputs; trust and compatibility require adapter-supplied verified attributes. | Deterministic policy decision naming the inputs used. |
| Prompt-visible | Metadata is present in the model's current prompt surface. | Runtime prompt inspection or equivalent host evidence. |
| Router-retrievable | A router or catalog can locate the record without putting the leaf in the prompt. | Router/catalog lookup result. |
| Retrieved candidate | Search returned the skill for a particular request. | Query ID, rank, and retrieval evidence. |
| Inspected | Full instructions or the candidate contract were read for selection. | Inspected version and digest. |
| Activated | A resolved, allowed, conflict-free version is bound to the task. | Activation record and policy decision. |
| Conditionally loaded | A named reference, script description, asset, or example entered context or execution scope. | Resource ID, reason, and digest. |
| Executing | An allowed skill-directed operation is in progress. | Structured transition and execution scope. |
| Verified | Outcome-specific checks completed. | Check result, limitations, and evidence references. |
| Deactivated/cached | The binding ended; reusable host-side data may remain cached. | End state and cache scope. |

## Transition rules

- Denials occur before search or semantic ranking.
- Prompt-visible and router-retrievable are separate branches. A record can be
  one, both, or neither depending on the configured level.
- Retrieval never grants permission. It only proposes eligible candidates.
- Inspection never implies activation.
- Activation pins an immutable version or digest for the task.
- A supporting resource is loaded only when a documented condition is met.
- Execution and verification are separate; a successful process exit is not a
  user-outcome claim.
- Every failure remains explicit. A partial, denied, skipped, or unknown state
  is not converted to success.

## State-machine text equivalent

In a conforming runtime, the normal path starts with cached or installed
material, validates an exact manifest reference into the registry,
filters it for eligibility, exposes it directly or through retrieval, inspects
candidate details, resolves conflicts, activates one pinned version, loads only
needed resources, executes work, verifies the outcome, and finally deactivates
the binding. Any denial or validation failure stops the path before model
selection. Execution or verification failure records the failure and may send
the task back to candidate selection without rewriting history.

The routing evaluator does not infer that inspection, activation, conditional
loading, execution, or verification occurred. Those claims need transition or
runtime evidence from the host.

See the canonical [lifecycle diagram](../diagrams/src/context-loading-lifecycle.mmd).
