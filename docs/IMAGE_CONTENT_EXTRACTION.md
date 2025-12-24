# Image Content Extraction Design & Implementation Plan

> Last updated: 2024-12-24 (added category-specific extraction prompts)

## Overview

This document describes the design and implementation plan for extracting semantic content from images in archived posts. The goal is to ensure that visual content (charts, analyst notes, diagrams, screenshots) is captured in a form that the RAG system can understand and retrieve.

---

## Part 1: The Problem

### Current State

Posts with images currently have this structure in their frontmatter:

```yaml
media:
- type: photo
  url: https://pbs.twimg.com/media/example.jpg
```

**What's captured:** URL reference to the image
**What's missing:** The *content* of the image - what a human sees when they look at it

### Why This Matters for RAG

Many archived posts contain images that are **critical to understanding the content**:

| Image Type | Example | RAG Impact |
|------------|---------|------------|
| Charts/Graphs | S&P 500 performance chart with analyst annotations | Numbers, trends, insights completely invisible to text search |
| Screenshots | Code snippets, terminal output, UI mockups | Technical details lost |
| Analyst Notes | Hand-drawn diagrams, whiteboard photos | Conceptual explanations invisible |
| Infographics | Process flows, comparison tables | Structured information missing |
| Memes with Text | Commentary on industry trends | Cultural context and humor lost |

### The Gap in Current Pipeline

```
Current flow:
Post with image → URL stored → Embedding generated from TEXT ONLY → RAG sees no image content

Desired flow:
Post with image → Vision model describes image → Description stored → Embedding includes description → RAG understands visual content
```

### Risk: URL Decay

Media URLs become invalid when:
- Original tweet is deleted
- Account is suspended
- Twitter changes CDN structure

Once the URL dies, the image is gone forever. **Extracting descriptions NOW preserves the semantic content permanently**, even if the image becomes inaccessible later.

---

## Part 2: Solution Design

### Core Approach: Vision-Based Content Extraction

Use Claude's vision capabilities to generate rich text descriptions of images at archive time.

```
Image URL → Claude Vision API → Structured Description → Stored in post → Included in embeddings
```

### Why Claude Vision?

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Claude Vision** | Already using Claude for RAG, high quality, understands context | API cost per image | **SELECTED** |
| GPT-4 Vision | High quality | Different API, additional complexity | Rejected |
| Local models (LLaVA, etc.) | Free, private | Quality varies, requires GPU/significant resources | Rejected |
| Manual descriptions | Perfect accuracy | Doesn't scale, friction | Only for edge cases |

**Rationale:** We're already planning to use Claude for RAG (Phase 6). Using Claude Vision maintains a single API relationship and ensures high-quality descriptions that work well with Claude's RAG responses.

### Description Schema

Extend the existing media schema to include rich descriptions:

```yaml
media:
- type: photo
  url: https://pbs.twimg.com/media/example.jpg
  category: chart  # "text_heavy", "chart", or "general"
  description: "S&P 500 performance chart showing 15% YTD gains through Q3 2024. Key annotations highlight: (1) March dip correlating with banking concerns, (2) July rally following Fed pause, (3) Analyst note: 'Expecting consolidation before year-end push'. Chart style is candlestick with 50-day and 200-day moving averages overlaid."
  extracted_at: 2024-12-24T10:30:00Z
  extraction_model: claude-3-5-sonnet-20241022
```

**Example for text-heavy image (analyst note):**
```yaml
media:
- type: photo
  url: https://pbs.twimg.com/media/analyst_note.jpg
  category: text_heavy
  description: |
    [TRANSCRIPTION]
    Key Observations - Q4 2024:
    1. Fed pivot confirmed - expect 3 cuts in 2025
    2. Credit spreads tightening → risk-on environment
    3. Watch: JPY carry trade unwind risk

    Action items:
    - Rotate from defensives to cyclicals
    - Add duration to fixed income
    - Hedge tail risk via VIX calls

    [CONTEXT]
    Handwritten analyst note on lined paper, appears to be meeting notes or personal research summary. Blue ink with some words underlined for emphasis.
  extracted_at: 2024-12-24T10:30:00Z
  extraction_model: claude-3-5-sonnet-20241022
```

### Description Quality Guidelines

The vision prompt should extract:

1. **Literal content**: What is visually shown (text, numbers, shapes)
2. **Semantic meaning**: What the image conveys or argues
3. **Context clues**: Timestamps, sources, author annotations
4. **Structural information**: Chart types, table layouts, flow directions

