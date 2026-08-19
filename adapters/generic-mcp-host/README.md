# Generic MCP-host adapter

MCP standardizes tool and resource protocol surfaces; it does not define this
repository's skill manifest, registry, eligibility, or activation lifecycle.
This adapter therefore exposes reference-architecture discovery operations as
illustrative MCP tools and keeps policy enforcement server-side.

Illustrative flow:

```text
tools/list -> skill_catalog.search -> skill_catalog.inspect
-> skill_catalog.activate -> host loads the pinned portable skill
```

## Evidence and assumptions

Evidence reviewed 2026-08-20:

- MCP defines `tools/list` for discovery and `tools/call` for invocation:
  [MCP schema reference](https://modelcontextprotocol.io/specification/2025-06-18/schema).
- MCP tool annotations are hints and must not be trusted for access-control
  decisions; the schema explicitly warns clients against doing so.

Compatibility assumptions:

- `skill_catalog.*` names and payloads are an example extension, not standard
  MCP methods.
- The server filters by profile and permission before returning search results.
- The host separately implements pinned content loading and lifecycle events.
- A successful MCP call does not prove task quality or end-to-end policy
  enforcement.
