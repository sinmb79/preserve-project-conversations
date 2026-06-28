---
name: preserve-project-conversations
description: OpenClaw/Hermes-oriented skill for preserving agent chats and coding sessions as five-layer project memory, then turning that memory into lecture notes, development notes, searchable library entries, ebook drafts, blog posts, and tweet/thread drafts. Use for local-first continuity across agent sessions, owner-controlled knowledge libraries, and evidence-backed project documentation.
---

# Preserve Project Conversations for OpenClaw/Hermes

## Contract

Always keep the five-layer memory as the canonical record:

1. `01_raw_conversation.md`
2. `02_major_outline.md`
3. `03_minor_outline.md`
4. `04_summary.md`
5. `05_patterns.md`

Lecture notes are a study view over those five files. They are not a substitute for raw evidence.

## Agent Procedure

1. Capture the conversation, coding log, or task transcript locally.
2. Create or update the project vault:

```bash
paideia-memory ingest --project "project-name" --input transcript.md --vault memory-vault
```

3. Generate learning documents from the five layers:

```bash
paideia-memory make-notes --project "project-name" --vault memory-vault
```

4. Rebuild the owner library:

```bash
paideia-memory library-index --vault memory-vault
```

5. When the owner asks to publish or study:

```bash
paideia-memory export-book --project "project-name" --vault memory-vault --output book.md --include-development
paideia-memory export-post --project "project-name" --vault memory-vault --format blog --output post.md
paideia-memory export-post --project "project-name" --vault memory-vault --format tweet --output thread.txt
```

## Operating Style

- Prefer local storage and owner-controlled exports.
- Show the user the path to generated files.
- Use `library-search` before claiming something was or was not discussed.
- For development sessions, summarize the coding story as Planning -> Implementation -> Verification -> Release -> Patterns.
- Keep citations to raw message IDs or file paths so the user can jump from a summary back to evidence.
- Run `scan --target` before sharing any bundle outside the local machine.

## Handoff

For another LLM or agent, provide:

```bash
paideia-memory context --project "project-name" --vault memory-vault
```

Then attach the relevant `06_lecture_notes.md` or `_library/index.md` when the next agent needs study-note context.
