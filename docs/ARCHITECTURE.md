# X-Bookmark Knowledge Repository: Architecture Revision & Implementation Plan

> Created: 2024-12-24
> Status: **APPROVED**

This document supersedes `SEMANTIC_SEARCH_DESIGN.md` for architectural decisions. It captures the transition from a self-hosted file-based system to a modern cloud-native stack.

---

## Part A: Master Architecture Overview

### Executive Summary

The project is transitioning from a **self-hosted, file-based architecture** to a **modern cloud-native stack** leveraging Supabase, Next.js, and Vercel. This shift addresses key limitations in the original design while enabling more sophisticated features like relational queries for research sessions and knowledge graphs.

---

### Architecture Comparison

#### BEFORE: Self-Hosted File-Based System

```
┌────────────────────── Hetzner VPS ──────────────────────┐
│                                                          │
│   Telegram Bot    FastAPI       React (Vite)            │
│        │             │               │                  │
│        ▼             ▼               ▼                  │
│   ┌─────────────────────────────────────────────────┐   │
│   │  Markdown Files   ChromaDB   JSON Indexes       │   │
│   │  (posts/*.md)     (vectors)  (index.json)       │   │
│   └─────────────────────────────────────────────────┘   │
│                                                          │
│   Nginx reverse proxy + Let's Encrypt SSL               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Characteristics:**
- Everything on one server
- Multiple data stores to sync (Markdown + JSON + ChromaDB)
- Manual deployment (SSH → git pull → build → restart)
- Custom FastAPI layer required for all endpoints
- Git-versioned posts (markdown files)

---

#### AFTER: Cloud-Native Distributed System

```
┌─────────────────── Vercel ───────────────────┐
│                   Next.js                    │
│                                              │
│   Frontend (React)    API Routes (Claude)   │
│         │                    │               │
└─────────┼────────────────────┼───────────────┘
          │                    │
          │                    ▼
          │             ┌──────────────┐
          │             │  Claude API  │
          │             └──────────────┘
          ▼
┌───────────────────────────────────────────┐
│                 Supabase                  │
│                                           │
│   PostgreSQL    pgvector    Realtime     │
│   (posts)       (embeddings) (chat)      │
│                                           │
└─────────────────────┬─────────────────────┘
                      │
                      │ writes
                      │
