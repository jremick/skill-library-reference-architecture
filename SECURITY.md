# Security policy

## Supported versions

This project is an unreleased public alpha. Security fixes apply to the current
default branch only. There are no supported packages, release artifacts, or
historical version lines.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/jremick/skill-library-reference-architecture/security/advisories/new).
Do not open an issue for a suspected vulnerability, and do not include secrets,
private configuration, customer data, or exploit details in public discussions.

Useful reports include:

- The affected commit or file.
- A minimal synthetic reproduction.
- Expected and observed behavior.
- Potential impact, especially policy bypass, path traversal, unsafe parsing,
  information disclosure, or generated-output tampering.

Receipt and remediation times are not guaranteed during alpha. Confirmed issues
will be prioritized according to impact and exploitability.

## Security boundaries

The reference implementation parses untrusted manifests and configuration. It
must not execute bundled scripts, resolve secrets, make network calls, or grant
permissions during validation or compilation. Ecosystem adapters remain subject
to the security model of their host product.
