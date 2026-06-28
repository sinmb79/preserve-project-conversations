# Preserve Project Conversations Knowledge

Recommended CLI:

```bash
paideia-memory ingest --project "my-project" --input conversation.md --vault memory-vault
paideia-memory make-notes --project "my-project" --vault memory-vault
paideia-memory library-index --vault memory-vault
paideia-memory library-search --vault memory-vault --query "keyword"
paideia-memory export-book --project "my-project" --vault memory-vault --output book.md --include-development
paideia-memory export-post --project "my-project" --vault memory-vault --format blog --output post.md
paideia-memory export-post --project "my-project" --vault memory-vault --format tweet --output thread.txt
```

Generated core files:

- `01_raw_conversation.md`
- `02_major_outline.md`
- `03_minor_outline.md`
- `04_summary.md`
- `05_patterns.md`

Generated learning/library files:

- `06_lecture_notes.md`
- `07_development_notes.md`
- `_library/index.md`
- `_library/catalog.json`

Use raw files as evidence, derived files as navigation, and patterns as reviewed operating memory.
