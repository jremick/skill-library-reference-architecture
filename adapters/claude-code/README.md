# Claude Code adapter

Place a portable skill directory at `.claude/skills/<name>/`. Keep
Claude-specific invocation controls in adapter configuration unless the
portable skill intentionally adopts them as an extension.

## Evidence and assumptions

Evidence reviewed 2026-08-20:

- Claude Code documents project skills at `.claude/skills/<name>/SKILL.md`,
  automatic metadata discovery, on-demand content loading, and optional
  supporting resources: [Extend Claude with skills](https://code.claude.com/docs/en/skills).

Compatibility assumptions:

- `disable-model-invocation`, `allowed-tools`, dynamic context injection, and
  forked execution are Claude extensions, not portable core fields here.
- Claude's skill filter is not a filesystem sandbox; the reference policy must
  still make eligibility decisions before exposure.
- Placement documentation does not prove behavior in an untested Claude Code or
  Agent SDK version.
