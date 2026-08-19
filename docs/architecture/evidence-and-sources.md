# Evidence and sources

Last reviewed: 2026-08-20.

This ledger separates current first-party evidence from architectural inference
and project recommendations. Vendor and standards documentation can change;
adapter maintainers should re-check dated behavior before making a current
compatibility claim.

## Primary evidence

| Area | Evidence-supported claim | Source |
| --- | --- | --- |
| Skill packaging | A skill minimally contains `SKILL.md`; scripts, references, and assets are optional. | [Agent Skills specification](https://agentskills.io/specification) |
| Progressive disclosure | The specification separates startup metadata, activated instructions, and resources loaded only as needed. Its size guidance is recommended rather than a universal architecture threshold. | [Agent Skills specification](https://agentskills.io/specification) |
| Ecosystem locations | GitHub documents several project and personal skill locations and supports Agent Skills across multiple Copilot surfaces. | [GitHub: About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) |
| Progressive discovery | MCP client guidance describes deferred definitions, lightweight search, and a catalog, inspect, execute pattern. | [MCP Client Best Practices, 2026-07-28](https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices) |
| Thresholds and strategies | MCP recommends locally configured context-share thresholds, gives a percentage range only as an example, and lists keyword, embedding, model/subagent, and hybrid discovery. | [MCP Client Best Practices, 2026-07-28](https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices) |
| OpenAI filtering | `tool_choice.allowed_tools` restricts the calls a model may make to a subset of declared tools; tool search separately supports deferred loading. | [OpenAI Function Calling](https://developers.openai.com/api/docs/guides/function-calling) |
| Anthropic deferred loading | `defer_loading: true` keeps a tool out of initial context until tool search returns and expands its reference. | [Claude Tool Search](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool) |
| Evaluation | Agent Skills guidance recommends clean-context runs, comparison with no skill or a previous version, concrete assertions, deterministic scripts for mechanical checks, and human review for qualities that resist objective checks. | [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills) |
| Telemetry privacy | OpenTelemetry's current GenAI guidance treats instructions, inputs, and outputs as potentially large and sensitive and recommends no default content capture without opt-in. | [OpenTelemetry GenAI spans](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md) |
| Versioning | Semantic Versioning requires a declared public API; `0.y.z` represents initial development and `1.0.0` defines the public API. | [Semantic Versioning 2.0.0](https://semver.org/) |

## Inference limits

- MCP, OpenAI, and Anthropic directly document tool discovery. Applying their
  mechanisms to procedural skill retrieval is an architectural inference, not
  proof that tool thresholds or accuracy gains transfer unchanged.
- Provider examples and numeric suggestions are not universal promotion gates.
- An allowed-tools subset constrains current callability; it does not by itself
  provide registry search, profile policy, or pre-retrieval authorization.
- OpenTelemetry supports interoperable telemetry naming, but a local-first,
  content-redacted skill event contract remains this project's policy choice.
- Independent schema and skill versions are a project design decision derived
  from change boundaries, not a requirement of the Agent Skills specification.

## Project recommendations

- Keep installed/cache, registered, eligible, prompt-visible,
  router-retrievable, retrieved, inspected, activated, resource-loaded,
  executed, and verified states distinct.
- Apply deterministic profile and permission denials before exact routing or
  semantic retrieval. Apply trust, lifecycle, and compatibility denials only
  when the adopting runtime or adapter supplies verified canonical attributes;
  do not infer an allow decision from missing evidence.
- Start with the simplest level that meets measured needs and promote only when
  held-out outcomes justify the added complexity.
- Keep thresholds configurable by task and risk class. Lower context cost is
  not sufficient evidence of better behavior.
- Collect structured outcomes and lifecycle events without raw prompts,
  credentials, unrestricted arguments, or tool results by default.
- Treat provider syntax and discovery locations as tested adapter claims.

These recommendations define the target architecture. The alpha routing
evaluator covers selection, rejection, and exposure only; lifecycle behavior,
resource use, task outcomes, telemetry effectiveness, and promotion require
separate host evidence.
