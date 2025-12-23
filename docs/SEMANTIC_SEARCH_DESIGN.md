# Semantic Search Design & Implementation Plan

> Last updated: 2024-12-23

## Overview

This document captures the design decisions and implementation plan for adding semantic search capabilities to the X-Bookmark Knowledge Repository. It traces our evaluation process from initial options through to final architecture decisions.

---

## Part 1: Decision Journey

### Starting Point

From `ROADMAP.md`, we had identified semantic search as Priority 1 with these open questions:
- Embedding model choice: Local vs API?
- Vector store: ChromaDB vs Qdrant vs JSON+numpy?
- How to handle multi-device access (iPhone, MacBook, Windows Desktop)?

### Constraint Discovery

**Critical constraint identified:** User works across multiple devices including iPhone, which cannot run Python ML stack.

This constraint shaped all subsequent decisions.

---

## Part 2: Options Evaluated

### Embedding Approach Options

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Local sentence-transformers** | Free, private, offline, high quality | Requires Python ML stack | **SELECTED** |
| OpenAI Embeddings API | High quality, simple | Ongoing cost, data leaves machine | Rejected |
| Ollama embeddings | Free, private | Extra daemon dependency, no real benefit at our scale | Rejected |

**Selected model:** `BAAI/bge-small-en-v1.5`
- 384 dimensions (compact vectors)
- Top-tier retrieval quality for its size
- ~130MB model file
- Fast inference on CPU

### Vector Store Options

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **ChromaDB** | Embedded, simple API, persists to disk | Less performant than Qdrant | **SELECTED** |
| Qdrant | High performance | Overkill for personal archive scale | Rejected |
| JSON + numpy | Minimal dependencies | Would rebuild what ChromaDB already does | Rejected |

**Rationale:** ChromaDB fits the file-based philosophy - it's just another local file alongside our markdown and JSON indexes. Handles thousands of posts trivially.

---

## Part 3: Multi-Device Architecture Evolution

### Initial Approaches Considered

We evaluated 5 different architecture patterns for multi-device access:

#### Option 1: Telegram Bot as Search Interface
```
Server (Bot + Search) ←── Telegram ←── All Devices
```
- Extend existing bot with `/search` commands
- Simple but limited UX on mobile

#### Option 2: Git-Synced with Local Regeneration
```
Git Repo (markdown only) → Each desktop regenerates vectors locally
```
- iPhone excluded from direct search
- Must rebuild vectors after each pull

#### Option 3: Vectors in Git
```
Git Repo (markdown + vectors.json) → Any machine loads and searches
```
- Instant search after git pull
- ~1.5KB per post, grows with archive
- Still excludes iPhone

#### Option 4: Cloud Vector Store (Pinecone/Weaviate)
```
Cloud DB ←── All devices query via API
```
- True multi-device including iPhone
- Monthly cost, data in cloud

#### Option 5: Self-Hosted API
```
VPS (API + DB) ←── All devices via HTTPS
```
- Full control, works everywhere
- Requires hosting

### The Clarifying Question

**"What if we build a web app frontend?"**

This reframed the problem entirely:
- A web app is just a URL
- Any device with a browser can access it
- No per-device setup or syncing needed
- Multi-device "solved" by the nature of the web

### Key Discovery: Existing Infrastructure

**The Telegram bot already runs on a Hetzner VPS.**

This eliminated hosting as a new concern - we can colocate the web app with the existing bot.

---

## Part 4: Final Architecture Decision

### Selected Approach: Colocated Web App on Existing VPS

```
┌────────────────────── Hetzner VPS ──────────────────────┐
│                                                          │
│   ┌──────────────┐    ┌──────────────┐                  │
│   │ Telegram Bot │    │   Web App    │                  │
│   │  (existing)  │    │  (FastAPI)   │                  │
│   └──────┬───────┘    └──────┬───────┘                  │
│          │                   │                          │
│          ▼                   ▼                          │
│   ┌─────────────────────────────────────────────────┐   │
│   │              Shared Data Layer                   │   │
│   │  /posts/*.md    ChromaDB (vectors)   index.json │   │
│   └─────────────────────────────────────────────────┘   │
│                                                          │
│   ┌─────────────────────────────────────────────────┐   │
│   │         Embedding Service (BGE model)            │   │
│   │         Generates vectors on post save           │   │
│   └─────────────────────────────────────────────────┘   │
│                                                          │
│   Nginx ─── reverse proxy to bot + web app              │
│                                                          │
└──────────────────────────────────────────────────────────┘
            │                           │
    Telegram API              https://bookmarks.domain.com
            │                           │
     Archive posts               Search & browse
     (any device)                 (any device)
```