**Bad description:** "A chart showing stock performance"
**Good description:** "Line chart of NVIDIA stock price (NVDA) from Jan-Dec 2024, showing 180% gain from ~$480 to ~$1,350. Notable events annotated: 'GTC keynote' in March with 15% spike, 'Blackwell announcement' in September. Y-axis ranges $400-$1,400, X-axis shows monthly intervals. Source watermark: '@marketanalyst'"

---

## Part 3: Integration Points

### 3.1 Archive Flow Integration

**Location:** `tools/telegram_bot.py` in `save_archived_post()` function (around line 540)

```python
# After fetching tweet, before saving:

async def extract_image_descriptions(media_items: list, post_context: str) -> list:
    """Use Claude Vision to describe images in context of the post."""
    from src.vision.extractor import ImageContentExtractor

    extractor = ImageContentExtractor()
    enriched_media = []

    for item in media_items:
        if item.get("type") in ["photo", "image"]:
            try:
                description = await extractor.describe_image(
                    image_url=item["url"],
                    post_context=post_context  # Include tweet text for context
                )
                enriched_media.append({
                    **item,
                    "description": description,
                    "extracted_at": datetime.utcnow().isoformat() + "Z",
                    "extraction_model": extractor.model_id
                })
            except Exception as e:
                logger.warning(f"Failed to extract image content: {e}")
                enriched_media.append(item)  # Keep original without description
        else:
            enriched_media.append(item)  # Videos, GIFs unchanged

    return enriched_media
```

### 3.2 Embedding Enhancement

**Location:** `tools/telegram_bot.py` embedding text construction (around line 598)

```python
# Current:
embed_text = content
embed_text += f"\n\nAuthor: @{thread.author_handle}"
# ... tags, topics, notes

# Enhanced:
embed_text = content
embed_text += f"\n\nAuthor: @{thread.author_handle}"

# Add image descriptions to embedding
if data.get("media"):
    image_descriptions = [
        m.get("description")
        for m in data["media"]
        if m.get("description")
    ]
    if image_descriptions:
        embed_text += f"\n\nImage content: {' | '.join(image_descriptions)}"

# ... tags, topics, notes
```

### 3.3 LLM Export Enhancement

**Location:** `tools/export.py`

Include image descriptions in the XML export format used for RAG context:

```xml
<post id="123456789">
  <author>@analyst</author>
  <content>Great chart showing the market dynamics...</content>
  <media>
    <image>
      <url>https://...</url>
      <description>S&P 500 chart showing...</description>
    </image>
  </media>
  <tags>markets, analysis</tags>
</post>
```

### 3.4 Schema Update

**Location:** `schemas/post.schema.json`

```json
{
  "media": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "type": {"type": "string", "enum": ["image", "photo", "video", "gif", "link"]},
        "url": {"type": "string", "format": "uri"},
        "category": {"type": "string", "enum": ["text_heavy", "chart", "general"]},
        "description": {"type": "string"},
        "extracted_at": {"type": "string", "format": "date-time"},
        "extraction_model": {"type": "string"}
      },
      "required": ["type", "url"]
    }
  }
}
```

The `category` field enables:
- Appropriate prompt selection during extraction
- Filtering searches by image type (e.g., "find all chart posts")
- Different display treatments in the frontend

---

## Part 4: Implementation Plan

### Phase 1: Vision Extraction Service

**Goal:** Create the core service for extracting image descriptions

#### 1.1 Create Vision Extractor Module

```
src/vision/
├── __init__.py
├── extractor.py      # Claude Vision API wrapper
└── prompts.py        # Extraction prompts
```

#### 1.2 Implement Extractor

