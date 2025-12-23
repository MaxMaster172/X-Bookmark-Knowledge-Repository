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

### Phase 1: Embedding Infrastructure

**Goal:** Generate and store embeddings for all posts

#### 1.1 Set Up Python Environment
```
Create virtual environment
Install dependencies: sentence-transformers, chromadb, fastapi, uvicorn
Pin versions in requirements.txt
```

#### 1.2 Create Embedding Service Module
```python
# src/embeddings/service.py
- Load BGE model once at startup
- Function: generate_embedding(text) -> vector
- Function: generate_embedding_batch(texts) -> vectors
```

#### 1.3 Create Vector Store Module
```python
# src/embeddings/vector_store.py
- Initialize ChromaDB with persistent storage
- Function: add_post(id, text, metadata, embedding)
- Function: search(query_text, n_results) -> posts
- Function: delete_post(id)
- Function: get_stats() -> count, etc.
```

#### 1.4 Create Migration Script
```python
# scripts/migrate_embeddings.py
- Read all existing markdown posts
- Generate embeddings for each
- Store in ChromaDB
- Report progress and statistics
```

**Deliverable:** All existing posts have embeddings in ChromaDB

---

### Phase 2: Search API

**Goal:** Expose semantic search via HTTP endpoints

#### 2.1 Create FastAPI Application
```python
# src/api/main.py
- FastAPI app initialization
- CORS configuration for web frontend
- Health check endpoint
```

#### 2.2 Implement Search Endpoints
```python
# src/api/routes/search.py
GET /api/search?q={query}&limit={n}
  -> Returns ranked posts with similarity scores

GET /api/posts/{id}
  -> Returns full post content

GET /api/posts/{id}/similar
  -> Returns posts similar to given post
```

#### 2.3 Implement Stats/Browse Endpoints
```python
# src/api/routes/browse.py
GET /api/stats
  -> Total posts, tags distribution, etc.

GET /api/tags
  -> List all tags with counts

GET /api/posts?tag={tag}&author={author}
  -> Filtered post listing (hybrid with existing index.json)
```

**Deliverable:** Working API that can be tested via curl/Postman

---

### Phase 3: Bot Integration

**Goal:** Generate embeddings automatically when posts are archived

#### 3.1 Hook Into Post Save Flow
```python
# Modify existing bot post-save logic
After markdown file is written:
  1. Extract text content
  2. Generate embedding
  3. Add to ChromaDB
```

#### 3.2 Add Search Command to Bot
```python
# Bot command handler
/search {query}
  -> Call search API
  -> Format top 5 results for Telegram
  -> Include links to full posts
```

**Deliverable:** New posts automatically embedded; search available via Telegram

---

### Phase 4: Web Frontend

**Goal:** Browser-based UI for search and browsing

#### 4.1 Choose Frontend Approach
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

## File Structure (Proposed)

```
X-Bookmark-Knowledge-Repository/
├── data/
│   ├── posts/              # Markdown files (existing)
│   ├── index.json          # Post index (existing)
│   ├── tags.json           # Tag index (existing)
│   └── vectors/            # ChromaDB storage (new)
│       └── chroma.sqlite3
├── src/
│   ├── bot/                # Telegram bot (existing, to be modified)
│   ├── embeddings/         # New
│   │   ├── __init__.py
│   │   ├── service.py      # Embedding generation
│   │   └── vector_store.py # ChromaDB wrapper
│   ├── api/                # New
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI app
│   │   └── routes/
│   │       ├── search.py
│   │       └── browse.py
│   └── web/                # New (frontend)
│       ├── index.html
│       ├── search.html
│       ├── post.html
│       ├── static/
│       │   ├── style.css
│       │   └── app.js
│       └── templates/      # If using server-side rendering
├── scripts/
│   ├── migrate_embeddings.py
│   └── deploy.sh
├── requirements.txt
├── docs/
│   ├── ROADMAP.md
│   └── SEMANTIC_SEARCH_DESIGN.md  # This document
└── README.md
```

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
