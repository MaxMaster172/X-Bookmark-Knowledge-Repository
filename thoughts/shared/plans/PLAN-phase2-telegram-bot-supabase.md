# Plan: Phase 2 - Telegram Bot Supabase Integration

## Goal

Update the Telegram bot and bulk import tool to write directly to Supabase instead of local files. This eliminates the multi-storage sync issue (markdown files + JSON indexes + ChromaDB) and unifies everything in PostgreSQL with pgvector.

## Technical Choices

- **Database Client**: Use existing `src/supabase/client.py` (already complete)
- **Embedding Storage**: Store 384-dim BGE embeddings directly in pgvector via `insert_post(embedding=...)`
- **Duplicate Check**: Replace file-based `check_duplicate()` with `SupabaseClient.post_exists()`
- **Vector Search**: Use `match_posts` RPC function (already working)
- **Message Formatting**: Switch from Telegram Markdown to HTML to avoid parsing bugs

## Current State Analysis

**CONFIRMED: Telegram bot currently saves to files, NOT Supabase.**

### Current Flow (telegram_bot.py):
```
save_archived_post() → YAML frontmatter → archive/posts/YYYY/MM/id.md
                     → JSON index      → data/index.json
                     → JSON tags       → data/tags.json
                     → git_sync()      → commits to repo
```

### Target Flow:
```
save_archived_post() → SupabaseClient.insert_post() → PostgreSQL + pgvector
                     → (Optional) SupabaseClient.insert_media() → post_media table
```

### Key Files:
- `tools/telegram_bot.py` - Main bot implementation (594 lines)
- `tools/bulk_import.py` - Notion import tool (484 lines)
- `tools/utils.py` - Shared utilities (file-based helpers)
- `src/supabase/client.py` - Supabase client (296 lines, complete)
- `src/embeddings/service.py` - BGE embedding generation (101 lines, complete)

### Supabase Client Methods Available:
- `insert_post()` - Insert with embedding support
- `post_exists()` - Check for duplicates
- `search_posts()` - Vector search via RPC
- `get_stats()` - Database statistics
- `get_recent_posts()` - Recent posts query
- `insert_media()` - Media metadata storage

## Tasks

### Task 1: Update telegram_bot.py - Imports and Initialization

Add Supabase client and embedding service imports, remove file-based imports.

- [ ] Add imports for `SupabaseClient` and `EmbeddingService`
- [ ] Remove unused imports from `utils.py` (keep only `extract_tweet_id` equivalent from `twitter_fetcher`)
- [ ] Initialize Supabase client in module scope (lazy singleton)

**Files to modify:**
- `tools/telegram_bot.py` (lines 1-50)

### Task 2: Update save_archived_post() Function

Replace file writes with Supabase insert. This is the core change.

- [ ] Build content string from thread (keep existing logic)
- [ ] Generate embedding using `EmbeddingService.generate()`
- [ ] Call `SupabaseClient.insert_post()` with all fields including embedding
- [ ] Handle media items via `insert_media()` if present
- [ ] Remove file write, index update, tags update, and git_sync calls
- [ ] Return post_id instead of file_path

**Files to modify:**
- `tools/telegram_bot.py` (lines 434-547, `save_archived_post` function)

### Task 3: Update Duplicate Checking

Replace file-based duplicate check with Supabase query.

- [ ] Create helper function `check_duplicate_supabase(post_id)` using `client.post_exists()`
- [ ] Update `handle_url()` to use new duplicate check
- [ ] Remove import of `check_duplicate` from utils

**Files to modify:**
- `tools/telegram_bot.py` (lines 230-260, `handle_url` function)

### Task 4: Update /stats Command

Query statistics from Supabase instead of JSON index.

- [ ] Use `SupabaseClient.get_stats()` to get post count, unique authors
- [ ] Update message formatting

**Files to modify:**
- `tools/telegram_bot.py` (lines 103-121, `stats` function)

### Task 5: Update /recent Command

Query recent posts from Supabase.

- [ ] Use `SupabaseClient.get_recent_posts(limit=5)`
- [ ] Format results for Telegram