```python
# src/vision/extractor.py

import anthropic
import httpx
import base64
from typing import Optional

class ImageContentExtractor:
    """Extract semantic content from images using Claude Vision."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model_id = "claude-3-5-sonnet-20241022"

    async def describe_image(
        self,
        image_url: str,
        post_context: Optional[str] = None
    ) -> str:
        """
        Generate a rich description of an image.

        Args:
            image_url: URL of the image to describe
            post_context: The text of the post containing this image (for context)

        Returns:
            Detailed text description of the image content
        """
        # Fetch and encode image
        image_data = await self._fetch_image(image_url)

        # Build prompt with context
        prompt = self._build_prompt(post_context)

        # Call Claude Vision
        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_data["media_type"],
                            "data": image_data["data"]
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )

        return response.content[0].text

    async def _fetch_image(self, url: str) -> dict:
        """Fetch image and return base64 encoded data."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "image/jpeg")
            media_type = content_type.split(";")[0]

            return {
                "media_type": media_type,
                "data": base64.standard_b64encode(response.content).decode("utf-8")
            }

    def _build_prompt(self, post_context: Optional[str], image_category: Optional[str] = None) -> str:
        """Build the extraction prompt based on image category."""
        from .prompts import get_extraction_prompt

        prompt = get_extraction_prompt(image_category)
        if post_context:
            return f"{prompt}\n\nContext from the post: {post_context}"
        return prompt

    async def describe_image(
        self,
        image_url: str,
        post_context: Optional[str] = None,
        image_category: Optional[str] = None  # "text_heavy", "chart", "general"
    ) -> dict:
        """
        Generate a rich description of an image.

        Args:
            image_url: URL of the image to describe
            post_context: The text of the post containing this image
            image_category: Hint for extraction strategy. If None, auto-detects.

        Returns:
            Dict with 'description', 'category', and 'transcription' (if applicable)
        """
        image_data = await self._fetch_image(image_url)

        # Auto-detect category if not provided
        if image_category is None:
            image_category = await self._detect_image_category(image_data, post_context)

        prompt = self._build_prompt(post_context, image_category)

        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=2048,  # Increased for verbatim transcription
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_data["media_type"],
                            "data": image_data["data"]
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }]
        )

        return {
            "description": response.content[0].text,
            "category": image_category
        }

    async def _detect_image_category(self, image_data: dict, post_context: Optional[str]) -> str:
        """Use a quick vision call to classify the image type."""
        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_data["media_type"],
                            "data": image_data["data"]
                        }
                    },
                    {
                        "type": "text",
                        "text": "Classify this image into ONE category: 'text_heavy' (screenshots, notes, documents with significant text), 'chart' (graphs, data visualizations, diagrams), or 'general' (photos, memes, other). Reply with only the category name."
                    }
                ]
            }]
        )
        category = response.content[0].text.strip().lower()
        if category not in ["text_heavy", "chart", "general"]:
            category = "general"
        return category
```

#### 1.3 Extraction Prompts (Category-Specific)

The extraction strategy varies based on image type:

| Category | Strategy | Output Focus |
|----------|----------|--------------|
| `text_heavy` | Verbatim transcription | Complete text content, preserving structure |
| `chart` | Data extraction + interpretation | Numbers, trends, annotations, insights |
| `general` | Semantic description | What's shown, context, relevance |

```python
# src/vision/prompts.py

def get_extraction_prompt(category: Optional[str] = None) -> str:
    """Return the appropriate extraction prompt for the image category."""
    if category == "text_heavy":
        return TEXT_HEAVY_PROMPT
    elif category == "chart":
        return CHART_PROMPT
    else:
        return GENERAL_PROMPT


TEXT_HEAVY_PROMPT = """This image contains significant text content (screenshot, document, notes, etc.).

Your task is to perform COMPLETE TEXT EXTRACTION. Transcribe ALL visible text verbatim.

Requirements:
1. **Full transcription**: Capture every word, number, and symbol visible
2. **Preserve structure**: Maintain paragraph breaks, bullet points, headers, and formatting
3. **Include annotations**: Handwritten notes, highlights, underlines, comments
4. **Note context**: UI elements, timestamps, source indicators, watermarks

Format your response as:
---
[TRANSCRIPTION]
(Complete text content here, preserving structure)

[CONTEXT]
(Brief note on what type of document/screenshot this is and any relevant visual context)
---

Do NOT summarize. Capture the complete text content."""


CHART_PROMPT = """This image contains a chart, graph, or data visualization.

Extract both the DATA and the MEANING from this visualization.

Include:
1. **Chart type**: Line, bar, candlestick, pie, scatter, etc.
2. **Axes and scales**: What's being measured, units, ranges
3. **Key data points**: Important numbers, peaks, troughs, intersections
4. **Trends**: Patterns, directions, correlations visible
5. **Annotations**: Any text labels, callouts, or notes on the chart
6. **Source/metadata**: Attribution, timestamps, data source if shown

Example format:
"Candlestick chart of BTC/USD from Jan-Mar 2024. Y-axis: $38,000-$72,000. Key movements: (1) Jan 10 ETF approval spike from $46K to $49K, (2) Consolidation $41-43K through late Jan, (3) Breakout above $50K on Feb 12, (4) ATH $72,000 on Mar 14. Volume bars show heavy buying on breakout days. Annotation reads: 'Halving anticipation rally'. Source: TradingView."

Be specific with numbers and dates when visible."""


GENERAL_PROMPT = """Describe this image in detail for a knowledge base system. Your description will be used for semantic search and RAG retrieval.

Include:
1. **What's shown**: People, objects, scenes, actions
2. **Any text**: Signs, captions, overlaid text, memes
3. **Context**: What this image represents or communicates
4. **Relevance**: Why someone might have saved this (insight, humor, reference)

Be factual and descriptive. Aim for 2-4 sentences that capture what a human would take away from seeing this image."""
```

