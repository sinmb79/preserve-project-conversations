# Skillpack Guide

Preserve Project Conversations can be used as a CLI, as a Claude/Anthropic-style `SKILL.md` folder, as an OpenClaw/Hermes-style local agent skill, or as ChatGPT GPT instructions.

## Principle

The canonical memory remains the five-layer contract:

1. `01_raw_conversation.md`
2. `02_major_outline.md`
3. `03_minor_outline.md`
4. `04_summary.md`
5. `05_patterns.md`

Lecture notes, development notes, libraries, ebooks, blog drafts, and tweet/thread drafts are derived views over those five files.

## Claude/Anthropic-Style Skill

Use:

```text
skillpacks/anthropic-claude/preserve-project-conversations/
```

Copy that folder into the target agent's skills directory or point the agent at it. The folder contains a `SKILL.md` with the five-layer workflow and publishing commands.

## OpenClaw/Hermes Skill

Use:

```text
skillpacks/openclaw-hermes/preserve-project-conversations/
```

This version emphasizes local-first agent continuity, owner-controlled exports, and handoff through `paideia-memory context`.

## ChatGPT GPT Package

Use:

```text
skillpacks/chatgpt-gpt/instructions.md
skillpacks/chatgpt-gpt/knowledge.md
```

Paste `instructions.md` into the GPT instruction field and upload or paste `knowledge.md` as reference knowledge. If the GPT can call tools or actions, wire those actions to a runtime that can execute `paideia-memory`.

## Common Commands

```bash
paideia-memory ingest --project "my-project" --input conversation.md --vault memory-vault
paideia-memory make-notes --project "my-project" --vault memory-vault
paideia-memory library-index --vault memory-vault
paideia-memory library-search --vault memory-vault --query "keyword"
paideia-memory export-book --project "my-project" --vault memory-vault --output book.md --include-development
paideia-memory export-post --project "my-project" --vault memory-vault --format blog --output post.md
paideia-memory export-post --project "my-project" --vault memory-vault --format tweet --output thread.txt
```

Run `paideia-memory scan --target .` before public sharing.
