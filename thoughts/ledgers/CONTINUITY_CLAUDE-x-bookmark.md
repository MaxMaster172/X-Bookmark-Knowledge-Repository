# X-Bookmark Knowledge Repository - Continuity Ledger

> Last updated: 2026-01-03 (Phase 6 COMPLETE - Vercel Deployment)

## Goal

Transform Twitter bookmarks into a queryable personal knowledge base with:
- Semantic search (vector embeddings)
- Thesis-based knowledge management
- RAG-powered chat interface
- Modern cloud-native architecture

**Definition of Done:** Full web UI with RAG chat, thesis detection, and knowledge graph visualization.

## Constraints

- **Embedding model**: BAAI/bge-small-en-v1.5 (384 dims) - local, free, private
- **Database**: Supabase PostgreSQL + pgvector
- **Frontend**: Next.js on Vercel (planned)
- **Bot**: Telegram bot on Hetzner VPS
- **Cost target**: <$35/month (mostly Claude API usage)

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Vector store | pgvector over ChromaDB | Unified with main DB, same query language |
| Frontend | Next.js over React+Vite | Built-in API routes for Claude key security |
| Hosting | Vercel over self-hosted | Git-push deploys, global CDN, auto SSL |
| Embeddings | Local BGE over OpenAI | Free, private, already working |

## State

- Done:
  - [x] Phase 1: Supabase Setup & Data Migration
    - Supabase project: `yjjgtwydeoijxrewbisl.supabase.co`
    - Schema: 12 tables including thesis system
    - Data: 4 posts migrated with embeddings
    - Vector search: `match_posts` RPC function working
    - Python client: `src/supabase/client.py` complete
  - [x] Phase 2: Telegram Bot Update
    - Updated `telegram_bot.py` to write to Supabase
    - Semantic search via pgvector `match_posts` RPC
    - Fixed Markdown parsing (switched to HTML)
    - Updated `bulk_import.py` for Supabase
    - Added python-dotenv for env var loading
    - Created integration tests (`tests/test_supabase_integration.py`)
- Done:
  - [x] Phase 3: Image Content Extraction
    - Created `src/vision/` module (extractor.py, prompts.py)
    - Integrated into telegram_bot.py
    - Deployed to VPS with ANTHROPIC_API_KEY
    - Backfill complete: 12/14 images processed (2 failed: 1 video, 1 deleted)
- Done:
  - [x] Phase 4: Next.js Application
    - Next.js 16 + Tailwind + shadcn/ui + Transformers.js
    - 4 themes: light, dark, sepia, nord (next-themes)
    - Browser-based semantic search (BGE embeddings via Transformers.js)
    - Pages: Home, Search, Post, Recent, Entities, Theses
    - Components: PostCard, SearchBar, EntityBadge, ThesisBadge, etc.
    - Design decisions documented in `web/docs/DESIGN_DECISIONS.md`
- Done:
  - [x] Phase 5: RAG Chat Interface
    - Claude Sonnet 4 (`claude-sonnet-4-20250514`) via Anthropic SDK with SSE streaming
    - `/api/chat` route with RAG context retrieval
    - `useChat` hook with embedding generation and streaming
    - Chat UI: ChatMessage, ChatInput, ContextSidebar, SourceCitation
    - `/chat` page with example prompts, auto-scroll, mobile drawer
    - Navigation links in Header, Home, Post pages
    - Rate limiting: 20 msg/hour (client-side localStorage)
    - Fix: Migrated from `@xenova/transformers` to `@huggingface/transformers` (Next.js 16 compat)
    - Handoffs: `thoughts/handoffs/x-bookmark-phase5/task-*.md`
- Done:
  - [x] Phase 6: Vercel Deployment
    - Deployed to Vercel: https://web-five-swart-90.vercel.app
    - Environment variables: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, ANTHROPIC_API_KEY
    - All pages functional: Home, Search, Chat, Recent, Entities, Theses
    - Supabase CORS working out of the box with anon key
- Now: [→] Phase 7: Thesis System & Knowledge Graph
- Remaining:
  - [ ] Phase 7: Thesis System & Knowledge Graph
  - [ ] Phase 8: Research Sessions & Discovery
  - [ ] Phase 9: Cleanup & Documentation

