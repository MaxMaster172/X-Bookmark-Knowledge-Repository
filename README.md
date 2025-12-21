# X/Twitter Bookmark Knowledge Repository

A personal archive system for Twitter/X posts, designed for easy manual capture and LLM-friendly retrieval.

## Why This Exists

Twitter/X bookmarks are a graveyard of forgotten insights. This repository provides:

- **Manual archiving** - Copy and paste posts you want to remember
- **Rich metadata** - Tag, categorize, and annotate your saves
- **LLM-ready exports** - Formats optimized for use with ChatGPT, Claude, etc.
- **Simple search** - Find posts by author, topic, tag, or full-text search
- **Git-backed** - Version controlled, portable, and yours forever

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Add your first post
cd tools
python add_post.py

# Search your archive
python search.py find "machine learning"

# Export for LLM use
python export.py llm --topic ai
```

## Directory Structure

```
├── archive/
│   ├── posts/           # Individual posts as markdown files
│   │   └── YYYY/MM/     # Organized by archive date
│   └── collections/     # Curated collections (manual)
├── data/
│   ├── index.json       # Searchable index
│   └── tags.json        # Tag taxonomy
├── tools/
│   ├── add_post.py      # Add new posts
│   ├── search.py        # Search and retrieve
│   ├── export.py        # Export for LLM use
│   └── utils.py         # Shared utilities
├── schemas/
│   └── post.schema.json # Data schema reference
└── exports/             # Generated exports
```

## Adding Posts

### Interactive Mode (Recommended)

```bash
python tools/add_post.py
```

Walks you through adding a post with prompts for:
- Post URL
- Content (copy/paste the tweet text)
- Author info
- Tags and topics
- Personal notes
- Importance level

### Quick Mode

```bash
python tools/add_post.py quick \
  "https://x.com/karpathy/status/123456789" \
  "The actual tweet content goes here..." \
  --tags ai,insight \
  --topics machine-learning \
  --importance high \
  --notes "Great explanation of transformers"
```

## Searching Posts

### Find posts by text

```bash
python tools/search.py find "attention mechanism"
```

### Filter by criteria

```bash
# By author
python tools/search.py find --author karpathy

# By tag
python tools/search.py find --tag insight

# By topic
python tools/search.py find --topic machine-learning

# By importance
python tools/search.py find --importance critical

# Combined
python tools/search.py find "neural" --author karpathy --tag ai
```

### Get a specific post

```bash
python tools/search.py get 123456789
```

### View archive stats

```bash
python tools/search.py stats
python tools/search.py tags
python tools/search.py authors
```

## Exporting for LLM Use

The key feature - export your archive in formats optimized for LLM context windows.

### LLM Context Format

Structured XML format designed for pasting into LLM conversations:

```bash
python tools/export.py llm --topic ai --limit 20
```

Output:
```xml
<archived_twitter_posts>
<post>
  <id>123456789</id>
  <author>@karpathy</author>
  <date>2024-01-15</date>
  <tags>ai, insight</tags>
  <content>The actual tweet content...</content>
  <user_notes>Your notes about why this matters</user_notes>
</post>
...
</archived_twitter_posts>
```

### Markdown Export

Human-readable format, also works well with LLMs:

```bash
python tools/export.py markdown --topic ai -o my_ai_posts.md
```

### Summary Export

Condensed format for fitting more posts in limited context:

```bash
python tools/export.py summary --limit 50
```

### JSON Export

For programmatic use:

```bash
python tools/export.py json --author karpathy
```

### Grouped Exports

```bash
# Separate files per author
python tools/export.py by-author

# Separate files per topic
python tools/export.py by-topic
```

## Post Schema

Each archived post supports:

| Field | Description |
|-------|-------------|
| `id` | Post ID from URL |
| `url` | Original post URL |
| `author.handle` | Twitter handle |
| `author.name` | Display name |
| `content` | Full post text |
| `posted_at` | Original post date |
| `archived_at` | When you saved it |
| `tags` | Your categorization tags |
| `topics` | Subject matter topics |
| `notes` | Your personal annotations |
| `importance` | low / medium / high / critical |
| `thread` | Thread position info |
| `media` | Image/video descriptions |

## Workflow Examples

### Building an AI Knowledge Base

1. When you see an insightful AI tweet, archive it:
   ```bash
   python tools/add_post.py
   # Add with tags: ai, insight
   # Add with topics: machine-learning, llm
   ```

2. Before working on an AI project, export relevant context:
   ```bash
   python tools/export.py llm --topic llm --importance high -o context.txt
   ```

3. Paste the export into your LLM conversation for informed assistance.

### Research Collection

1. Archive posts as you research a topic
2. Use consistent tags for the research project
3. Export when ready to synthesize:
   ```bash
   python tools/export.py markdown --tag my-research-project
   ```

### Personal Insights Journal

Tag posts with `insight` or `quote`, then periodically review:
```bash
python tools/search.py find --tag insight --format full
```

## Tips

- **Be consistent with tags** - Use a small set of tags repeatedly
- **Use topics for subject matter** - Topics are what the post is *about*
- **Use tags for your categorization** - Tags are *why you saved it*
- **Add notes liberally** - Future you will thank present you
- **Mark important posts** - Use `high` or `critical` for must-remember content
- **Export regularly** - Build topic-specific context files for LLM use

## License

MIT - This is your personal knowledge base, do what you want with it.
