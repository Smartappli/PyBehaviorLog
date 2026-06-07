# Security Policy

## Supported Versions

Security fixes are prioritized for the current `main` branch and the latest
published release line. Older versions may receive fixes when the issue is
severe and the patch can be applied safely.

## Reporting a Vulnerability

Do not open a public issue with exploit details, credentials, private research
data, or sensitive deployment information.

Preferred reporting path:

1. Open the repository's **Security** tab on GitHub.
2. Use **Report a vulnerability** if private vulnerability reporting is
   available.
3. Include enough detail to reproduce the issue, affected versions or commits,
   and any relevant configuration.

If private reporting is unavailable, open a public issue with only a minimal
description and ask a maintainer for a private reporting channel. Do not include
proof-of-concept exploit code, secrets, database dumps, private media, or
research subject data in the public issue.

## Scope

Security reports are especially useful when they affect:

- authentication, authorization, project membership, or review permissions
- unsafe file import/export behavior
- exposure of uploaded media, observation data, or audit trails
- dependency, container, or deployment vulnerabilities
- cross-site scripting, cross-site request forgery, SQL injection, or template
  injection
- secret handling and production configuration

## Maintainer Response

Maintainers will triage reports based on severity, reproducibility, and affected
versions. Confirmed vulnerabilities should be fixed privately when practical,
then disclosed with release notes or an advisory once users have a reasonable
upgrade path.

