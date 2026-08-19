# Security policy

## Supported versions

This project is unreleased and preparing for public alpha. Security fixes apply
to the current default branch only. There are no supported packages, release
artifacts, or historical version lines.

## Reporting a vulnerability

This repository is pre-public and GitHub private vulnerability reporting is not
yet available. There is currently no public vulnerability-reporting endpoint.
Contributors who already have repository access should contact the maintainer
through an existing trusted private channel. Do not open an issue for a
suspected vulnerability and do not include secrets, private configuration,
customer data, or exploit details in public discussions.

GitHub private vulnerability reporting is available only after the repository
is public. The publication procedure is therefore two-phase: complete every
pre-public source and repository check; prepare this policy and the issue
configuration for the public reporting route; change visibility; then
immediately enable and read back private vulnerability reporting. The repository
must not be declared Stage 2 or announced until that live read-back succeeds.

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