┌─────────────────────┴─────────────────────┐
│              Hetzner VPS                  │
│                                           │
│            Telegram Bot                   │
│         (archive interface)               │
│                                           │
└───────────────────────────────────────────┘
```

**Characteristics:**
- Specialized services for each concern
- Unified data layer (Supabase PostgreSQL + pgvector)
- Automatic deployment (git push)
- Auto-generated CRUD API + Next.js API routes for Claude
- VPS only runs the Telegram bot

---

### Technology Stack Changelog

| Layer | OLD | NEW | Rationale |
|-------|-----|-----|-----------|
| **Frontend Framework** | React + Vite + React Router | Next.js | Built-in API routes solve Claude API key placement; file-based routing |
| **Backend/API** | FastAPI (to be built) | Supabase auto-API + Next.js API routes | No need to build CRUD endpoints; Claude calls live in `/api/chat` |
| **Database** | Markdown files + JSON indexes | Supabase PostgreSQL | Relational queries for sessions, knowledge graph; unified data model |
| **Vector Store** | ChromaDB (local SQLite) | pgvector (PostgreSQL extension) | Unified with main database; same query language |
| **Deployment Platform** | Hetzner VPS + Nginx | Vercel (frontend) + Supabase (data) + VPS (bot) | Git-push deploys; global CDN; automatic SSL |
| **SSL/HTTPS** | Let's Encrypt / Certbot | Automatic (Vercel) | Zero configuration |
| **Preview Environments** | None | Automatic per branch (Vercel) | Test features before merging |

---

### What Stays the Same

| Component | Status |
|-----------|--------|
| **Telegram Bot** | Stays on Hetzner VPS, updates to write to Supabase |
| **Tailwind CSS** | Still used for styling |
| **shadcn/ui** | Still used for components |
| **Claude API** | Still used for RAG (called from Next.js API routes) |
| **BGE Embeddings** | Still used, stored in pgvector instead of ChromaDB |
| **Core UX Vision** | Search, browse, RAG chat - unchanged |

---

### Data Model Changes

| Data Type | OLD Storage | NEW Storage |
|-----------|-------------|-------------|
| Posts | `archive/posts/*.md` (YAML frontmatter) | `posts` table in PostgreSQL |
| Post indexes | `data/index.json`, `data/tags.json` | SQL queries (no separate index) |
| Embeddings | `data/vectors/` (ChromaDB) | `embedding` column (pgvector) |
| Media metadata | `media:` array in markdown | `post_media` table |
| Research sessions | `data/sessions/*.json` (planned) | `sessions` + `session_posts` tables |
| Chat history | Not specified | JSONB in `sessions` table |

---

### New Capabilities Enabled

1. **Image Content Extraction**: Claude Vision extracts semantic descriptions from images at archive time
2. **Relational Queries**: SQL JOINs for knowledge graph, research sessions
3. **Realtime Subscriptions**: Supabase Realtime for streaming chat responses
4. **Global CDN**: Frontend served from 100+ edge locations
5. **Preview Deployments**: Every branch gets a unique URL for testing

---

### Trade-offs Accepted

| Trade-off | Mitigation |
|-----------|------------|
| **Loss of git-versioned posts** | Posts are write-once (archived tweets); Supabase has point-in-time recovery |
| **Split architecture (3 services)** | Each service is specialized and reliable; well-documented integration patterns |
| **External dependencies** | Both Supabase and Vercel are open-source and self-hostable if needed |
| **Potential costs at scale** | Free tiers are generous; personal use stays well within limits |

---

### Cost Summary

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| **Vercel** | Hobby (Free) | $0 |
| **Supabase** | Free | $0 |
| **Hetzner VPS** | Existing | ~$5-10 |
| **Claude API** | Pay-as-you-go | ~$5-20 (usage dependent) |
| **Image Extraction** | Claude Vision | ~$0.50-1 |

**Total:** ~$10-30/month (mostly Claude API for RAG)

---

## Part B: Detailed Implementation Plan

### Phase Overview

```
Phase 1: Supabase Setup & Data Migration
    └── Create project, schema, migrate data

Phase 2: Telegram Bot Update
    └── Write to Supabase instead of files

Phase 3: Image Content Extraction
    └── Claude Vision integration

Phase 4: Next.js Application
    └── Core pages + Supabase client

Phase 5: RAG Chat Interface
    └── Claude API routes + streaming UI

Phase 6: Vercel Deployment
    └── Connect repo, configure, go live

Phase 7: Advanced Features
    └── Knowledge graph, research sessions

Phase 8: Cleanup & Documentation
    └── Remove old code, update docs
```

---

### Phase 1: Supabase Setup & Data Migration

**Goal:** Set up Supabase project and migrate existing data from files to PostgreSQL

#### 1.1 Create Supabase Project
- Sign up at supabase.com
- Create new project (free tier)
- Note project URL and anon key

#### 1.2 Enable pgvector Extension
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 1.3 Create Database Schema

```sql
-- Core posts table
CREATE TABLE posts (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    author_handle TEXT,
    author_name TEXT,
    content TEXT,
    posted_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archived_via TEXT DEFAULT 'telegram',
    tags TEXT[],
    topics TEXT[],
    notes TEXT,
    importance TEXT,
    thread_position INTEGER,
    is_thread BOOLEAN DEFAULT FALSE,

    -- Quoted post (embedded)
    quoted_post_id TEXT,
    quoted_text TEXT,
    quoted_author TEXT,
    quoted_url TEXT,

    -- Embedding vector (384 dimensions for BGE)
    embedding VECTOR(384)
);

-- Media items (one-to-many)
CREATE TABLE post_media (
    id SERIAL PRIMARY KEY,
    post_id TEXT REFERENCES posts(id) ON DELETE CASCADE,
    type TEXT,
    url TEXT,
    category TEXT,  -- 'text_heavy', 'chart', 'general'
    description TEXT,
    extracted_at TIMESTAMPTZ,
    extraction_model TEXT
);

-- Research sessions (Phase 7)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    conversation JSONB
);

CREATE TABLE session_posts (
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    post_id TEXT REFERENCES posts(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (session_id, post_id)
);

-- Indexes
CREATE INDEX posts_author_idx ON posts(author_handle);
CREATE INDEX posts_archived_at_idx ON posts(archived_at DESC);
CREATE INDEX posts_tags_idx ON posts USING GIN(tags);
CREATE INDEX posts_embedding_idx ON posts USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX post_media_post_id_idx ON post_media(post_id);
```

#### 1.4 Create Migration Script

**File:** `scripts/migrate_to_supabase.py`

```
- Read all posts from archive/posts/**/*.md
- Parse YAML frontmatter + content
- For each post:
  - Insert into posts table
  - Insert media items into post_media table
  - Copy embedding from ChromaDB to pgvector