### Why This Works

| Concern | How It's Addressed |
|---------|-------------------|
| Multi-device access | Web app = just a URL, works on any browser |
| iPhone support | Safari works fine |
| Hosting cost | $0 additional - uses existing VPS |
| Privacy | Everything stays on your server |
| Embedding cost | $0 - local model |
| Complexity | Single server, shared data layer |

### Resource Analysis

Confirmed the existing VPS can handle the load:

| Component | RAM Usage | CPU | Notes |
|-----------|-----------|-----|-------|
| Telegram bot | ~50-100 MB | Idle | Already running |
| Web app (FastAPI) | ~100-200 MB | Idle | Spikes on requests |
| Embedding model | ~300-500 MB | Spike on embed | 1-3 sec per post |
| ChromaDB | ~50-100 MB | Light | In-process |
| **Total** | **~500 MB - 1 GB** | **Mostly idle** | Works on 2GB VPS |

---

## Part 5: Technical Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Embedding model | `BAAI/bge-small-en-v1.5` | Best quality/size ratio, 384 dims |
| Vector store | ChromaDB | Simple, embedded, fits file-based philosophy |
| Hosting | Existing Hetzner VPS | Already available, sufficient resources |
| API framework | FastAPI | Async, fast, good Python ecosystem fit |
| Multi-device strategy | Web app | Universal browser access |
| Model loading | Keep loaded in memory | Instant embeddings, RAM available |

---

## Part 6: Implementation Plan

> **REVISED 2024-12-23**: Updated after reviewing existing codebase structure.

### Lessons Learned from Existing Code

After examining the existing `tools/` directory:

| Existing Code | What It Does | Impact on Plan |
|---------------|--------------|----------------|
| `tools/search.py` | Full keyword search CLI | Enhance with semantic search, don't create separate tool |
| `tools/telegram_bot.py` | Complete archive bot with `/search` | Hook embedding into `save_archived_post()` |
| `tools/utils.py` | Shared utilities, `parse_post_file()` | Reuse instead of creating duplicate parser |

### Key Changes from Original Plan

1. **Phase reordering**: Bot integration moves to Phase 2 (new posts need embeddings immediately)
2. **Consolidate search**: Add semantic mode to existing `tools/search.py`
3. **Remove duplicates**: Delete `src/posts/parser.py`, use `tools/utils.py`
4. **Integration point**: `save_archived_post()` at `tools/telegram_bot.py:429`

---

### Phase 1: Embedding Infrastructure ✅ COMPLETE

**Goal:** Generate and store embeddings for all posts

#### 1.1 Set Up Python Environment ✅
```
Created virtual environment
Installed: sentence-transformers, chromadb, fastapi, uvicorn
See requirements.txt
```

#### 1.2 Create Embedding Service Module ✅
```python
# src/embeddings/service.py
- Singleton pattern for model loading
- generate(text) -> vector
- generate_batch(texts) -> vectors
- generate_for_query(query) -> vector (with BGE prefix)
```

#### 1.3 Create Vector Store Module ✅
```python
# src/embeddings/vector_store.py
- ChromaDB wrapper with persistent storage
- add_post(), search(), get_similar(), delete_post()
- Metadata flattening for ChromaDB compatibility
```

#### 1.4 Create Migration Script ✅
```python
# scripts/migrate_embeddings.py
- Reads from archive/posts/ (correct path)
- Raw YAML parsing (avoids frontmatter library conflict)
- Successfully processed 4 existing posts
```

**Status:** Complete. Vector store at `data/vectors/` with 4 embedded posts.

---

### Phase 2: Bot Integration (MOVED UP - was Phase 3)

**Goal:** Generate embeddings automatically when posts are archived

