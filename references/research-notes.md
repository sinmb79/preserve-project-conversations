# Research Notes

## Product and framework map

- OpenAI ChatGPT memory is convenient, but platform-managed and not guaranteed to retain every detail.
- Claude Projects are useful for project knowledge, but cross-chat context depends on project knowledge and memory summaries.
- LangGraph and LlamaIndex provide practical memory abstractions for agents, but they are framework-specific.
- Letta/MemGPT focuses on memory tiers and agent-controlled memory management.
- Zep focuses on temporal knowledge graphs for changing facts and relationships.
- Local Markdown and JSON memory tools show user demand for portable memory outside one vendor.

## Design conclusion

The first implementation should not compete with those systems. It should create the durable source-of-truth artifact they can all consume: raw conversation plus human-readable hierarchy, summary, and pattern rules.

## Evaluation checklist

- Does the raw file remain exact?
- Are all five core files present?
- Does the summary preserve explicit requirements?
- Does the pattern file avoid overclaiming model-weight learning?
- Can the owner promote, downgrade, or reject patterns explicitly?
- Can search recover a small requirement from either summary, outline, or raw?
- Can local similarity search recover related wording without a remote service?
- Are high-confidence secrets masked in derived files and preserved only in raw evidence?
- Does share export exclude raw transcripts by default and redact included derived files again?
- Can sealed export decrypt back into a readable share bundle with the correct password?
- Do repeated sessions update `_pattern_registry.md`, `_timeline.md`, and `_project_index.md`?
- Does malformed JSON fail clearly instead of creating misleading memory?
