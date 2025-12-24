# Stack Decision: Adopting Supabase + Next.js + Vercel

> Last updated: 2024-12-24
> Status: **DECIDED**

## The Decision

We are adopting a modern cloud-native stack:

| Layer | Technology | Replaces |
|-------|------------|----------|
| **Frontend** | Next.js | React + Vite + React Router |
| **Deployment** | Vercel | Self-hosted on VPS with Nginx |
| **Database** | Supabase (PostgreSQL + pgvector) | ChromaDB + JSON files + Markdown |
| **API** | Supabase Auto-API + Next.js API Routes | FastAPI |
| **Bot Hosting** | Hetzner VPS | (unchanged) |

---

## Why This Stack

### Supabase (Database + Backend)

**The problem it solves:**
- Current file-based storage (markdown + JSON) doesn't scale to relational queries
- Planned features (Research Sessions, Knowledge Graph) need proper relationships
- ChromaDB works but adds another system to maintain
- No unified query layer across posts, tags, sessions, and vectors

**What we gain:**
- PostgreSQL with pgvector: unified storage for posts AND embeddings
- Auto-generated REST API: no need to build FastAPI endpoints
- Realtime subscriptions: perfect for streaming chat
- Row Level Security: future multi-user support if ever needed
- Managed backups and infrastructure

**Evaluation:** See `docs/SUPABASE_EVALUATION.md`

---

### Next.js (Frontend Framework)

**The problem it solves:**
- React + Vite is frontend-only; can't safely call Claude API (exposes key)
- Would need separate backend just for Claude API routes
- Manual routing setup with React Router

**What we gain:**
- Built-in API routes: Claude calls live in `/app/api/chat/route.ts`
- File-based routing: less boilerplate
- Optimized for Vercel deployment
- Server and client components when needed
- Large ecosystem, excellent documentation

**Evaluation:** See `docs/FRONTEND_FRAMEWORK_EVALUATION.md`

---

### Vercel (Deployment Platform)

**The problem it solves:**
- Manual deployment: SSH → git pull → build → restart
- Single server location (latency for remote access)
- Manual SSL certificate management
- No preview environments for testing

**What we gain:**
- Git push deployment: automatic builds and deploys
- Global CDN: frontend served from nearest edge
- Preview URLs: every branch gets a test environment
- Automatic HTTPS
- Optimized for Next.js (they created it)

**Evaluation:** See `docs/VERCEL_EVALUATION.md`

---

## Architecture Overview

### Before (Original Plan)