## Open Questions

- ~~**Rate limiting for chat**: What limits to control Claude API costs?~~ RESOLVED: 20 msg/hour client-side tracking
- ~~UNCONFIRMED: Is the Telegram bot currently saving to files or already Supabase?~~ CONFIRMED: Now writes to Supabase only.

## Working Set

### Key Files
- `docs/ARCHITECTURE.md` - Master architecture document (APPROVED)
- `docs/THESIS_SYSTEM_DESIGN.md` - Thesis system design
- `deploy/sql/001_initial_schema.sql` - Database schema
- `src/supabase/client.py` - Supabase Python client
- `src/vision/` - Image extraction module (Phase 3)
- `tools/telegram_bot.py` - Telegram bot (Phase 3 integrated)
- `scripts/backfill_image_descriptions.py` - Image backfill script
- `web/` - Next.js application (Phase 4)
- `web/docs/DESIGN_DECISIONS.md` - Phase 4 design decisions
- `thoughts/shared/plans/PLAN-phase5-rag-chat.md` - Phase 5 implementation plan

### Environment
- Branch: `main`
- Supabase URL: `https://yjjgtwydeoijxrewbisl.supabase.co`
- Credentials file: `SUPABASE CREDENTIALS.txt` (gitignored)

### Test Commands
```bash
# Test Supabase connection
python -c "import os; os.environ['SUPABASE_URL']='...'; from src.supabase import get_supabase_client; print(get_supabase_client().get_stats())"

# Run migration dry-run
python scripts/migrate_to_supabase.py --dry-run

# Test vector search
python tools/search.py find "AI investing" --semantic
```

## Phase 3 Implementation Checklist (CODE COMPLETE)

Per `docs/ARCHITECTURE.md` Phase 3:

1. [x] Create vision module:
   - [x] `src/vision/prompts.py` - Category-specific extraction prompts
   - [x] `src/vision/extractor.py` - Claude Vision API wrapper (singleton)
   - [x] `src/vision/__init__.py` - Module exports
2. [x] Update Supabase client:
   - [x] Add `update_media()` method
   - [x] Add `get_media_without_descriptions()` method
3. [x] Integrate into telegram_bot.py:
   - [x] Image extraction before media insert
   - [x] Include descriptions in embedding text
   - [x] Environment vars: ENABLE_IMAGE_EXTRACTION, MAX_IMAGES_TO_EXTRACT
4. [x] Create backfill script:
   - [x] `scripts/backfill_image_descriptions.py`
   - [x] CLI with --dry-run, --limit, --regenerate-embeddings
5. [x] Deploy to VPS:
   - [x] Add ANTHROPIC_API_KEY to .env
   - [x] Add ENABLE_IMAGE_EXTRACTION=true to .env
   - [x] Pull code, reinstall deps, restart bot
6. [x] Run backfill on existing images (12/14 succeeded)

## Phase 2 Implementation Checklist (COMPLETE)

Per `docs/ARCHITECTURE.md` Phase 2:

1. [x] Install supabase Python client (already in requirements.txt)
2. [x] Update `tools/telegram_bot.py`:
   - [x] Modify `save_archived_post()` to write to Supabase
   - [x] Keep BGE embedding generation (already working)
   - [x] Store embedding in pgvector instead of ChromaDB
   - [x] Remove git sync (no more markdown files)
3. [x] Update `/search` command to use Supabase vector search
4. [x] Fix Telegram Markdown bug (switch to HTML parse mode)
5. [x] Update `tools/bulk_import.py` to write to Supabase
6. [x] Add python-dotenv for environment variable loading
7. [x] Create integration tests

## Stats

- **Total posts**: 27 (all migrated to Supabase)
- **Unique authors**: Multiple (expanded from original 3)
- **Database tables**: 12 (all schema applied)
- **Embeddings**: 384-dimensional vectors on all posts
- **VPS status**: Bot running with new Supabase code

## Session Auto-Summary (2025-12-28T19:11:44.439Z)
- Files changed: C
## Session Auto-Summary (2025-12-28T19:14:28.720Z)
- Files changed: C
## Session Auto-Summary (2025-12-31T14:43:46.752Z)
- Files changed: C