### Phase 2: Bot Integration

**Goal:** Extract image descriptions when archiving new posts

#### 2.1 Add to Archive Flow

Modify `save_archived_post()` to call the vision extractor before saving.

#### 2.2 Configuration

```python
# Environment variable to control extraction
ENABLE_IMAGE_EXTRACTION = os.getenv("ENABLE_IMAGE_EXTRACTION", "true").lower() == "true"

# Cost control: max images per post
MAX_IMAGES_TO_EXTRACT = int(os.getenv("MAX_IMAGES_TO_EXTRACT", "4"))
```

#### 2.3 Error Handling

- Image extraction failures should NOT block post archiving
- Log failures for later manual review or retry
- Store posts with partial extraction (some images described, others not)

### Phase 3: Backfill Existing Posts

**Goal:** Extract descriptions for already-archived posts that have images

#### 3.1 Create Backfill Script

```python
# scripts/backfill_image_descriptions.py

"""
Backfill image descriptions for existing posts.

Usage:
    python scripts/backfill_image_descriptions.py [--dry-run] [--limit N]
"""

import asyncio
from pathlib import Path
from tools.utils import parse_post_file, POSTS_DIR
from src.vision.extractor import ImageContentExtractor

async def backfill():
    extractor = ImageContentExtractor()
    posts_needing_extraction = []

    # Find posts with images but no descriptions
    for post_file in POSTS_DIR.rglob("*.md"):
        post = parse_post_file(post_file)
        if post.get("media"):
            for media_item in post["media"]:
                if media_item.get("type") in ["photo", "image"]:
                    if not media_item.get("description"):
                        posts_needing_extraction.append(post_file)
                        break

    print(f"Found {len(posts_needing_extraction)} posts needing image extraction")

    # Process with rate limiting
    for post_file in posts_needing_extraction:
        await process_post(post_file, extractor)
        await asyncio.sleep(1)  # Rate limit: 1 post per second
```

#### 3.2 Backfill Priorities

1. **Most recent posts first** - URLs most likely to still be valid
2. **High-importance posts** - `importance: 5` posts get priority
3. **Posts with single images** - Lower cost, quick wins
4. **Batch processing** - Run during off-peak hours

#### 3.3 URL Validation

Before extracting, validate the image URL is still accessible:

```python
async def validate_image_url(url: str) -> bool:
    """Check if image URL is still accessible."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.head(url, follow_redirects=True)
            return response.status_code == 200
    except:
        return False
```

### Phase 4: Embedding Re-indexing

**Goal:** Update embeddings to include image descriptions

After backfilling descriptions, run the embedding migration to regenerate vectors:

```bash
# Re-run migration for posts with new descriptions
python scripts/migrate_embeddings.py --force
```

The existing migration script already reads from post files - it will automatically include the new `description` fields in the embedding text once we update the embedding text construction.

---

## Part 5: Cost Analysis

### Per-Image Cost

Using Claude 3.5 Sonnet for vision (two calls per image):

| Call | Input | Output | Purpose |
|------|-------|--------|---------|
| Classification | ~1,000-2,000 tokens (image) + 50 (prompt) | ~10 tokens | Detect image category |
| Extraction | ~1,000-2,000 tokens (image) + 200-400 (prompt) | ~100-500 tokens | Full extraction |

| Factor | Value |
|--------|-------|
| Classification call | ~$0.003 |
| Extraction call | ~$0.005-$0.012 |
| **Total per image** | **~$0.008-$0.015** |

**Note:** For text-heavy images, output tokens may be higher (~500-1000) due to verbatim transcription, increasing cost to ~$0.02/image in those cases.

### Projected Costs

| Scenario | Images | Cost |
|----------|--------|------|
| Backfill existing archive | ~50 posts × 1.5 images avg | ~$0.75-$1.50 |
| Monthly new posts | ~30 posts × 1.5 images avg | ~$0.50-$0.90/month |
| Annual ongoing | ~360 posts × 1.5 images avg | ~$6-$11/year |

**Conclusion:** Costs are minimal - roughly a coffee per year.

### Cost Optimization Options