**Why this is now Phase 2:** Without this, new posts won't be searchable. This is critical for ongoing use.

#### 2.1 Hook Into Post Save Flow
```python
# Modify tools/telegram_bot.py save_archived_post() function
# Add after line 540 (after git_sync):

from src.embeddings.vector_store import get_vector_store
from src.embeddings.service import get_embedding_service

# Generate and store embedding
try:
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()

    # Create embedding text (content + metadata)
    embed_text = f"{content}\n\nAuthor: @{thread.author_handle}"
    if data.get("tags"):
        embed_text += f"\nTags: {', '.join(data['tags'])}"
    if data.get("topics"):
        embed_text += f"\nTopics: {', '.join(data['topics'])}"

    embedding = embedding_service.generate(embed_text)
    vector_store.add_post(
        post_id=post_id,
        content=content,
        metadata={...},
        embedding=embedding
    )
except Exception as e:
    logger.warning(f"Failed to generate embedding: {e}")
    # Non-blocking - post is still saved
```

#### 2.2 Upgrade Bot /search Command
```python
# Modify tools/telegram_bot.py search() function
# Add semantic search option:

/search query        -> semantic search (default)
/search -k query     -> keyword search (legacy)
```

**Deliverable:** New posts automatically embedded; semantic search via Telegram

---

### Phase 3: Consolidate Search Tools (MOVED UP - was part of Phase 2)

**Goal:** Single unified search CLI with both keyword and semantic modes

#### 3.1 Enhance Existing tools/search.py
```python
# Add to tools/search.py:
# New subcommand: semantic

search_parser.add_argument(
    "--semantic", "-s",
    action="store_true",
    help="Use semantic (meaning-based) search"
)

# When --semantic flag is used:
from src.embeddings.vector_store import get_vector_store
vector_store = get_vector_store()
results = vector_store.search(query, n_results=limit)
```

#### 3.2 Remove Duplicate Files
```
DELETE: scripts/search.py (our separate semantic search CLI)
DELETE: src/posts/parser.py (use tools/utils.py instead)
DELETE: src/posts/__init__.py
```

#### 3.3 Update Migration Script
```python
# Update scripts/migrate_embeddings.py to use tools/utils.py
from tools.utils import parse_post_file, ARCHIVE_DIR, BASE_DIR
```

**Deliverable:** Single `tools/search.py` with both modes

---

### Phase 4: Search API

**Goal:** Expose semantic search via HTTP endpoints for web frontend

#### 4.1 Create FastAPI Application
```python
# src/api/main.py
- FastAPI app initialization
- CORS configuration for web frontend
- Health check endpoint
```

#### 4.2 Implement Search Endpoints
```python
# src/api/routes/search.py
GET /api/search?q={query}&limit={n}&mode={semantic|keyword}
  -> Returns ranked posts with similarity scores

GET /api/posts/{id}
  -> Returns full post content

GET /api/posts/{id}/similar
  -> Returns posts similar to given post
```

#### 4.3 Implement Stats/Browse Endpoints
```python
# src/api/routes/browse.py
GET /api/stats
  -> Total posts, tags distribution, etc.

GET /api/tags
  -> List all tags with counts

GET /api/posts?tag={tag}&author={author}
  -> Filtered post listing (uses existing index.json)
```

**Deliverable:** Working API that can be tested via curl/Postman

---

### Phase 5: Web Frontend

**Goal:** Browser-based UI for search and browsing

#### 5.1 Choose Frontend Approach
Options (to be decided):
- **Minimal:** Plain HTML + vanilla JS (simplest)
- **Light framework:** Alpine.js or htmx (progressive enhancement)
- **Full SPA:** React/Vue (most interactive, more complexity)

Recommendation: Start with **htmx + minimal CSS** for simplicity, upgrade later if needed.

#### 4.2 Core Pages
```
/ (home)
  - Search bar (prominent)
  - Recent posts
  - Quick stats

/search?q={query}
  - Search results with snippets
  - Similarity scores
  - Filter by tag/author

/post/{id}
  - Full post content
  - Metadata (tags, author, date)
  - "Similar posts" section

/browse
  - All posts, paginated
  - Filter controls
  - Sort options
```

