# Bulk Import from Notion

> **Status**: Planned feature - not yet implemented
> **Priority**: Low (nice-to-have)
> **Complexity**: Low
> **Created**: 2024-12-27

## Overview

A simple utility to bulk import X/Twitter post URLs from a Notion page into the knowledge repository. This is a "longshot" feature for migrating posts that were temporarily collected in Notion before this system existed.

---

## The Problem

Before this knowledge repository was built, X/Twitter posts were being saved to a Notion page as bookmarks. These need to be migrated into the archive so they're searchable via semantic search and available to the RAG chat system.

---

## Design Philosophy

**Keep it simple.** This feature prioritizes:

1. **Minimal complexity** - Just a script that processes a list of URLs
2. **No manual metadata** - Tags, topics, importance levels are unnecessary
3. **Let AI handle organization** - Embeddings and knowledge graph will handle discovery
4. **One-time migration focus** - Not building ongoing Notion sync

### Why No Metadata?

The system uses:
- **Embeddings** for semantic similarity search
- **RAG chat** for intelligent Q&A
- **Knowledge-entity graph** (future) for relationship mapping

Manual categorization becomes redundant when AI layers handle discovery. The *content itself* is what matters - store it, embed it, done.

---

## Approach: Simple URL List Processing

### Input

A plain text file with one URL per line:

```
https://x.com/parcadei/status/2004018525569274049
https://x.com/parcadei/status/2004255802979504636
https://x.com/adocomplete/status/2004258607094026270
https://x.com/rahulgs/status/2004393052224606353
https://x.com/0xPaulius/status/2003784545594917088
```

### How to Get This List from Notion

**Option A: Export as Markdown**
1. Open your Notion page
2. Click `...` menu → Export → Markdown
3. Open the exported `.md` file
4. Extract URLs with a simple regex or manual copy

**Option B: Copy-Paste**
1. Select all content on the Notion page
2. Paste into a text editor (Notion pastes as markdown)
3. Extract the URLs

**Option C: Manual Collection**
1. Click each bookmark in Notion
2. Copy the underlying URL
3. Paste into a text file

For a "not that extensive" Notion page, any of these work fine.

---

## Implementation Plan

### Script: `tools/bulk_import.py`

```
Usage:
  python tools/bulk_import.py <urls_file>
  python tools/bulk_import.py urls.txt --dry-run
  python tools/bulk_import.py urls.txt --delay 2
```

### Core Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     BULK IMPORT FLOW                        │
└─────────────────────────────────────────────────────────────┘

1. READ URL FILE
   ├── Parse urls.txt line by line
   ├── Validate: must match x.com or twitter.com pattern
   └── Extract tweet IDs from URLs

2. DUPLICATE CHECK
   ├── Load index.json
   ├── Compare tweet IDs against existing posts
   └── Filter out already-archived posts

3. PRE-FLIGHT REPORT
   │
   │  "Found 47 URLs"
   │  "Already archived: 12 (will skip)"
   │  "To import: 35"
   │  "Continue? [Y/n]"
   │

4. FETCH LOOP (for each URL)
   ├── Call FxTwitter API (reuse twitter_fetcher.py)
   ├── Handle threads (fetch all tweets in thread)
   ├── Rate limit: sleep between requests
   ├── On failure: log to bulk_import_errors.log, continue
   └── On success: add to batch

5. BATCH SAVE
   ├── Write markdown files to archive/posts/YYYY/MM/
   ├── Update index.json
   ├── Update tags.json (minimal: just track post exists)
   ├── Generate embeddings (ChromaDB)
   └── Single git commit: "Bulk import: 35 posts from Notion"

6. SUMMARY REPORT
   │
   │  "Import complete!"
   │  "Successfully imported: 33"
   │  "Failed to fetch: 2 (see bulk_import_errors.log)"
   │  "Skipped (duplicate): 12"
   │
```

---

## Technical Details

### Dependencies

Reuses existing modules - no new dependencies:

| Module | Purpose |
|--------|---------|
| `tools/twitter_fetcher.py` | Fetch posts via FxTwitter API |
| `tools/utils.py` | Index/tags I/O, git sync |
| `src/embeddings/service.py` | Generate embeddings |
| `src/embeddings/vector_store.py` | Store in ChromaDB |

### URL Validation

```python
import re

X_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/(\d+)'
)

def extract_tweet_id(url: str) -> str | None:
    """Extract tweet ID from X/Twitter URL."""
    match = X_URL_PATTERN.match(url)
    return match.group(1) if match else None
```

### Rate Limiting

FxTwitter is a free service - be respectful:

```python
DEFAULT_DELAY = 1.5  # seconds between requests