- Verify counts match
```

#### 1.5 Run Migration
```bash
python scripts/migrate_to_supabase.py --dry-run  # Verify first
python scripts/migrate_to_supabase.py            # Execute
```

**Deliverable:** All existing posts and embeddings in Supabase

---

### Phase 2: Telegram Bot Update

**Goal:** Update bot to write to Supabase instead of local files

#### 2.1 Install Supabase Python Client
```
pip install supabase
```

#### 2.2 Create Supabase Service Module

**File:** `src/supabase/client.py`
- Initialize Supabase client with env vars
- Helper functions: `insert_post()`, `insert_media()`, `update_embedding()`

#### 2.3 Update telegram_bot.py

**Modify:** `save_archived_post()` function (~line 429)
- Replace file write with Supabase insert
- Keep BGE embedding generation on VPS (already working)
- Store embedding in pgvector instead of ChromaDB
- Remove git sync (no more markdown files)

#### 2.4 Update Search Function

**Modify:** Bot `/search` command
- Replace ChromaDB query with Supabase vector search:
```sql
SELECT *, embedding <=> $query_embedding AS distance
FROM posts
ORDER BY distance
LIMIT 10;
```

#### 2.5 Fix Telegram Markdown Bug

**Modify:** All dynamic message handlers
- Switch from `parse_mode="Markdown"` to `parse_mode="HTML"`
- Escape `<`, `>`, `&` in dynamic content

**Deliverable:** Bot archives directly to Supabase

---

### Phase 3: Image Content Extraction

**Goal:** Extract semantic descriptions from images using Claude Vision

#### 3.1 Create Vision Module

**Files:**
- `src/vision/__init__.py`
- `src/vision/extractor.py` - Claude Vision API wrapper
- `src/vision/prompts.py` - Category-specific extraction prompts

#### 3.2 Implement ImageContentExtractor

```python
class ImageContentExtractor:
    - detect_category(image_data) -> "text_heavy" | "chart" | "general"
    - describe_image(url, context, category) -> description
    - _fetch_image(url) -> base64 data