#### 4.3 Static Assets & Styling
```
Minimal CSS framework (e.g., Pico CSS, Simple.css)
Mobile-responsive (iPhone is primary mobile use case)
Dark mode support (optional but nice)
```

**Deliverable:** Functional web interface accessible from any device

---

### Phase 5: Deployment & Integration

**Goal:** Everything running on Hetzner VPS

#### 5.1 Server Setup
```bash
# On VPS
Set up systemd service for FastAPI app
Configure Nginx reverse proxy:
  - /api/* -> FastAPI (port 8000)
  - /* -> Static frontend files
  - Existing bot routes unchanged
SSL via Let's Encrypt (certbot)
```

#### 5.2 Process Management
```bash
# Supervisor or systemd units
- telegram-bot.service (existing)
- bookmark-api.service (new)
Both auto-restart on failure
```

#### 5.3 Deployment Workflow
```
Local development
  -> Push to GitHub
  -> SSH to VPS, git pull
  -> Restart services

(Or set up GitHub Actions for auto-deploy later)
```

**Deliverable:** Production system running on VPS, accessible via domain

---

### Phase 6: Polish & Iteration

**Goal:** Refine based on actual usage

#### 6.1 Search Quality Tuning
- Adjust similarity thresholds
- Test with real queries
- Consider hybrid search (semantic + keyword)

#### 6.2 Performance Optimization
- Add response caching if needed
- Lazy-load embedding model if RAM tight
- Index optimization

#### 6.3 UX Improvements
- Keyboard shortcuts
- Search history
- Bookmarklet for quick saving (alternative to Telegram)

---

## File Structure (Revised)

```
X-Bookmark-Knowledge-Repository/
├── archive/
│   └── posts/              # Markdown files organized by YYYY/MM/
│       └── 2025/12/*.md
├── data/
│   ├── index.json          # Post index (existing)
│   ├── tags.json           # Tag index (existing)
│   └── vectors/            # ChromaDB storage (new)
│       └── chroma.sqlite3
├── tools/                  # EXISTING - enhance, don't duplicate
│   ├── telegram_bot.py     # Modify: add embedding on save
│   ├── twitter_fetcher.py  # Existing - no changes
│   ├── search.py           # Modify: add --semantic flag
│   ├── export.py           # Existing - no changes
│   ├── add_post.py         # Existing - no changes
│   └── utils.py            # Existing - reuse parse_post_file()
├── src/
│   ├── embeddings/         # NEW - core embedding logic
│   │   ├── __init__.py
│   │   ├── service.py      # BGE model wrapper
│   │   └── vector_store.py # ChromaDB wrapper
│   └── api/                # NEW - FastAPI for web frontend
│       ├── __init__.py
│       ├── main.py
│       └── routes/
│           ├── search.py
│           └── browse.py
├── web/                    # NEW - frontend (Phase 5)
│   ├── index.html
│   ├── search.html
│   └── static/
│       ├── style.css
│       └── app.js
├── scripts/
│   └── migrate_embeddings.py  # Bulk embedding tool
├── schemas/
│   └── post.schema.json    # Existing
├── docs/
│   ├── ROADMAP.md
│   └── SEMANTIC_SEARCH_DESIGN.md
├── requirements.txt
└── README.md
```

**Key principle:** Integrate with existing `tools/` structure rather than creating parallel systems.

---

## Dependencies (requirements.txt)

```
# Embeddings
sentence-transformers>=2.2.0
chromadb>=0.4.0

# API
fastapi>=0.100.0
uvicorn>=0.23.0
python-multipart>=0.0.6

# Existing (likely already present)
python-telegram-bot>=20.0
pyyaml>=6.0
```

---

## Open Items for Future Discussion

1. **Frontend framework choice** - Start simple (htmx) or go SPA (React)?
2. **Domain name** - Use subdomain of existing domain or new one?
3. **Authentication** - Is the web app public or should it require login?
4. **Backup strategy** - How to backup ChromaDB alongside markdown files?

---

## References

- [sentence-transformers documentation](https://www.sbert.net/)
- [BGE embedding models](https://huggingface.co/BAAI/bge-small-en-v1.5)
- [ChromaDB documentation](https://docs.trychroma.com/)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