If classification overhead is a concern:
- **Skip classification for known types**: If post text contains "chart", "graph", assume `chart` category
- **Batch classification**: Classify multiple images in one call (if they're from the same post)
- **Cache classification**: Similar images from same author may have consistent types

### Cost Controls

1. **Skip duplicates:** Don't re-extract if description exists
2. **Image size limits:** Skip very large images (>5MB) or resize
3. **Batch during off-peak:** Lower priority for batch backfill
4. **Manual override:** Allow skipping extraction for specific posts

---

## Part 6: Quality Assurance

### Extraction Quality Checks

1. **Minimum length:** Descriptions under 50 characters may indicate extraction failure
2. **Hallucination detection:** Cross-reference numbers/dates with post text
3. **Manual spot-checks:** Review sample of extractions weekly initially

### Monitoring

```python
# Track extraction metrics
extraction_metrics = {
    "total_extracted": 0,
    "failed": 0,
    "avg_description_length": 0,
    "model_version": "claude-3-5-sonnet-20241022"
}
```

### Fallback Behavior

If extraction fails:
1. Log the failure with image URL and error
2. Save post without description (don't block archiving)
3. Queue for retry in next backfill run
4. After 3 failures, mark as "manual review needed"

---

## Part 7: Future Enhancements

### 7.1 Multi-Modal Embeddings

Instead of text descriptions, use image embedding models:

```
Image → CLIP/SigLIP → Image embedding → Combined with text embedding
```

**Status:** Deferred. Text descriptions are simpler and work well with our current text-based RAG.

### 7.2 Video Frame Extraction

For video content, extract key frames and describe:

```
Video → Extract frames at intervals → Describe each frame → Concatenate descriptions
```

**Status:** Deferred. Videos are rare in the archive and high-value content is usually in charts/images.

### 7.3 OCR Enhancement

For screenshots with text, use dedicated OCR before vision:

```
Screenshot → OCR (extract raw text) → Vision (extract context) → Combined description
```

**Status:** Deferred. Claude Vision handles text well already.

### 7.4 Image Archival

After extraction, optionally store images locally:

```
Image → Download → Store in /archive/media/{post_id}/ → Update URL to local path
```

**Status:** Deferred per ROADMAP.md decision. Descriptions preserve semantic value even if URLs die.

---

## Part 8: Dependencies

### New Python Dependencies

```
# requirements.txt additions
anthropic>=0.18.0    # Already planned for RAG (Phase 6)
httpx>=0.25.0        # Async HTTP client for image fetching
```

### API Requirements

- **Anthropic API key** with vision capabilities enabled
- Same key used for future RAG integration

---

## Part 9: File Structure

```
src/
├── vision/
│   ├── __init__.py
│   ├── extractor.py      # Claude Vision API wrapper
│   └── prompts.py        # Extraction prompts
├── embeddings/           # (existing)
│   ├── service.py        # Update embedding text construction
│   └── vector_store.py
└── ...

scripts/
├── migrate_embeddings.py         # (existing)
├── backfill_image_descriptions.py # New: backfill existing posts
└── ...

tools/
├── telegram_bot.py       # Update save_archived_post()
├── export.py             # Update LLM export format
└── ...
```

---

## Part 10: Implementation Order

```
Phase 1: Vision Extraction Service
    └── Create src/vision/ module
    └── Implement ImageContentExtractor class
    └── Write extraction prompts
    └── Add httpx dependency
    └── Test with sample images

Phase 2: Bot Integration
    └── Add extraction call to save_archived_post()
    └── Add configuration (enable/disable, max images)
    └── Handle errors gracefully
    └── Test end-to-end with real posts

Phase 3: Embedding Enhancement
    └── Update embedding text construction to include descriptions
    └── Update export.py to include descriptions in LLM format
    └── Verify RAG context includes image content

Phase 4: Backfill Existing Posts
    └── Create backfill_image_descriptions.py script
    └── Run on existing archive (prioritize recent posts)
    └── Re-run embedding migration

Phase 5: Monitoring & Refinement
    └── Add extraction metrics logging
    └── Monitor description quality
    └── Tune prompts based on results
```

---

## Summary

| Aspect | Decision |
|--------|----------|
| **Extraction model** | Claude 3.5 Sonnet Vision |
| **When to extract** | At archive time (new posts) + backfill (existing) |
| **Storage** | `media[].description` field in post frontmatter |
| **Embedding integration** | Include descriptions in embedding text |
| **RAG integration** | Include in LLM export context |
| **Cost** | ~$0.01/image, <$10/year projected |
| **Failure handling** | Non-blocking, queue for retry |

---

## References

- [Anthropic Vision Documentation](https://docs.anthropic.com/en/docs/build-with-claude/vision)
- [Claude 3.5 Sonnet Capabilities](https://www.anthropic.com/claude/sonnet)
- Related: `docs/SEMANTIC_SEARCH_DESIGN.md` (embedding integration)
- Related: `docs/ROADMAP.md` (project priorities)