for url in urls_to_import:
    result = fetch_thread(url)
    # ... process ...
    time.sleep(delay)
```

### Error Handling

Non-blocking failures - log and continue:

```python
errors = []
for url in urls:
    try:
        thread = fetch_thread(url)
        save_post(thread)
        successes.append(url)
    except Exception as e:
        errors.append({"url": url, "error": str(e)})
        continue

# Write errors to log file
if errors:
    with open("bulk_import_errors.log", "w") as f:
        for err in errors:
            f.write(f"{err['url']}: {err['error']}\n")
```

### Metadata Stored

Only what comes from the post itself:

```yaml
---
id: '2004018525569274049'
url: https://x.com/parcadei/status/2004018525569274049
author:
  handle: parcadei
  name: dei
content: "continuous claude v2 is now up..."
posted_at: Wed Dec 25 10:30:00 +0000 2025
archived_at: '2025-12-27T15:00:00.000000'
archived_via: bulk_import
tags: []
topics: []
notes: ""
media: []
thread:
  is_thread: false
---
```

Key difference: `archived_via: bulk_import` to distinguish from telegram/manual entries.

---

## CLI Interface

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `urls_file` | Yes | Path to file containing URLs (one per line) |
| `--dry-run` | No | Show what would be imported without doing it |
| `--delay` | No | Seconds between API requests (default: 1.5) |
| `--skip-confirm` | No | Skip the confirmation prompt |
| `--no-embed` | No | Skip embedding generation (faster, but no semantic search) |

### Example Session

```bash
$ python tools/bulk_import.py notion_urls.txt

Bulk Import - X-Bookmark Knowledge Repository
─────────────────────────────────────────────

Reading URLs from: notion_urls.txt
Found 47 URLs

Checking for duplicates...
Already archived: 12 posts (will skip)
New posts to import: 35

Continue with import? [Y/n] y

Importing posts...
[1/35] @parcadei/2004018525569274049 ✓
[2/35] @parcadei/2004255802979504636 ✓
[3/35] @adocomplete/2004258607094026270 ✓
...
[18/35] @someuser/1234567890 ✗ (post not found)
...
[35/35] @lastuser/9876543210 ✓

Generating embeddings...
[████████████████████████████████] 33/33

Saving to archive...
Committing changes...

─────────────────────────────────────────────
Import Complete!

✓ Successfully imported: 33
✗ Failed to fetch: 2
  - https://x.com/someuser/status/1234567890 (post not found)
  - https://x.com/another/status/5555555555 (account suspended)
○ Skipped (duplicate): 12

Errors logged to: bulk_import_errors.log
```

---

## File Structure

```
tools/
└── bulk_import.py       # New script

# Generated during import:
bulk_import_errors.log   # Failed URLs (if any)
```

---

## Alternative Approaches (Not Recommended)

These were considered but rejected for being overkill:

### Notion API Integration
- Requires API setup, auth tokens
- More complex than needed for one-time migration
- Useful if doing ongoing sync (not our use case)

### Full UI with Preview/Edit
- Over-engineered for a simple bulk import
- Can always edit posts after import if needed
- YAGNI (You Ain't Gonna Need It)

### Preserving Notion Structure
- Could map Notion headings to topics
- Adds complexity for questionable value
- AI layers will find relationships anyway

---

## Current Status

**Implemented**: `tools/bulk_import.py` - CLI script that imports from Notion Markdown exports to local filesystem.

**Important**: This script currently writes to local files (`archive/posts/*.md`). After the Supabase migration (see `ARCHITECTURE.md`), it will need to be updated to write directly to Supabase instead.

---

## When to Use This

**Recommended**: Wait until after Supabase migration is complete (Phase 2 in ARCHITECTURE.md). Then:
1. Update `bulk_import.py` to write to Supabase (similar changes as telegram_bot.py)
2. Run the import once - posts go directly to the central database

**Why wait?** Currently the Telegram bot runs on a Hetzner VPS and saves posts there. Running bulk import locally would create a separate archive out of sync with the VPS. Supabase provides a single source of truth.

---

## Future Enhancements (If Needed)

Only build these if the simple version proves insufficient:

1. **Resume from failure** - Save progress, restart from where it stopped
2. **Parallel fetching** - Multiple API calls at once (careful with rate limits)
3. **Notion API mode** - Direct API access instead of export
4. **Interactive mode** - Review each post before saving

---

## References

- FxTwitter API: https://github.com/FixTweet/FxTwitter
- Existing fetcher: `tools/twitter_fetcher.py`
- Existing utilities: `tools/utils.py`
- Embedding service: `src/embeddings/service.py`
