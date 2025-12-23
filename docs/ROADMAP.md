# X-Bookmark Knowledge Repository - Roadmap & Planning

> Last updated: 2024-12-23

## Current State (v1.0)

### What's Built
- **Telegram Bot**: Send X posts directly from mobile → bot archives with metadata
- **Twitter Fetcher**: Pulls full threads via free APIs (FxTwitter/VxTwitter)
- **File-based Archive**: Markdown files with YAML frontmatter, organized by date
- **Metadata System**: Tags, topics, notes, importance levels
- **Search CLI**: Keyword search with filtering by author/tags/topics/importance
- **Export Tools**: Multiple formats including LLM-optimized XML output

### Architecture
```
User → Telegram Bot → Twitter Fetcher → Markdown Files → Index JSON
                                              ↓
                                      Search/Export Tools
```

---

## Future Vision

**End Goal**: A queryable personal knowledge base that helps generate insights and content through natural language interaction (RAG-powered).

---

## Planned Enhancements

### Priority 1: Semantic Search with Embeddings ✅ APPROVED

**Why**: Keyword search is limited. We want to find posts by *meaning*, not just exact words.

**Capabilities**:
- Natural language queries ("what did I save about transformer architectures?")
- Find conceptually similar posts
- Better retrieval for RAG pipeline

**Implementation Options**:
| Option | Pros | Cons |
|--------|------|------|
| Local embeddings (sentence-transformers) | Free, private, offline | Requires Python ML stack |
| OpenAI embeddings API | High quality, simple | Cost per request, requires API key |
| Local Ollama | Free, private, good quality | Requires Ollama running |

**Storage**: Vector store options - ChromaDB (simple), Qdrant (performant), or plain JSON with numpy.

**Decision**: TBD

---

### Priority 2: RAG Integration ✅ APPROVED

**Why**: The ultimate goal - chat with your bookmarks, generate insights, create content from your curated knowledge.

**Capabilities**:
- Ask questions, get answers citing your archived posts
- Generate content based on saved knowledge
- Surface forgotten insights when relevant

**Implementation Options**:
| Option | Pros | Cons |
|--------|------|------|
| Custom RAG pipeline | Full control, tailored to our data | More work to build |
| LangChain/LlamaIndex | Battle-tested, many integrations | Complexity, dependencies |
| Claude with tool use | Native conversation, high quality | API costs |

**Depends on**: Semantic search (embeddings) should be built first.

**Decision**: TBD - discuss implementation approach

---

### Priority 3: Auto-Tagging with LLM ✅ APPROVED

**Why**: Manual tagging is friction. LLM can suggest tags based on content, user just confirms.

**Capabilities**:
- Bot suggests tags/topics after fetching post
- User can accept, modify, or override
- Consistent tagging vocabulary over time

**Implementation Options**:
| Option | Pros | Cons |
|--------|------|------|
| Claude API | High quality suggestions | Cost per request |
| Local LLM (Ollama) | Free, private | Quality varies, needs local setup |
| Simple keyword extraction | No API needed | Less intelligent |

**Integration point**: Telegram bot conversation flow

**Decision**: TBD

---

### Priority 4: Frontend / User Interface 🔜 SEPARATE DISCUSSION

**Status**: User has specific ideas - to be discussed in dedicated planning session.

**Notes**: Keep architecture frontend-agnostic. Current file-based storage + JSON index should support various frontend approaches.

---

### Deferred: Media Archival ⏸️ ON HOLD

**The Problem**: Media URLs can go stale if tweets are deleted.

**User Constraint**: Uses multiple devices (iPhone, MacBook, Windows Desktop) - local storage won't sync.

**Options Considered**:
| Option | Pros | Cons |
|--------|------|------|
| Cloud storage (S3/R2) | Cross-device, permanent | Cost, complexity |
| Git LFS | Version controlled | Storage limits, not for large video |
| Accept the risk | Simple | Media may be lost |

**Decision**: **Deferred** - accept media loss risk for now. URLs preserved in archive; most value is in text content anyway. Revisit if this becomes a pain point.

---

### Deferred: Collections/Folders ❌ NOT PURSUING

**Reasoning**: For RAG-based retrieval, flexible multi-tag systems outperform rigid hierarchies.

- A post can have many tags but only one folder
- RAG benefits from overlapping, rich metadata
- Folders would restrict, not enhance, our retrieval capabilities

**Decision**: **Not needed** - current tag/topic system is better suited for RAG use case.

---

### Deferred: Scheduled Exports ⏸️ LATER

**What**: Cron job to auto-generate fresh LLM context files.

**Decision**: **Not needed yet** - revisit once RAG is built and usage patterns are clear.

---

## Implementation Order

```
Phase 1: Semantic Search
    └── Add embedding generation for posts
    └── Build vector store
    └── Create semantic search CLI

Phase 2: RAG Pipeline
    └── Design retrieval strategy
    └── Build chat interface
    └── Test and iterate

Phase 3: Auto-Tagging
    └── Integrate LLM suggestions into bot flow
    └── Build tag vocabulary management

Phase 4: Frontend (separate planning)
    └── TBD based on dedicated discussion
```

---

## Open Questions

1. **Embedding model choice**: Local vs API? Quality vs cost vs privacy tradeoffs.
2. **Vector store**: Simple (ChromaDB) vs performant (Qdrant) vs minimal (JSON+numpy)?
3. **RAG LLM**: Claude API vs local models vs hybrid?
4. **Auto-tagging trigger**: On every archive, or batch process existing?
5. **Frontend architecture**: To be discussed separately.

---

## Technical Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-12-23 | No folders/collections | Tags are more flexible for RAG retrieval |
| 2024-12-23 | Defer media archival | Multi-device constraint; text is primary value |
| 2024-12-23 | Defer scheduled exports | Premature until RAG usage patterns emerge |

---

## References

- Current implementation: `tools/` directory
- Post schema: `schemas/post.schema.json`
- Data indexes: `data/index.json`, `data/tags.json`
