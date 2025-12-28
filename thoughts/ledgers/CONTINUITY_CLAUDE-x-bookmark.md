# X-Bookmark Knowledge Repository - Continuity Ledger

> Last updated: 2025-12-28

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
- Now: [→] Phase 2: Telegram Bot Update
- Next: Phase 3: Image Content Extraction
- Remaining:
  - [ ] Phase 4: Next.js Application
  - [ ] Phase 5: RAG Chat Interface
  - [ ] Phase 6: Vercel Deployment
  - [ ] Phase 7: Thesis System & Knowledge Graph
  - [ ] Phase 8: Research Sessions & Discovery
  - [ ] Phase 9: Cleanup & Documentation

## Open Questions

- **Rate limiting for chat**: What limits to control Claude API costs?
- UNCONFIRMED: Is the Telegram bot currently saving to files or already Supabase?

## Working Set

### Key Files
- `docs/ARCHITECTURE.md` - Master architecture document (APPROVED)
- `docs/THESIS_SYSTEM_DESIGN.md` - Thesis system design
- `deploy/sql/001_initial_schema.sql` - Database schema
- `src/supabase/client.py` - Supabase Python client
- `tools/telegram_bot.py` - Telegram bot (needs Phase 2 update)
- `scripts/migrate_to_supabase.py` - Migration script (completed)

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

## Phase 2 Implementation Checklist

Per `docs/ARCHITECTURE.md` Phase 2:

1. [ ] Install supabase Python client (already in requirements.txt)
2. [ ] Update `tools/telegram_bot.py`:
   - [ ] Modify `save_archived_post()` to write to Supabase
   - [ ] Keep BGE embedding generation (already working)
   - [ ] Store embedding in pgvector instead of ChromaDB
   - [ ] Remove git sync (no more markdown files)
3. [ ] Update `/search` command to use Supabase vector search
4. [ ] Fix Telegram Markdown bug (switch to HTML parse mode)
5. [ ] Update `tools/bulk_import.py` to write to Supabase

## Stats

- **Total posts**: 4 (in both files and Supabase)
- **Unique authors**: 3
- **Database tables**: 12 (all schema applied)
- **Embeddings**: 384-dimensional vectors on all posts
