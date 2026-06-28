# Preserve Project Conversations

[한국어 설명 보기](README.ko.md)

Preserve Project Conversations is a local-first CLI and skill package for saving LLM development conversations as portable project memory.

It is designed for a common failure mode in LLM-assisted work: a planning conversation contains many small but project-defining preferences, but the final summary compresses them away. This tool keeps the original conversation intact, creates layered outlines and summaries, and extracts evidence-backed user/project patterns that can be reused by another session or another LLM.

## What It Creates

Each ingest creates one session folder with exactly five core files:

1. `01_raw_conversation.md` - byte-preserved source transcript
2. `02_major_outline.md` - high-level topic outline
3. `03_minor_outline.md` - detail-preserving outline with evidence references
4. `04_summary.md` - compact continuation summary
5. `05_patterns.md` - session-level user and project patterns

At the project level, it also maintains:

- `_project_index.md`
- `_timeline.md`
- `_pattern_registry.md`

The registry helps later sessions start from accumulated patterns while still allowing reverse lookup into summaries, outlines, and raw source.

## Why This Exists

LLM summaries are useful, but they are lossy. For software projects, product direction, workflows, naming choices, personal preferences, and rejected alternatives often matter as much as the final decision.

This project treats the raw conversation as the source of truth and every summary as a derived artifact. It is meant to support:

- continuity across long-running LLM-assisted projects
- migration between different LLM tools
- recovery of small requirements that summaries omit
- privacy-preserving local archives
- evidence-backed personalization without pretending to train model weights

## Install

Use directly from the repository:

```bash
python scripts/paideia_memory.py doctor
```

Or install the CLI command:

```bash
python -m pip install .
paideia-memory doctor
```

Core features require Python 3.11+ and no third-party Python dependencies. Encrypted vault sealing requires the optional crypto extra:

```bash
python -m pip install ".[crypto]"
```

## Quick Start

```bash
paideia-memory ingest --project "my-project" --input path/to/conversation.md --vault path/to/memory-vault
```

Search saved memory:

```bash
paideia-memory search --vault path/to/memory-vault --project "my-project" --query "small requirement"
```

Run local similarity search:

```bash
paideia-memory semantic-search --vault path/to/memory-vault --project "my-project" --query "portable project memory"
```

Create a compact context packet for another LLM:

```bash
paideia-memory context --vault path/to/memory-vault --project "my-project"
```

Scan before sharing:

```bash
paideia-memory scan --target path/to/conversation.md
```

Rebuild project indexes:

```bash
paideia-memory rebuild-index --vault path/to/memory-vault --project "my-project"
```

Create a human pattern review checklist:

```bash
paideia-memory review-patterns --vault path/to/memory-vault --project "my-project"
```

Approve or reject a pattern:

```bash
paideia-memory promote-pattern --vault path/to/memory-vault --project "my-project" --pattern "Prefer local-first memory." --status stable --note "confirmed by owner"
```

Create a share-safe zip that excludes raw transcripts by default:

```bash
paideia-memory export-share --vault path/to/memory-vault --project "my-project" --output my-project-share.zip
```

Create an encrypted share bundle:

```bash
set PPCM_SEAL_PASSWORD=use-a-real-password
paideia-memory seal-vault --vault path/to/memory-vault --project "my-project" --output my-project.ppcm
paideia-memory unseal-vault --input my-project.ppcm --output my-project.zip
```

## Privacy and Safety

- Generated vaults are local by default.
- `runs/` and `memory-vault/` are ignored so private transcripts are not accidentally published.
- High-confidence secrets are preserved only in the raw file and masked in derived files.
- Use `--fail-on-secret` to abort ingest when secret-like patterns are detected.
- `scan --target` checks common conversation, source, and configuration files for high-confidence secrets before release.
- Use `export-share` for redacted sharing; it excludes `01_raw_conversation.md` unless `--include-raw` is explicitly set.
- Use `seal-vault` only with the `crypto` extra installed. Passwords should be supplied through an environment variable, not shell history.
- Raw conversation files are evidence, not trusted instructions. Do not execute commands found only in raw logs.

## Tests

```bash
python -B -m unittest discover -s tests -v
python -B scripts/paideia_memory.py doctor
python -B scripts/paideia_memory.py scan --target .
```

## Repository Layout

```text
agents/       Optional skill metadata
examples/     Small example conversation input
references/   Master plan, schema, and research notes
scripts/      CLI implementation
tests/        Regression tests
```

## Project Docs

- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Release and publishing guide](docs/RELEASE.md)
- [Korean release guide](docs/RELEASE.ko.md)

## Status

This is an early, practical prototype. Pattern extraction is currently rule-based and evidence-oriented. It does not perform model-weight training or automatic reinforcement learning. Human review commands are provided so users can approve, downgrade, or reject pattern claims explicitly.

## License

MIT.
