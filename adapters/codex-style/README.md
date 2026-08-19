# Codex-style adapter

This fixture uses `.agents/skills/<name>/SKILL.md` as an illustrative
project-scoped placement and keeps the canonical manifest outside the host skill
directory. It models the runtime pattern in which metadata is discoverable and
the body/resources are loaded when selected.

## Evidence and assumptions

Evidence reviewed 2026-08-20:

- OpenAI describes skills as reusable workflows containing instructions and
  supporting resources and says OpenAI Skills follow the Agent Skills open
  standard: [Skills in ChatGPT](https://help.openai.com/en/articles/20001066).
- The portable file contract is defined by the
  [Agent Skills specification](https://agentskills.io/specification).

Compatibility assumptions:

- This adapter does not claim that every Codex surface discovers project skills
  from `.agents/skills` or exposes identical installation semantics.
- The target Codex product/version must be checked before installation.
- Codex-specific plugin packaging, app dependencies, and workspace policy are
  outside this filesystem fixture.

See `fixture.yaml` for the portable-to-host mapping.
