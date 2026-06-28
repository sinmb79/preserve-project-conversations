# Security Policy

## Supported Versions

The current `main` branch is supported for security fixes.

## Reporting a Vulnerability

Please do not disclose vulnerabilities publicly before there is time to assess them.

Open a private security advisory on GitHub when available, or contact the repository owner through GitHub.

## Security Boundaries

Preserve Project Conversations is local-first by design:

- It does not send transcripts to external services.
- Raw transcripts are preserved as evidence and should be treated as sensitive.
- Derived files mask high-confidence secret-like values, but masking is best-effort and should not replace human review.
- `export-share` excludes raw transcripts by default.
- `seal-vault` encrypts a share bundle only when the optional `crypto` dependency is installed.

## Safe Use

- Run `scan --target` before sharing a vault or source transcript.
- Prefer `export-share` over manual zipping.
- Use strong passwords for sealed bundles.
- Do not paste raw transcripts from untrusted sources into shell sessions.
