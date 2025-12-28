---
date: 2025-12-28T18:30:00-05:00
type: plan
status: complete
plan_file: thoughts/shared/plans/PLAN-phase2-telegram-bot-supabase.md
---

# Plan Handoff: Phase 2 - Telegram Bot Supabase Integration

## Summary

Created comprehensive implementation plan for migrating the Telegram bot from file-based storage to Supabase. The plan covers 10 tasks including updating `save_archived_post()`, adding vector search, fixing Markdown bugs, and updating `bulk_import.py`.

## Plan Created

`thoughts/shared/plans/PLAN-phase2-telegram-bot-supabase.md`

## Key Technical Decisions

- **Use existing Supabase client**: `src/supabase/client.py` is already complete with all needed methods
- **Store embeddings in pgvector**: Use `insert_post(embedding=...)` instead of ChromaDB
- **Switch to HTML parsing**: Fix Telegram Markdown bugs by using `parse_mode="HTML"`
- **Keep embedding generation on VPS**: BGE model is free, private, already working

## Task Overview

1. **Update imports** - Add Supabase/embedding imports, remove file-based imports
2. **Update save_archived_post()** - Core change: write to Supabase instead of files
3. **Update duplicate checking** - Use `post_exists()` instead of JSON index
4. **Update /stats** - Query `get_stats()` from Supabase
5. **Update /recent** - Query `get_recent_posts()` from Supabase
6. **Update /search** - Add semantic vector search via pgvector
7. **Fix Markdown bug** - Switch all messages to HTML parse mode
8. **Update bulk_import.py** - Apply same Supabase changes
9. **Add env var handling** - Load Supabase credentials properly
10. **Create integration tests** - Verify the integration works

## Research Findings

- `tools/telegram_bot.py:434-547` - `save_archived_post()` writes YAML files + JSON indexes + git sync
- `tools/utils.py:213-216` - `check_duplicate()` reads from JSON index
- `src/supabase/client.py:53-117` - `insert_post()` already supports embedding parameter
- `src/embeddings/service.py:43-55` - `generate()` returns 384-dim embedding list
- `match_posts` RPC function confirmed working in Supabase

## Assumptions Made

- Supabase credentials are available via environment variables on the VPS
- The `match_posts` RPC function exists and works (confirmed in Phase 1)
- No need to maintain backward compatibility with file-based storage

## For Next Steps

1. User should review plan at: `thoughts/shared/plans/PLAN-phase2-telegram-bot-supabase.md`
2. After approval, run `/implement_plan` with the plan path
3. Or use `/validate-agent` to check tech choices before implementation
