# Changelog

All notable changes to Preserve Project Conversations are documented here.

## v0.2.1 - 2026-06-28

### Changed

- Expanded `scan --target` to cover source and configuration files (`.py`, `.toml`, `.yml`, `.yaml`, `.ini`, `.cfg`) in addition to conversation/document files.
- Added release and PyPI publishing guidance for local checks, GitHub Releases, Trusted Publisher setup, and Windows UTF-8 console use.

### Security

- Reduced repository-scan blind spots before public release by checking common code and workflow file types.

## v0.2.0 - 2026-06-28

### Added

- Installable Python package metadata and `paideia-memory` console script.
- MIT license.
- GitHub Actions CI on Ubuntu and Windows for Python 3.11 and 3.12.
- ChatGPT, Claude-style, Gemini-style, and generic message export parsing improvements.
- Human pattern review workflow with `review-patterns` and `promote-pattern`.
- Local n-gram similarity search with `semantic-search`.
- Redacted share zip generation with `export-share`.
- Optional encrypted share bundle support with `seal-vault` and `unseal-vault`.
- UTF-8-safe CLI output on Windows CI.

### Changed

- Expanded README and Korean README with installation, sharing, pattern review, and encryption usage.
- Strengthened regression tests from 11 to 16 cases.

### Security

- Share exports exclude raw transcripts by default.
- Derived files are redacted again during share export.
- Optional sealed bundles require the `crypto` extra and a password supplied by environment variable or secure prompt.

## v0.1.0 - 2026-06-28

### Added

- Initial public release.
- Five-file memory session contract.
- Project-level index, timeline, and pattern registry.
- Secret-like value scanning and masking for derived files.
- Exact raw source byte preservation.
- Basic search and context packet generation.
