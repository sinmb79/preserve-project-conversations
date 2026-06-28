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

## Quick Start

Requires Python 3.11+ and no third-party Python dependencies.

```bash
python scripts/paideia_memory.py ingest --project "my-project" --input path/to/conversation.md --vault path/to/memory-vault
```

Search saved memory:

```bash
python scripts/paideia_memory.py search --vault path/to/memory-vault --project "my-project" --query "small requirement"
```

Create a compact context packet for another LLM:

```bash
python scripts/paideia_memory.py context --vault path/to/memory-vault --project "my-project"
```

Scan before sharing:

```bash
python scripts/paideia_memory.py scan --target path/to/conversation.md
```

Rebuild project indexes:

```bash
python scripts/paideia_memory.py rebuild-index --vault path/to/memory-vault --project "my-project"
```

## Privacy and Safety

- Generated vaults are local by default.
- `runs/` and `memory-vault/` are ignored so private transcripts are not accidentally published.
- High-confidence secrets are preserved only in the raw file and masked in derived files.
- Use `--fail-on-secret` to abort ingest when secret-like patterns are detected.
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

## Status

This is an early, practical prototype. Pattern extraction is currently rule-based and evidence-oriented. It does not perform model-weight training or automatic reinforcement learning. Future work can add stronger semantic search, richer import adapters, and human-in-the-loop pattern review.

## License

No open-source license has been selected yet.
