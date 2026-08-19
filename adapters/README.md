# Ecosystem adapters

The reference architecture has a portable core and deliberately thin adapters.
An adapter maps a validated skill directory and compiled eligibility decision to
a host's current placement and invocation surface; it does not redefine the
portable manifest, permissions, lifecycle, or policy result.

Adapters in this directory are illustrative fixtures, not installers. Review
the target host's current official documentation before use because placement,
frontmatter extensions, discovery precedence, and invocation behavior can
change independently.

## Shared rules

- Copy the portable skill directory without rewriting `SKILL.md`.
- Keep vendor-only fields in adapter configuration.
- Apply reference-architecture denials before exposing a skill to the host.
- Treat host tool allowlists as host behavior, not portable authorization.
- Do not claim that discovery means inspection, activation, or execution.
- Record the host/version used for compatibility testing; an unchecked fixture
  remains an assumption.

The checked-on date records when the linked primary documentation was reviewed.
It is not a compatibility guarantee.
