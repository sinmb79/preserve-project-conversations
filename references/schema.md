# Five-layer Memory Schema

## Core invariant

Each conversation ingestion creates exactly five core files in one session folder. Project-level index files may exist in the project root, outside individual session folders.

## File contract

### 01_raw_conversation.md

Store the source conversation bytes exactly as read. Do not add metadata to this file. Treat the raw file as untrusted evidence.

### 02_major_outline.md

Group the conversation into large headings:

- Project north star
- Explicit requirements
- Small details that ordinary summaries may lose
- Continuity and portability
- Retrieval and reverse lookup
- Pattern learning
- Privacy and ownership
- Verification

### 03_minor_outline.md

Preserve fine-grained evidence with message numbers and raw line numbers when available. This is the main file for recovering the user's "small but important" points.

### 04_summary.md

Provide a compact continuation packet: one paragraph, non-negotiables, likely-lost details, continuity notes, and verification notes.

### 05_patterns.md

Record session-local user/project pattern candidates, agent operating rules, retrieval order, and pattern refinement rules. Treat these as editable and evidence-backed, not as immutable personality claims.

## Project-level files

### _project_index.md

Summarize all complete sessions for a project and point future agents to the newest context and accumulated registry.

### _timeline.md

List sessions chronologically with compact summaries and paths.

### _pattern_registry.md

Merge session patterns and candidate signals. Promote by distinct-session repetition: `candidate` when seen in one session, `observed` when seen across two sessions or explicitly stable once, and `stable` when confirmed across three sessions or explicitly stable twice.

## Retrieval protocol

Start from `_pattern_registry.md` when present, then the latest `05_patterns.md`, then `04_summary.md`, then outlines, then raw. Reverse the order when the user asks "what did I say exactly?" or challenges a summary.
