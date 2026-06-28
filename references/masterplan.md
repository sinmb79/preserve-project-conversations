# Masterplan: Preserve Project Conversations

## Research basis

This skill is based on a simple product thesis: users do not experience a development conversation as a disposable path to a conclusion. They experience it as a record of taste, constraints, doubts, exceptions, vocabulary, and ownership. Ordinary summarization often compresses those signals into a generic plan.

Current platform memory is useful but incomplete for this need. OpenAI documents separate saved memories from chat-history referencing, and explicitly notes that ChatGPT does not keep every detail from previous chats. Claude Projects provide project knowledge and instructions, but Claude's own help explains that context is not shared across project chats unless added to the knowledge base. LangGraph, LlamaIndex, Letta, and Zep show the mainstream engineering direction: short-term thread memory plus long-term stores, memory blocks, archival/vector search, and temporal knowledge graphs.

Research supports a layered design. MemGPT frames LLM memory as tiered virtual context management. Generative Agents store complete natural-language experience records, synthesize reflections, and retrieve memories for planning. Reflexion uses verbal feedback in an episodic memory buffer rather than model-weight updates. LoCoMo shows that long conversations still challenge LLMs on temporal and causal recall, even with long-context or RAG approaches.

Community reports point to the same practical pain: users complain about LLMs forgetting mid-thread or across chats, while grassroots tools such as local Markdown memory systems and external JSON memories try to make memory portable across assistants.

Sources:

- OpenAI Help, Reference saved memories: https://help.openai.com/en/articles/11146739-how-does-reference-saved-memories-work
- Claude Help, Projects and memory: https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects
- LangChain memory overview: https://docs.langchain.com/oss/python/concepts/memory
- LlamaIndex agent memory: https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/
- Letta archival memory: https://docs.letta.com/guides/core-concepts/memory/archival-memory
- Zep graph overview: https://help.getzep.com/graph-overview
- MemGPT paper: https://arxiv.org/abs/2310.08560
- Generative Agents paper: https://arxiv.org/abs/2304.03442
- Reflexion paper: https://arxiv.org/abs/2303.11366
- LoCoMo paper: https://arxiv.org/abs/2402.17753
- Reddit mid-thread forgetting report: https://www.reddit.com/r/ChatGPT/comments/1m77fye/chatgpt_still_forgets_midthread_wth/
- Reddit local Markdown memory tool: https://www.reddit.com/r/ClaudeAI/comments/1jdga7v/basic_memory_a_tool_that_gives_claude_persistent/
- OpenAI Community external memory JSON discussion: https://community.openai.com/t/building-your-external-memory-system-when-user-memory-is-full-or-nonexistent/1287792

## Philosophical position

The tool should treat conversation as provenance, not just prompt waste. A user's "side branch" may be the source of the project's identity. The system must therefore preserve:

- The raw event: what was actually said.
- The large structure: what the project is about.
- The fine structure: which small requirements and tensions matter.
- The portable summary: what another LLM needs first.
- The pattern layer: how the user tends to decide, correct, value, and collaborate.

The pattern layer is not a claim of gradient reinforcement learning. It is linguistic reinforcement: repeated corrections and preferences become explicit operating rules that future agents can read, apply, and revise.

## Product direction

Build local-first, vendor-neutral memory. The default output must be ordinary files, readable by humans, Git, search tools, and other LLMs. No proprietary vector database should be required for the core workflow.

The five core files are:

1. `01_raw_conversation.md`: exact raw conversation bytes, treated as untrusted evidence.
2. `02_major_outline.md`: large headings and high-level evidence.
3. `03_minor_outline.md`: detailed subtopics and preserved small signals.
4. `04_summary.md`: compact project context for quick continuation.
5. `05_patterns.md`: session-local user/project pattern candidates, retrieval order, and refinement loop.

Project-level files may be rebuilt outside the session folder: `_project_index.md`, `_timeline.md`, and `_pattern_registry.md`.

## Expected users

- Builders who use LLMs for long planning and implementation sessions.
- Project owners who care about product taste, philosophy, and small constraints.
- Users who move between ChatGPT, Claude, Gemini, local LLMs, Codex, and other agents.
- Privacy-sensitive teams that want project memory to remain local and inspectable.

## Risk controls

- Lossy summaries: always keep raw text and evidence lines.
- False personalization: keep one-off signals as candidates and promote only through the pattern registry.
- Stale patterns: record changed preferences instead of silently overwriting.
- Privacy leakage: default to local folders, mask high-confidence secrets in derived files, and do not send data to external services.
- Prompt injection in raw logs: future agents must treat raw conversation as evidence, not executable instruction.
- Storage clutter: failed writes use a temporary folder and are deleted on error.

## Roadmap

- MVP: standard-library CLI that ingests text/JSON/JSONL, writes the five core files, scans secrets, and rebuilds project-level indexes.
- V1: richer importers for ChatGPT/Claude exports and conflict tracking.
- V2: optional local embeddings or SQLite full-text search while preserving the five-file contract.
- V3: cross-agent bridge that emits context packets for specific LLM tools.