```

#### 3.3 Integrate into Archive Flow

**Modify:** `save_archived_post()` in telegram_bot.py
- For each image in media:
  1. Call extractor.describe_image()
  2. Store description + category in post_media table
  3. Include descriptions in embedding text

#### 3.4 Create Backfill Script

**File:** `scripts/backfill_image_descriptions.py`
- Find posts with images but no descriptions
- Process with rate limiting (1 post/sec)
- Re-generate embeddings after backfill

**Deliverable:** Images are semantically searchable

---

### Phase 4: Next.js Application

**Goal:** Build the web frontend with Supabase integration

#### 4.1 Initialize Next.js Project

```bash
npx create-next-app@latest web --typescript --tailwind --eslint --app
cd web
npx shadcn@latest init
```

#### 4.2 Install Dependencies

```bash
npm install @supabase/supabase-js
npx shadcn@latest add button card input dialog
```

#### 4.3 Create App Structure

```
web/
├── app/
│   ├── layout.tsx          # Root layout with providers
│   ├── page.tsx            # Home: search bar + recent posts
│   ├── search/
│   │   └── page.tsx        # Search results (X-like feed)
│   ├── post/
│   │   └── [id]/
│   │       └── page.tsx    # Post detail + similar posts
│   ├── chat/
│   │   └── page.tsx        # RAG chat interface
│   └── api/
│       └── chat/
│           └── route.ts    # Claude API endpoint
├── components/
│   ├── PostCard.tsx        # Post preview card
│   ├── SearchBar.tsx       # Search input
│   ├── ChatMessage.tsx     # Chat message bubble
│   └── ...
├── lib/
│   ├── supabase.ts         # Supabase client
│   └── utils.ts            # Utilities
└── ...
```

#### 4.4 Implement Core Pages

**Home (`/`):**
- Prominent search bar (centered)
- Recent posts feed (last 10)
- Quick stats (total posts, top tags)

**Search (`/search?q=...`):**
- X-like feed of results
- Similarity scores (subtle color gradient)
- Filter sidebar (tags, authors, date range)
- "Add to chat context" action

**Post Detail (`/post/[id]`):**
- Full post content with media
- Metadata (tags, author, date, original URL)
- Similar posts sidebar
- "Chat about this" button

#### 4.5 Implement Supabase Queries

```typescript
// lib/supabase.ts
export async function searchPosts(query: string, limit = 10) {
  // Generate embedding for query (call API route)
  // Vector search with pgvector
}

