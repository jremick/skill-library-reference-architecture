# Security model

The architecture defines controls intended to limit which skills and resources
can reach model context or execution. It does not make untrusted instructions
safe merely by packaging them as a skill.

The alpha CLI is not a host security boundary. It validates repository
documents, compiles canonical profile and permission inputs, and evaluates
deterministic routing selection, rejection, and exposure. It does not attest
trust, verify host compatibility, load or execute resources, operate lifecycle
transitions, collect telemetry, or make promotion decisions.

## Protected assets

- user and organization data;
- credentials and authentication material;
- permissions and approval boundaries;
- model context and routing integrity;
- skill, registry, policy, and compiler provenance;
- execution environments and connected systems; and
- telemetry and evaluation evidence.

## Trust boundaries

1. **Package boundary:** downloaded or contributed skill content is untrusted
   until validated and reviewed.
2. **Registry boundary:** only content-bound, provenance-aware records enter the
   canonical inventory.
3. **Policy boundary:** profile and permission denials are applied before
   retrieval or model ranking. Trust, lifecycle, and compatibility denials join
   this boundary only when a host or adapter supplies verified canonical
   attributes.
4. **Model boundary:** retrieved instructions and tool results are untrusted
   input; a model cannot grant itself more authority.
5. **Execution boundary:** scripts and tools run with the minimum permitted
   capability, separate from model interpretation.
6. **Telemetry boundary:** collection is local-first and excludes sensitive
   content by default.

## Primary threats and controls

| Threat | Required controls |
| --- | --- |
| Prompt or instruction injection | Treat skill text, references, and tool results as data from a named source; enforce hard policy outside the model; test adversarial fixtures. |
| Unauthorized discovery | Filter before indexing, search, or semantic ranking; return no metadata for denied records unless policy explicitly allows disclosure. |
| Privilege escalation | Bind activation to a policy decision and immutable version; require fresh authorization for material side effects. |
| Dependency or alias confusion | Resolve canonical IDs and digests deterministically; reject cycles, ambiguous aliases, and undeclared dependencies. |
| Malicious scripts/assets | Validate paths and digests; separate inspection from execution; sandbox where supported; enforce time, network, file, and output limits. |
| Cross-skill data flow | Treat outputs as untrusted inputs; apply destination policy and data-handling rules on every transition. |
| Supply-chain substitution | Record provenance and content digests; verify releases; quarantine changed or unowned content. |
| Telemetry leakage | Use allowlisted structured fields, redaction, retention limits, and local aggregation; exclude raw prompts, credentials, tool arguments, and results by default. |
| Stale generated surfaces | Bind generated profiles, indexes, and routers to source digests; fail validation on drift. |
| Misleading success claims | Record executed and verified as separate states; retain denied, failed, partial, and skipped results. |

## Policy order

For a conforming host, the minimum safe order is:

```text
validate provenance and schema
  -> apply canonical profile and permission denials
  -> apply verified trust/lifecycle/compatibility denials when supplied
  -> expose only eligible metadata to exact routing or retrieval
  -> inspect and pin a candidate
  -> re-check conflicts and execution authority
  -> activate with least privilege
  -> verify outcome and emit redacted telemetry
```

Retrieval does not grant permission, and approving model-authored orchestration
does not grant blanket approval to every nested action. The host or broker
evaluates each call against the granted scope.

The current compiler cannot infer a trustworthy host-compatibility or trust
decision from descriptive metadata. An adapter must verify and supply those
attributes, and an unknown required value must fail closed.

The current [MCP client security guidance](https://modelcontextprotocol.io/docs/develop/clients/client-best-practices)
similarly recommends per-call authorization, brokered credentials, network
isolation for programmatic tool execution, resource limits, and output
filtering. This is supporting evidence for the controls, not a claim that every
skill runtime implements MCP.

## Telemetry privacy

Collect stable IDs, versions, ranks, state transitions, durations, aggregate
cost, outcome labels, verification status, corrections, and rollback decisions.
Do not collect raw prompts, credentials, unrestricted arguments, or tool results
by default. Any opt-in content capture requires a separate purpose, consent,
retention, and access-control decision.

OpenTelemetry provides common semantic-convention machinery, but its GenAI
surface is evolving. This project therefore versions its telemetry contract and
treats provider mappings as adapters rather than copying unstable fields into
the portable core. See the
[OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/).

The presence of the telemetry schema does not mean that the CLI collects events
or that telemetry improves outcomes. Both collection and effectiveness require
runtime evidence and comparison with a simpler baseline.

## Stop and rollback conditions

An adopting implementation should stop promotion when a denial can reach
model-visible search results, a runtime cannot represent a required approval
boundary, provenance is unresolved,
telemetry requires sensitive content to function, or rollback cannot restore a
known-good bundle. Quarantine affected versions and preserve failure evidence.
The repository policy records this as a reference checklist; it is not an
executable promotion or rollback controller.
