# X-Bookmark Knowledge Repository - Roadmap & Planning

> Last updated: 2024-12-23 (revised with full feature roadmap)

## Current State (v1.5 - Semantic Search Complete)

### What's Built

**Core Archive System (v1.0)**
- **Telegram Bot**: Send X posts directly from mobile → bot archives with metadata
- **Twitter Fetcher**: Pulls full threads via free APIs (FxTwitter/VxTwitter)
- **File-based Archive**: Markdown files with YAML frontmatter, organized by date
- **Metadata System**: Tags, topics, notes, importance levels
- **Export Tools**: Multiple formats including LLM-optimized XML output

**Semantic Search (v1.5)** ✅ NEW
- **Embedding Service**: Local BGE model generates 384-dim vectors
- **Vector Store**: ChromaDB for persistent, searchable embeddings
- **Auto-embedding**: New posts get embeddings on save automatically
- **Semantic Search CLI**: `tools/search.py --semantic` for meaning-based search
- **Bot Search Upgrade**: `/search` command now uses semantic search by default

### Architecture
```
User → Telegram Bot → Twitter Fetcher → Markdown Files → Index JSON
              │                               │
              │                               ▼
              │                        Search/Export Tools
              │                               │
              ▼                               ▼
       Embedding Service ────────────► ChromaDB Vectors
              │
              ▼
       Semantic Search (CLI + Bot)
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

**Decision**:
- **Embedding model:** `BAAI/bge-small-en-v1.5` (local, free, 384 dimensions)
- **Vector store:** ChromaDB (embedded, simple, fits file-based philosophy)
- **Architecture:** Colocated with existing Hetzner VPS

See `docs/SEMANTIC_SEARCH_DESIGN.md` for full decision rationale.

---

### Priority 2: RAG Integration ✅ DECIDED

**Why**: The ultimate goal - chat with your bookmarks, generate insights, create content from your curated knowledge.

**Capabilities**:
- Ask questions, get answers citing your archived posts
- Generate content based on saved knowledge
- Surface forgotten insights when relevant
- Create thread drafts, summaries, and synthesized content

**Decision**:
- **LLM**: Claude API (high quality, streaming support, native tool use)
- **Approach**: Custom RAG pipeline (simple, tailored to our data structure)
- **Key features**: Source citations, streaming responses, context control, export synthesis

See Phase 6 in `docs/SEMANTIC_SEARCH_DESIGN.md` for full implementation details.

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

### Priority 4: Frontend / User Interface ✅ DECIDED

**Status**: Full tech stack and design direction decided.

**Decisions**:
- **Hosting**: Web app on existing Hetzner VPS alongside Telegram bot
- **Backend**: FastAPI serving API endpoints
- **Frontend**: React + Tailwind CSS + shadcn/ui
- **Build**: Vite for fast development
- **Auth**: Network-level security (VPN/tunnel); add token auth later if needed
- **Design**: Modern, polished "AI-forward" aesthetic; dark mode default; mobile-first

**Core Features**:
- Semantic search with X-like feed display
- RAG chat interface (the centerpiece)
- Post browsing and filtering
- Knowledge graph visualization
- Research sessions

See `docs/SEMANTIC_SEARCH_DESIGN.md` for full implementation details.

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
Phase 1: Embedding Infrastructure ✅ COMPLETE
    └── Set up Python environment with sentence-transformers, ChromaDB
    └── Create embedding service (BGE model wrapper)
    └── Create vector store (ChromaDB wrapper)
    └── Build migration script for existing posts

Phase 2: Bot Integration ✅ COMPLETE
    └── Hook embedding generation into save_archived_post()
    └── Upgrade /search command to semantic search

Phase 3: Consolidate Search Tools ✅ COMPLETE
    └── Add --semantic flag to tools/search.py
    └── Remove duplicate files

Phase 4: Search API 🔜 NEXT
    └── Create FastAPI application
    └── Implement search, posts, stats endpoints
    └── Test with curl/Postman

Phase 5: Web Frontend (Search & Browse)
    └── Set up React + Tailwind + shadcn/ui + Vite
    └── Build search UI with X-like feed
    └── Build post detail and browse pages

Phase 6: RAG Chat Interface (THE CORE FEATURE)
    └── Build RAG pipeline with Claude API
    └── Create streaming chat UI
    └── Add source citations, context control, export

Phase 7: Deployment & Integration
    └── Set up systemd services on VPS
    └── Configure Nginx reverse proxy
    └── Set up network-level security

Phase 8: Advanced Features
    └── Knowledge graph visualization
    └── Resurface/rediscovery feature
    └── Related posts sidebar
    └── Research sessions

Phase 9: Draft Workspace (LOW PRIORITY)
    └── Writing tool with inline RAG suggestions
    └── Nice-to-have after everything else works

Phase 10: Polish & Iteration
    └── Performance optimization
    └── UX refinements
    └── Future possibilities (browser extension, etc.)
```

---

## Open Questions

1. ~~**Embedding model choice**: Local vs API?~~ → **Decided:** Local `bge-small-en-v1.5`
2. ~~**Vector store**: Simple vs performant vs minimal?~~ → **Decided:** ChromaDB
3. ~~**RAG LLM**: Claude API vs local models vs hybrid?~~ → **Decided:** Claude API
4. ~~**Frontend architecture**: To be discussed separately.~~ → **Decided:** React + Tailwind + shadcn/ui
5. ~~**Authentication**: Public or private?~~ → **Decided:** Network-level (VPN/tunnel)
6. **Auto-tagging trigger**: On every archive, or batch process existing? (deferred to later)
7. **Domain name**: Subdomain of existing domain or new one?
8. **Backup strategy**: How to backup ChromaDB alongside markdown files?

---

## Technical Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-12-23 | No folders/collections | Tags are more flexible for RAG retrieval |
| 2024-12-23 | Defer media archival | Multi-device constraint; text is primary value |
| 2024-12-23 | Defer scheduled exports | Premature until RAG usage patterns emerge |
| 2024-12-23 | Local embeddings (bge-small-en-v1.5) | Free, private, high quality, sufficient for personal scale |
| 2024-12-23 | ChromaDB for vector storage | Simple, embedded, fits file-based philosophy |
| 2024-12-23 | Web app for multi-device access | Browser = universal access; simpler than per-device solutions |
| 2024-12-23 | Colocate on existing Hetzner VPS | Already hosting bot; sufficient resources; $0 additional cost |
| 2024-12-23 | React + Tailwind + shadcn/ui | Modern, flexible, large ecosystem, Claude-friendly |
| 2024-12-23 | Network-level auth | Private use only; simple; add token auth later if needed |
| 2024-12-23 | Claude API for RAG | High quality, streaming support, native tool use |
| 2024-12-23 | Custom RAG pipeline | Simple, tailored to our data, no heavy dependencies |

---

## References

- Current implementation: `tools/` directory
- Embedding service: `src/embeddings/`
- Design document: `docs/SEMANTIC_SEARCH_DESIGN.md`
- Post schema: `schemas/post.schema.json`
- Data indexes: `data/index.json`, `data/tags.json`
- Vector store: `data/vectors/`