export async function getPost(id: string) { ... }
export async function getRecentPosts(limit = 10) { ... }
export async function getSimilarPosts(id: string, limit = 5) { ... }
```

**Deliverable:** Working web UI for search and browsing

---

### Phase 5: RAG Chat Interface

**Goal:** Implement Claude-powered chat with source citations

#### 5.1 Create Chat API Route

**File:** `web/app/api/chat/route.ts`

```typescript
export async function POST(request: Request) {
  const { message, history, contextPostIds } = await request.json();

  // 1. Retrieve relevant posts via vector search
  // 2. Build context with retrieved posts
  // 3. Call Claude API with streaming
  // 4. Return streaming response with source citations
}
```

#### 5.2 Implement RAG Pipeline

**File:** `web/lib/rag.ts`

```typescript
export async function generateRAGResponse(
  query: string,
  history: Message[],
  contextPosts: Post[]
) {
  // Build system prompt with post context
  // Call Claude with streaming
  // Parse response for source citations
}
```

#### 5.3 Build Chat UI

**Page:** `web/app/chat/page.tsx`

Features:
- Full-screen chat interface
- Streaming responses (token-by-token)
- Source citations inline (clickable links)
- Context sidebar (add/remove posts)
- Conversation history
- Prompt templates ("Synthesize into thread", "Find contrarian takes")

#### 5.4 Add Export Functionality

- Export chat as markdown
- Generate thread drafts
- Create summaries

**Deliverable:** Working RAG chat with source citations

---

### Phase 6: Vercel Deployment

**Goal:** Deploy Next.js app to Vercel with automatic deploys

#### 6.1 Connect Repository

1. Push code to GitHub
2. Import project in Vercel dashboard
3. Configure:
   - Framework: Next.js
   - Root directory: `web/`

#### 6.2 Configure Environment Variables

```
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx  # For server-side operations
ANTHROPIC_API_KEY=xxx
```

#### 6.3 Set Up Custom Domain

1. Add domain in Vercel dashboard
2. Configure DNS (CNAME or A record)
3. SSL automatically provisioned

#### 6.4 Configure CORS in Supabase

- Add Vercel domain to allowed origins
- Add preview deployment pattern: `*.vercel.app`

#### 6.5 Verify Deployment

- Test search functionality
- Test chat API route
- Test preview deployment on feature branch

**Deliverable:** Live production deployment with CI/CD

---

### Phase 7: Advanced Features

**Goal:** Build knowledge graph, research sessions, and discovery features

#### 7.1 Knowledge Graph Visualization

- Use D3.js or react-force-graph
- Nodes: posts (sized by importance)
- Edges: similarity (from vector distances)
- Interactive: click to explore

#### 7.2 Research Sessions

- Save chat + source posts as named project
- Resume sessions later
- Export entire session as document

#### 7.3 Resurface / Rediscovery

- "Random gem" feature
- Surface posts not viewed recently
- Optional weekly digest

#### 7.4 Related Posts Sidebar

- Show 3-5 similar posts on every post view
- Already have vector similarity - just UI

**Deliverable:** Feature-complete knowledge assistant

---

### Phase 8: Cleanup & Documentation

**Goal:** Remove old code, update documentation

#### 8.1 Remove Deprecated Code

- `src/embeddings/` (ChromaDB wrapper) - replaced by pgvector
- `src/api/` (FastAPI) - never built, replaced by Next.js API routes
- `scripts/migrate_embeddings.py` - one-time migration done
- Local vector store files (`data/vectors/`)

#### 8.2 Remove Markdown Files

- Delete `archive/posts/` directory (data now lives in Supabase)
- Delete `data/index.json`, `data/tags.json` (replaced by SQL queries)
- Delete `data/vectors/` (replaced by pgvector)

#### 8.3 Update Documentation

- Update `ROADMAP.md` with new architecture
- Deprecate `SEMANTIC_SEARCH_DESIGN.md` (superseded by this document)
- Update `README.md` with new setup instructions

#### 8.4 Update VPS Configuration

- Remove FastAPI systemd service (never created)
- Keep telegram-bot.service (updated for Supabase)
- Remove Nginx frontend config (Vercel handles this)

**Deliverable:** Clean codebase with accurate documentation

---

## Critical Files to Modify

| File | Changes |
|------|---------|
| `tools/telegram_bot.py` | Write to Supabase; add image extraction; fix markdown bug |
| `tools/utils.py` | Add Supabase helpers |
| `requirements.txt` | Add supabase, anthropic, httpx |
| `docs/ROADMAP.md` | Update with new architecture |
| NEW: `web/` | Entire Next.js application |
| NEW: `src/supabase/` | Supabase client module |
| NEW: `src/vision/` | Image extraction module |
| NEW: `scripts/migrate_to_supabase.py` | Data migration script |

---

## Resolved Questions

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Markdown backup** | Remove after migration | Clean break; Supabase is single source of truth |
| **Embedding generation** | Keep on VPS (BGE) | Free, private, already working; equivalent quality to OpenAI |
| **Domain name** | Decide later | Use Vercel default URL initially, configure custom domain after launch |

## Open Questions

1. **Rate limiting for chat**: What limits to control Claude API costs?

---

## Success Criteria

- [ ] All existing posts migrated to Supabase
- [ ] Bot archives new posts to Supabase
- [ ] Image descriptions extracted and searchable
- [ ] Web UI deployed and accessible
- [ ] RAG chat working with source citations
- [ ] Preview deployments functional
- [ ] Documentation updated

---

## References

- `docs/STACK_DECISION.md` - Stack decision rationale
- `docs/SUPABASE_EVALUATION.md` - Supabase evaluation
- `docs/FRONTEND_FRAMEWORK_EVALUATION.md` - Next.js vs React+Vite
- `docs/VERCEL_EVALUATION.md` - Vercel evaluation
- `docs/IMAGE_CONTENT_EXTRACTION.md` - Claude Vision implementation details
- `docs/TELEGRAM_MARKDOWN_BUG.md` - Markdown parsing bug and fix