```
┌────────────────────── Hetzner VPS ──────────────────────┐
│                                                          │
│   Telegram Bot    FastAPI       React (static)          │
│        │             │               │                  │
│        ▼             ▼               ▼                  │
│   ┌─────────────────────────────────────────────────┐   │
│   │  Markdown Files   ChromaDB   JSON Indexes       │   │
│   └─────────────────────────────────────────────────┘   │
│                                                          │
│   Nginx reverse proxy                                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Characteristics:**
- Everything on one server
- Multiple data stores to sync
- Manual deployment
- Custom API layer needed

---

### After (New Stack)

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
- Unified data layer (Supabase)
- Automatic deployment (Vercel)
- VPS only runs the bot

---

## What Changes

### Data Storage

| Before | After |
|--------|-------|
| Posts: Markdown files with YAML | Posts: PostgreSQL table |
| Indexes: `index.json`, `tags.json` | Indexes: SQL queries |
| Embeddings: ChromaDB | Embeddings: pgvector column |
| Sessions: JSON files (planned) | Sessions: PostgreSQL tables |

### API Layer

| Before | After |
|--------|-------|
| FastAPI (custom endpoints) | Supabase auto-API (CRUD) |
| Build search, posts, stats routes | Query Supabase directly |
| Separate Claude API backend | Next.js API routes |

### Deployment

| Before | After |
|--------|-------|
| SSH to VPS | Git push |
| Manual nginx config | Automatic |
| Certbot for SSL | Automatic HTTPS |
| Single location | Global CDN |

### Development

| Before | After |
|--------|-------|
| React + Vite + React Router | Next.js (all-in-one) |
| Separate backend process | API routes in same project |
| No preview environments | Preview URL per branch |

---

## What Stays the Same

| Component | Status |
|-----------|--------|
| **Telegram Bot** | Stays on Hetzner VPS, updates to write to Supabase |
| **Tailwind CSS** | Still used for styling |
| **shadcn/ui** | Still used for components |
| **Claude API** | Still used for RAG (called from Next.js API routes) |
| **BGE Embeddings** | Still used, but generated server-side and stored in pgvector |

---

## Trade-offs Accepted

### 1. Loss of Git-Versioned Posts

**Before:** Every post is a markdown file, full git history of changes.

**After:** Posts live in PostgreSQL, no git diff.

**Why acceptable:** Posts are archived tweets (write-once). Edit history has limited value. Supabase provides point-in-time recovery if needed.

---

### 2. Split Architecture

**Before:** One VPS, everything in one place.

**After:** Three services (Vercel, Supabase, VPS).

**Why acceptable:** Each service is specialized and reliable. Integration patterns are well-established. Easier to maintain than custom FastAPI + ChromaDB + Nginx.

---

### 3. External Dependencies

**Before:** Self-hosted, full control.

**After:** Dependent on Vercel and Supabase uptime.

**Why acceptable:** Both have excellent uptime. Both are open-source and self-hostable if needed. For a personal project, the convenience outweighs the dependency risk.

---

### 4. Potential Costs at Scale

**Before:** Fixed VPS cost (~$5-10/month).

**After:** Usage-based pricing could increase.

**Why acceptable:** Free tiers are generous. Personal use stays well within limits. Would need significant growth to incur costs.

---

## Migration Path

### Phase 1: Supabase Setup
- Create Supabase project
- Design and create schema (posts, media, sessions)
- Enable pgvector extension
- Migrate existing posts from markdown to database
- Migrate embeddings from ChromaDB to pgvector

### Phase 2: Telegram Bot Update
- Update bot to write to Supabase instead of files
- Update embedding generation to store in pgvector
- Test full archive flow

### Phase 3: Next.js Application
- Initialize Next.js project with Tailwind + shadcn/ui
- Build core pages (home, search, post detail)
- Implement Supabase client integration
- Build chat page with Claude API route

### Phase 4: Vercel Deployment
- Connect repository to Vercel
- Configure environment variables
- Set up custom domain
- Verify preview deployments work

### Phase 5: Cleanup
- Decommission FastAPI (never built)
- Remove ChromaDB dependency
- Update documentation
- Archive old markdown files (for reference)

---

## Cost Summary

| Service | Tier | Cost |
|---------|------|------|
| **Vercel** | Hobby (Free) | $0/month |
| **Supabase** | Free | $0/month |
| **Hetzner VPS** | Existing | ~$5-10/month |
| **Claude API** | Pay-as-you-go | ~$5-20/month (usage dependent) |

**Total:** ~$10-30/month (mostly Claude API for RAG)

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-12-24 | Adopt Supabase | Unified data layer, relational queries for planned features |
| 2024-12-24 | Adopt Next.js | Built-in API routes solve Claude key placement |
| 2024-12-24 | Adopt Vercel | Optimal Next.js deployment, git-push deploys |
| 2024-12-24 | Keep VPS for bot | Telegram bot needs persistent Python process |

---

## References

- `docs/SUPABASE_EVALUATION.md` - Full Supabase analysis
- `docs/FRONTEND_FRAMEWORK_EVALUATION.md` - React vs Next.js analysis
- `docs/VERCEL_EVALUATION.md` - Full Vercel analysis
- `docs/ROADMAP.md` - Original project roadmap (to be updated)
- `docs/SEMANTIC_SEARCH_DESIGN.md` - Original design (to be updated)