**Files to modify:**
- `tools/telegram_bot.py` (lines 124-145, `recent` function)

### Task 6: Update /search Command - Add Semantic Search

Implement vector search using Supabase pgvector.

- [ ] Generate query embedding using `EmbeddingService.generate_for_query()`
- [ ] Call `SupabaseClient.search_posts()` with query embedding
- [ ] Format results showing similarity scores
- [ ] Keep keyword fallback for short queries or when embedding fails

**Files to modify:**
- `tools/telegram_bot.py` (lines 148-220, `search` and `keyword_search` functions)

### Task 7: Fix Telegram Markdown Parsing Bug

Switch from Markdown to HTML parse mode to avoid escaping issues.

- [ ] Change all `parse_mode="Markdown"` to `parse_mode="HTML"`
- [ ] Update message formatting to use HTML tags (`<b>`, `<i>`, `<code>`)
- [ ] Create `escape_html()` helper for dynamic content
- [ ] Update: `/start`, `/help`, `/stats`, `add_tags`, `add_topics`, `add_notes`

**Files to modify:**
- `tools/telegram_bot.py` (multiple locations)

### Task 8: Update bulk_import.py - Supabase Integration

Apply same changes to the bulk import tool.

- [ ] Add Supabase client and embedding service imports
- [ ] Update `save_posts()` to use `SupabaseClient.insert_post()`
- [ ] Update `generate_embeddings()` to store in pgvector (no ChromaDB)
- [ ] Update `check_duplicates()` to use `client.post_exists()`
- [ ] Remove git_sync calls
- [ ] Update preflight report to show Supabase stats

**Files to modify:**
- `tools/bulk_import.py`

### Task 9: Add Environment Variable Handling

Ensure Supabase credentials are loaded properly.

- [ ] Add `.env` file loading (python-dotenv) or document env var setup
- [ ] Update error messages to guide users on missing credentials
- [ ] Test credential loading from `SUPABASE CREDENTIALS.txt` (gitignored)

**Files to modify:**
- `tools/telegram_bot.py`
- `tools/bulk_import.py`

### Task 10: Create Integration Tests

Add tests to verify the Supabase integration works.

- [ ] Test `insert_post()` with embedding
- [ ] Test `post_exists()` duplicate detection
- [ ] Test `search_posts()` vector search
- [ ] Test error handling for missing credentials

**Files to create:**
- `tests/test_supabase_integration.py`

## Success Criteria

### Automated Verification:
- [ ] `python -c "from src.supabase import get_supabase_client; print(get_supabase_client().get_stats())"` - Client connects
- [ ] `python -c "from src.embeddings import get_embedding_service; print(get_embedding_service().generate('test')[:3])"` - Embeddings work
- [ ] Unit tests pass (if created)

### Manual Verification:
- [ ] Send a test X/Twitter URL to bot → Post appears in Supabase `posts` table
- [ ] Embedding is stored (not null) in the `embedding` column
- [ ] `/stats` shows correct count from Supabase
- [ ] `/recent` shows posts from Supabase
- [ ] `/search <query>` returns semantically similar posts
- [ ] Duplicate detection prevents re-archiving same post
- [ ] No markdown files created in `archive/posts/`
- [ ] No git commits attempted

## Out of Scope

- **Media content extraction (Phase 3)** - We store media URLs but don't extract descriptions
- **Thesis detection (Phase 7)** - No entity/thesis linking yet
- **Web UI (Phase 4-6)** - Telegram bot only
- **Removing old code** - Keep file-based code as fallback until migration complete
- **Backfilling existing posts** - Already done in Phase 1 migration

## Dependencies

- Supabase credentials in environment (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`)
- `match_posts` RPC function must exist in Supabase (confirmed working)
- sentence-transformers installed for BGE embeddings
- python-telegram-bot library

## Risk Mitigation

1. **Supabase connection failure**: Add try/catch with clear error messages
2. **Embedding generation slow**: Model already cached (singleton pattern)
3. **API rate limits**: Supabase free tier has generous limits for personal use
