# GitHub Copilot adapter

Place a portable project skill at `.github/skills/<name>/SKILL.md`. GitHub also
documents `.agents/skills` and `.claude/skills` as accepted project locations;
this fixture selects one location to avoid duplicate-name precedence ambiguity.

## Evidence and assumptions

Evidence reviewed 2026-08-20:

- GitHub documents the three project placements, required `name` and
  `description` frontmatter, optional resources, and model-selected loading:
  [Adding agent skills for GitHub Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills).

Compatibility assumptions:

- GitHub product surfaces do not necessarily expose identical skill behavior.
- `allowed-tools` is a GitHub host extension and is intentionally omitted from
  the portable example.
- A host-supported placement is not evidence that reference-architecture
  profile filters or lifecycle telemetry are enforced by GitHub.
