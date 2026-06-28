# Agent Bindings

These files describe how different agent ecosystems can use Preserve Project Conversations.

The canonical runtime is the CLI:

```bash
paideia-memory ingest --project "my-project" --input conversation.md --vault memory-vault
paideia-memory make-notes --project "my-project" --vault memory-vault
paideia-memory library-index --vault memory-vault
```

The canonical memory remains the five-layer contract:

1. `01_raw_conversation.md`
2. `02_major_outline.md`
3. `03_minor_outline.md`
4. `04_summary.md`
5. `05_patterns.md`

Lecture notes and publishing exports are derived views over those five files.

## Files

- `openai.yaml`: UI metadata for OpenAI/Codex-style skill surfaces.
- `claude.md`: Claude/Anthropic-style skill loading note.
- `openclaw.yaml`: OpenClaw-oriented binding metadata.
- `hermes.yaml`: Hermes-oriented binding metadata.
