# Thesis System Design

> **Status**: Proposed
> **Created**: 2024-12-28
> **Purpose**: Transform the archive from a post collection into a thesis-building knowledge system

## Overview

The Thesis System introduces **thesis-based knowledge management** to the X-Bookmark Knowledge Repository. Instead of just saving posts, the system helps build and refine evolving understanding ("theses") about topics you care about.

**Core concept**: When you save a post about SK Hynix's HBM yield advantage, it doesn't just get tagged—it actively contributes to your thesis on "HBM Memory Leadership" and expands your entity knowledge about SK Hynix.

### Key Benefits

1. **Active synthesis** - Posts don't just accumulate; they build understanding
2. **Automatic organization** - Claude detects entities and relevant theses
3. **Human steering** - Override AI decisions to keep knowledge accurate
4. **Thesis evolution** - Watch your understanding grow over time
5. **Multi-dimensional access** - Browse by entity, thesis, category, or recent

---

## Conceptual Model

### Three-Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                        ENTITY CATEGORIES                        │
│         (Umbrella groups: Amino Acids, Memory Companies)        │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                           ENTITIES                              │
│              (Nouns: Glycine, SK Hynix, Vitamin D)              │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│           POSTS              │  │          THESES              │
│    (Individual data points)  │  │  (Evolving understanding)    │
└──────────────────────────────┘  └──────────────────────────────┘
```

### Relationships

| Relationship | Cardinality | Example |
|--------------|-------------|---------|
| Category → Entity | One-to-many | "Amino Acids" contains Glycine, Taurine, L-Theanine |
| Entity → Post | Many-to-many | SK Hynix mentioned in multiple posts |
| Entity → Thesis | Many-to-many | SK Hynix contributes to "HBM Leadership" and "AI Infrastructure" |
| Post → Thesis | Many-to-many | One post can support multiple theses |
| Thesis → Thesis | Many-to-many | "Vitamin D" thesis relates to "Vitamin K2" thesis |

### Example Knowledge Graph

```
Category: Memory Companies
├── Entity: SK Hynix
│   ├── Post: "SK Hynix 73% yield on HBM3E"
│   ├── Post: "SK Hynix NVIDIA partnership extended"
│   └── Contributes to:
│       ├── Thesis: "HBM Memory Leadership"
│       └── Thesis: "AI Infrastructure Bottlenecks"
│
├── Entity: Samsung
│   ├── Post: "Samsung HBM3E struggles continue"
│   └── Contributes to:
│       └── Thesis: "HBM Memory Leadership"

Category: Amino Acids
├── Entity: Glycine
│   ├── Post: "Glycine 3g before bed improves sleep"
│   ├── Post: "Glycine + Magnesium synergy study"
│   └── Contributes to:
│       ├── Thesis: "Sleep Optimization"
│       └── Thesis: "Collagen Synthesis"
```

---

## Data Model

### Database Schema (Supabase/PostgreSQL)

```sql
-- ============================================
-- ENTITY CATEGORIES
-- ============================================
CREATE TABLE entity_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,              -- "Amino Acids", "Memory Companies"
    description TEXT,                        -- Brief description of this category
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- ENTITIES
-- ============================================
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,                      -- "Glycine", "SK Hynix"
    category_id UUID REFERENCES entity_categories(id) ON DELETE SET NULL,
    description TEXT,                        -- AI-generated or manual summary
    aliases TEXT[] DEFAULT '{}',             -- ["GLY", "glycin", "2-aminoacetic acid"]
    metadata JSONB DEFAULT '{}',             -- Flexible structured data
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(name, category_id)                -- Same name OK in different categories
);

-- Embedding for entity matching
ALTER TABLE entities ADD COLUMN embedding VECTOR(384);
CREATE INDEX entities_embedding_idx ON entities
    USING ivfflat (embedding vector_cosine_ops);

-- ============================================
-- THESES
-- ============================================
CREATE TABLE theses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,               -- "HBM Memory Leadership", "Sleep Optimization"
    category TEXT,                           -- "investing", "health", "tech", "general"
    description TEXT,                        -- What this thesis is about
    current_synthesis TEXT,                  -- AI-generated evolving understanding
    synthesis_updated_at TIMESTAMPTZ,
    synthesis_post_count INTEGER DEFAULT 0,  -- Posts included in last synthesis
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Embedding for thesis matching
ALTER TABLE theses ADD COLUMN embedding VECTOR(384);
CREATE INDEX theses_embedding_idx ON theses
    USING ivfflat (embedding vector_cosine_ops);

-- ============================================
-- JUNCTION TABLES
-- ============================================

-- Posts ↔ Entities (many-to-many)
CREATE TABLE post_entities (
    post_id TEXT REFERENCES posts(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 1.0,            -- AI confidence (0.0-1.0)
    manually_verified BOOLEAN DEFAULT FALSE, -- User confirmed this link
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (post_id, entity_id)
);

-- Posts ↔ Theses (many-to-many, with contribution)
CREATE TABLE post_theses (
    post_id TEXT REFERENCES posts(id) ON DELETE CASCADE,
    thesis_id UUID REFERENCES theses(id) ON DELETE CASCADE,
    contribution TEXT,                       -- "How this post adds to the thesis"
    confidence FLOAT DEFAULT 1.0,
    manually_verified BOOLEAN DEFAULT FALSE,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (post_id, thesis_id)
);

-- Entities ↔ Theses (many-to-many)
CREATE TABLE entity_theses (
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    thesis_id UUID REFERENCES theses(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'subject',             -- "primary_subject", "supporting", "comparison"
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (entity_id, thesis_id)
);

-- Thesis ↔ Thesis relationships (for cross-thesis connections)
CREATE TABLE thesis_relationships (
    thesis_a_id UUID REFERENCES theses(id) ON DELETE CASCADE,
    thesis_b_id UUID REFERENCES theses(id) ON DELETE CASCADE,
    relationship_type TEXT,                  -- "supports", "contradicts", "extends", "related"
    description TEXT,                        -- "Vitamin D absorption requires K2"
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (thesis_a_id, thesis_b_id),
    CHECK (thesis_a_id < thesis_b_id)        -- Prevent duplicates (A,B) and (B,A)
);

-- ============================================
-- CORRECTIONS (for learning from steering)
-- ============================================
CREATE TABLE corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id TEXT REFERENCES posts(id) ON DELETE CASCADE,
    correction_type TEXT NOT NULL,           -- "entity_added", "entity_removed", "thesis_changed", etc.
    original_value JSONB,                    -- What AI suggested
    corrected_value JSONB,                   -- What user changed it to
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX post_entities_post_idx ON post_entities(post_id);
CREATE INDEX post_entities_entity_idx ON post_entities(entity_id);
CREATE INDEX post_theses_post_idx ON post_theses(post_id);
CREATE INDEX post_theses_thesis_idx ON post_theses(thesis_id);
CREATE INDEX entity_theses_entity_idx ON entity_theses(entity_id);
CREATE INDEX entity_theses_thesis_idx ON entity_theses(thesis_id);
CREATE INDEX entities_category_idx ON entities(category_id);
CREATE INDEX theses_category_idx ON theses(category);
```

---

## Claude API Integration

### Integration Points

| Point | Trigger | Purpose | Estimated Cost |
|-------|---------|---------|----------------|
| Post Analysis | On post save | Detect entities + theses | ~$0.005/post |
| Contribution Generation | On thesis link | Explain how post adds to thesis | ~$0.003/link |
| Synthesis Regeneration | Threshold or on-demand | Update thesis understanding | ~$0.01/thesis |
| Entity Description | On new entity | Generate entity summary | ~$0.002/entity |

### 1. Post Analysis Prompt

```python
POST_ANALYSIS_PROMPT = """Analyze this archived post for knowledge graph integration.

## POST CONTENT
{post_content}

## POST METADATA
Author: {author}
Tags: {tags}
Topics: {topics}
User notes: {notes}

## EXISTING ENTITIES (match these first before creating new)
{existing_entities_json}

## EXISTING THESES (match these first before creating new)
{existing_theses_json}

## EXISTING ENTITY CATEGORIES
{existing_categories_json}

## INSTRUCTIONS
1. Identify all entities mentioned (companies, people, substances, technologies, etc.)
2. Match to existing entities when possible (check aliases)
3. Identify which theses this post supports or adds to
4. For new entities/theses, suggest appropriate categorization

Return valid JSON:
{{
    "entities": [
        {{
            "name": "SK Hynix",
            "existing_id": "uuid-if-matched" or null,
            "category": "Memory Companies",
            "category_id": "uuid-if-matched" or null,
            "is_new": false,
            "confidence": 0.95,
            "context": "mentioned as HBM3E manufacturer"
        }}
    ],
    "theses": [
        {{
            "name": "HBM Memory Leadership",
            "existing_id": "uuid-if-matched" or null,
            "is_new": false,
            "confidence": 0.90,
            "contribution_summary": "Provides yield data (73%) supporting SK Hynix's manufacturing advantage over competitors"
        }}
    ],
    "suggested_new_category": null or {{
        "name": "...",
        "description": "..."
    }},
    "cross_thesis_relationships": [
        {{
            "thesis_a": "HBM Memory Leadership",
            "thesis_b": "AI Infrastructure Bottlenecks",
            "relationship": "supports",
            "reason": "HBM supply constraints affect AI chip availability"
        }}
    ]
}}
"""
```

### 2. Synthesis Regeneration Prompt

```python
SYNTHESIS_PROMPT = """You are maintaining a knowledge synthesis for the thesis: "{thesis_name}"

## THESIS DESCRIPTION
{thesis_description}

## CATEGORY
{thesis_category}

## CONTRIBUTING ENTITIES
{entities_list}

## ALL CONTRIBUTING POSTS (chronological)
{posts_formatted}

## PREVIOUS SYNTHESIS (if any)
{previous_synthesis}

## INSTRUCTIONS
Write an updated synthesis (3-5 paragraphs) that:

1. **Current Understanding**: Summarize the key insights and conclusions
2. **Supporting Evidence**: Reference specific posts/data points that support the thesis
3. **Recent Developments**: Highlight what's new since the last synthesis (if applicable)
4. **Open Questions**: Note any tensions, gaps, or areas needing more information
5. **Connections**: Mention relationships to other theses if relevant

Write in first person plural ("Our thesis...", "We've observed...") as this represents
the user's evolving understanding. Be specific and cite sources. Avoid generic statements.

Format with markdown headers for readability.
"""
```

### 3. Implementation Code

```python
# src/knowledge_graph/analyzer.py

from anthropic import Anthropic
from typing import Optional
import json

class PostAnalyzer:
    def __init__(self, db, anthropic_client: Anthropic):
        self.db = db
        self.client = anthropic_client
        self.model = "claude-sonnet-4-20250514"  # Cost-effective for analysis

    async def analyze_post(self, post: dict) -> dict:
        """Analyze a post for entities and theses."""

        # Fetch existing data for matching
        existing_entities = await self.db.get_all_entities_with_aliases()
        existing_theses = await self.db.get_all_theses()
        existing_categories = await self.db.get_all_entity_categories()

        prompt = POST_ANALYSIS_PROMPT.format(
            post_content=post["content"],
            author=post.get("author", {}).get("handle", "unknown"),
            tags=", ".join(post.get("tags", [])),
            topics=", ".join(post.get("topics", [])),
            notes=post.get("notes", ""),
            existing_entities_json=json.dumps(existing_entities, indent=2),
            existing_theses_json=json.dumps(existing_theses, indent=2),
            existing_categories_json=json.dumps(existing_categories, indent=2)
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        result = json.loads(response.content[0].text)
        return result

    async def process_analysis_results(self, post_id: str, analysis: dict) -> dict:
        """Create/link entities and theses based on analysis."""

        created = {"entities": [], "theses": [], "categories": []}

        # Handle new category if suggested
        if analysis.get("suggested_new_category"):
            cat = analysis["suggested_new_category"]
            category_id = await self.db.create_entity_category(
                name=cat["name"],
                description=cat["description"]
            )
            created["categories"].append(cat["name"])

        # Process entities
        for entity in analysis["entities"]:
            if entity["is_new"]:
                # Create new entity
                entity_id = await self.db.create_entity(
                    name=entity["name"],
                    category_name=entity["category"],
                    description=entity.get("context")
                )
                created["entities"].append(entity["name"])
            else:
                entity_id = entity["existing_id"]

            # Link post to entity
            await self.db.link_post_entity(
                post_id=post_id,
                entity_id=entity_id,
                confidence=entity["confidence"]
            )

        # Process theses
        for thesis in analysis["theses"]:
            if thesis["is_new"]:
                # Create new thesis
                thesis_id = await self.db.create_thesis(
                    name=thesis["name"],
                    category=self._infer_thesis_category(analysis)
                )
                created["theses"].append(thesis["name"])
            else:
                thesis_id = thesis["existing_id"]

            # Link post to thesis with contribution
            await self.db.link_post_thesis(
                post_id=post_id,
                thesis_id=thesis_id,
                contribution=thesis["contribution_summary"],
                confidence=thesis["confidence"]
            )

            # Check if synthesis regeneration needed
            await self._check_synthesis_trigger(thesis_id)

        # Process cross-thesis relationships
        for rel in analysis.get("cross_thesis_relationships", []):
            await self.db.create_thesis_relationship(
                thesis_a_name=rel["thesis_a"],
                thesis_b_name=rel["thesis_b"],
                relationship_type=rel["relationship"],
                description=rel["reason"]
            )

        return created


class SynthesisEngine:
    """Manages thesis synthesis regeneration."""

    THRESHOLD_POSTS = 3          # Regenerate after N new posts
    MIN_HOURS_BETWEEN = 24       # Minimum hours between auto-regenerations
    ON_DEMAND_COOLDOWN = 1       # Hours between on-demand regenerations

    def __init__(self, db, anthropic_client: Anthropic):
        self.db = db
        self.client = anthropic_client
        self.model = "claude-sonnet-4-20250514"

    async def should_auto_regenerate(self, thesis_id: str) -> bool:
        """Check if thesis needs automatic regeneration."""

        thesis = await self.db.get_thesis(thesis_id)

        if not thesis.get("synthesis_updated_at"):
            # Never synthesized - check if we have enough posts
            post_count = await self.db.count_thesis_posts(thesis_id)
            return post_count >= 1  # Generate initial synthesis with first post

        posts_since = await self.db.count_posts_since(
            thesis_id,
            thesis["synthesis_updated_at"]
        )

        hours_since = self._hours_since(thesis["synthesis_updated_at"])

        return (
            posts_since >= self.THRESHOLD_POSTS and
            hours_since >= self.MIN_HOURS_BETWEEN
        )

    async def regenerate_synthesis(self, thesis_id: str, force: bool = False) -> str:
        """Regenerate thesis synthesis."""

        thesis = await self.db.get_thesis(thesis_id)

        # Check cooldown for on-demand (unless force)
        if not force and thesis.get("synthesis_updated_at"):
            hours_since = self._hours_since(thesis["synthesis_updated_at"])
            if hours_since < self.ON_DEMAND_COOLDOWN:
                raise CooldownError(
                    f"Synthesis updated recently. Try again in {self.ON_DEMAND_COOLDOWN - hours_since:.0f} hours."
                )

        # Fetch all contributing posts
        posts = await self.db.get_thesis_posts(thesis_id)
        entities = await self.db.get_thesis_entities(thesis_id)

        # Format posts for prompt
        posts_formatted = self._format_posts_for_synthesis(posts)
        entities_list = ", ".join([e["name"] for e in entities])

        prompt = SYNTHESIS_PROMPT.format(
            thesis_name=thesis["name"],
            thesis_description=thesis.get("description", "No description"),
            thesis_category=thesis.get("category", "general"),
            entities_list=entities_list,
            posts_formatted=posts_formatted,
            previous_synthesis=thesis.get("current_synthesis", "None - this is the initial synthesis")
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        new_synthesis = response.content[0].text

        # Update thesis
        await self.db.update_thesis_synthesis(
            thesis_id=thesis_id,
            synthesis=new_synthesis,
            post_count=len(posts)
        )

        return new_synthesis

    def _format_posts_for_synthesis(self, posts: list) -> str:
        """Format posts for inclusion in synthesis prompt."""

        formatted = []
        for i, post in enumerate(posts, 1):
            contribution = post.get("contribution", "No contribution summary")
            formatted.append(f"""
### Post {i} ({post['archived_at'][:10]})
**Author**: @{post['author']['handle']}
**Content**: {post['content'][:500]}{'...' if len(post['content']) > 500 else ''}
**Contribution**: {contribution}
---""")

        return "\n".join(formatted)
```

---

## User Flows

### Flow 1: Post Save (with Knowledge Graph Integration)

```
┌─────────────────────────────────────────────────────────────────┐
│                     POST SAVE FLOW                              │
└─────────────────────────────────────────────────────────────────┘

User shares X post to Telegram
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Bot fetches post content via FxTwitter API                      │
│ Bot prompts for tags, topics, notes, importance (existing flow) │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ NEW: Claude API analyzes post                                   │
│ - Detects entities (matches existing or suggests new)           │
│ - Detects relevant theses (matches existing or suggests new)    │
│ - Generates contribution summaries                              │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Bot presents analysis to user:                                  │
│                                                                 │
│ 📊 Knowledge Graph Analysis:                                    │
│                                                                 │
│ Entities detected:                                              │
│   • SK Hynix (Memory Companies) ✓                               │
│   • HBM3E (Technologies) [NEW]                                  │
│                                                                 │
│ Contributes to theses:                                          │
│   • HBM Memory Leadership                                       │
│     "Provides yield data supporting SK Hynix's lead"            │
│   • AI Infrastructure Bottlenecks                               │
│     "Highlights supply constraints in AI hardware"              │
│                                                                 │
│ [✅ Accept] [✏️ Edit] [⏭️ Skip]                                  │
└─────────────────────────────────────────────────────────────────┘
            │
            ├── User accepts ──────────────────────────────────┐
            │                                                  │
            ├── User edits ───┐                                │
            │                 │                                │
            │                 ▼                                │
            │   ┌─────────────────────────────────────────┐    │
            │   │ Edit interface:                         │    │
            │   │ - Add/remove entities                   │    │
            │   │ - Change entity categories              │    │
            │   │ - Add/remove thesis links               │    │
            │   │ - Edit contribution summaries           │    │
            │   │ - Create new thesis                     │    │
            │   └─────────────────────────────────────────┘    │
            │                 │                                │
            │                 ▼                                │
            │   ┌─────────────────────────────────────────┐    │
            │   │ Store correction for learning           │    │
            │   └─────────────────────────────────────────┘    │
            │                 │                                │
            └─────────────────┴────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Save to database:                                               │
│ - Post record                                                   │
│ - Post embedding                                                │
│ - Entity links                                                  │
│ - Thesis links with contributions                               │
│ - Create new entities/theses if needed                          │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Check synthesis triggers for each linked thesis:                │
│                                                                 │
│ if posts_since_synthesis >= 3 AND hours_since >= 24:            │
│     queue_synthesis_regeneration(thesis_id)                     │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
         ✅ Done
```

### Flow 2: Thesis Synthesis Regeneration

```
┌─────────────────────────────────────────────────────────────────┐
│               SYNTHESIS REGENERATION FLOW                       │
└─────────────────────────────────────────────────────────────────┘

Trigger: Auto (threshold reached) OR Manual (user clicks regenerate)
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Fetch thesis data:                                              │
│ - Thesis name, description, category                            │
│ - All contributing entities                                     │
│ - All contributing posts (with contribution summaries)          │
│ - Previous synthesis (if any)                                   │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Call Claude API with synthesis prompt                           │
│ - Include all posts (or smart summarization for large theses)   │
│ - Reference previous synthesis for continuity                   │
│ - Generate 3-5 paragraph synthesis                              │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Update thesis record:                                           │
│ - current_synthesis = new synthesis                             │
│ - synthesis_updated_at = now()                                  │
│ - synthesis_post_count = count of posts included                │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
         ✅ Done
```

### Flow 3: Human Steering (Correction)

```
┌─────────────────────────────────────────────────────────────────┐
│                    STEERING/CORRECTION FLOW                     │
└─────────────────────────────────────────────────────────────────┘

User viewing post detail page
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Post shows detected entities and thesis links:                  │
│                                                                 │
│ 📄 Post about glycine and sleep                                 │
│                                                                 │
│ Entities: [Glycine] [Magnesium]                                 │
│ Theses: [Sleep Optimization]                                    │
│                                                                 │
│ [✏️ Edit Knowledge Links]                                       │
└─────────────────────────────────────────────────────────────────┘
            │
            │ User clicks Edit
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Edit Modal:                                                     │
│                                                                 │
│ ENTITIES                                                        │
│ [Glycine ✓] [Magnesium ✓] [+ Add entity]                        │
│                                                                 │
│ Glycine category: [Amino Acids ▼]                               │
│                                                                 │
│ THESES                                                          │
│ [Sleep Optimization ✓] [+ Add thesis]                           │
│                                                                 │
│ Contribution to "Sleep Optimization":                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ "Shows glycine + magnesium synergy for sleep quality..."    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ [💾 Save Changes] [Cancel]                                      │
└─────────────────────────────────────────────────────────────────┘
            │
            │ User saves changes
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Compare original vs corrected:                                  │
│ - Record what changed in corrections table                      │
│ - Update entity/thesis links                                    │
│ - Mark links as manually_verified = true                        │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Future enhancement (v2):                                        │
│ - Use corrections as few-shot examples in analysis prompt       │
│ - "Previously, you classified X as Y but user corrected to Z"   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Synthesis Configuration

```python
# src/knowledge_graph/config.py

SYNTHESIS_CONFIG = {
    # Auto-regeneration settings
    "threshold_posts": 3,           # Regenerate after N new posts
    "min_hours_between_auto": 24,   # Minimum hours between auto-regenerations

    # On-demand settings
    "on_demand_cooldown_hours": 1,  # Cooldown between manual regenerations

    # Large thesis handling
    "max_posts_full_context": 50,   # Include full content up to this many posts
    "summarization_threshold": 50,  # Above this, use summarization strategy

    # Cost controls
    "max_daily_synthesis_calls": 20,  # Prevent runaway costs
    "max_monthly_analysis_calls": 500,
}

ANALYSIS_CONFIG = {
    # Entity detection
    "min_entity_confidence": 0.6,   # Below this, don't auto-link
    "suggest_threshold": 0.4,       # Below min but above this, suggest to user

    # Thesis detection
    "min_thesis_confidence": 0.5,
    "max_new_theses_per_post": 2,   # Limit new thesis creation

    # Model selection
    "analysis_model": "claude-sonnet-4-20250514",      # Cost-effective
    "synthesis_model": "claude-sonnet-4-20250514",     # Same for consistency
}
```

---

## Web UI Requirements

### New Pages

| Route | Purpose | Key Features |
|-------|---------|--------------|
| `/recent` | Recent saves | Chronological feed, entity/thesis badges, quick filters |
| `/entities` | Entity browser | Grouped by category, search, post counts |
| `/entities/[id]` | Entity detail | All posts, contributing theses, entity facts |
| `/theses` | Thesis browser | By category, synthesis previews, post counts |
| `/theses/[id]` | Thesis detail | Full synthesis, all posts, entities, relationships |
| `/posts/[id]` | Post detail | Content, entities, thesis contributions, edit links |
| `/explore` | Knowledge graph | Visual graph of entities, theses, relationships |

### Page Wireframes

#### `/theses/[id]` - Thesis Detail Page

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Back to Theses                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HBM Memory Leadership                              [investing] │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                 │
│  12 posts · 3 entities · Updated 2 days ago                     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CURRENT SYNTHESIS                        [🔄 Regenerate]       │
│  ─────────────────────────────────────────────────────────────  │
│  3 new posts since last update                                  │
│                                                                 │
│  ## Current Understanding                                       │
│                                                                 │
│  Our thesis on HBM memory leadership centers on SK Hynix's      │
│  dominant position in the high-bandwidth memory market. The     │
│  company maintains a significant manufacturing advantage,       │
│  achieving 73% yields on HBM3E production compared to           │
│  Samsung's estimated 40% yields...                              │
│                                                                 │
│  ## Supporting Evidence                                         │
│                                                                 │
│  - SK Hynix yield data from Q3 2024 earnings call              │
│  - NVIDIA partnership extension announcement (Dec 2024)         │
│  - Samsung restructuring of memory division...                  │
│                                                                 │
│  ## Open Questions                                              │
│                                                                 │
│  - Can Samsung close the yield gap with new Pyeongtaek fab?    │
│  - Impact of China restrictions on competitive dynamics...      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ENTITIES                                                       │
│  ─────────────────────────────────────────────────────────────  │
│  [SK Hynix] [Samsung] [Micron]                                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RELATED THESES                                                 │
│  ─────────────────────────────────────────────────────────────  │
│  → AI Infrastructure Bottlenecks (supports)                     │
│  → Memory Cycle Dynamics (related)                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CONTRIBUTING POSTS                                             │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ @semaborlmbs · Dec 15, 2024                               │  │
│  │ SK Hynix reportedly achieving 73% yields on HBM3E...      │  │
│  │                                                           │  │
│  │ 💡 Contribution: "Provides yield data (73%) supporting    │  │
│  │    SK Hynix's manufacturing advantage over competitors"   │  │
│  │                                                [View →]   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ @chipmoneysemi · Dec 12, 2024                             │  │
│  │ NVIDIA extends HBM supply agreement with SK Hynix...      │  │
│  │                                                           │  │
│  │ 💡 Contribution: "Demonstrates customer lock-in and       │  │
│  │    validates SK Hynix's technology leadership"            │  │
│  │                                                [View →]   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  [Load more posts...]                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### `/entities/[id]` - Entity Detail Page

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Back to Entities                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SK Hynix                                    [Memory Companies] │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                 │
│  8 posts · 2 theses                                             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CONTRIBUTES TO THESES                                          │
│  ─────────────────────────────────────────────────────────────  │
│  → HBM Memory Leadership (primary subject, 6 posts)             │
│  → AI Infrastructure Bottlenecks (supporting, 3 posts)          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ALL POSTS MENTIONING SK HYNIX                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  [Post cards with dates, previews, thesis badges...]            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Migration Path

### Phase 1: Database Setup (with Supabase migration)

When migrating to Supabase (already planned), add thesis system tables:

```sql
-- Run after core posts table is set up
-- See "Database Schema" section above for full SQL
```

### Phase 2: Backfill Existing Posts

```python
# scripts/backfill_knowledge_graph.py

async def backfill_existing_posts():
    """Analyze all existing posts and populate knowledge graph."""

    posts = await db.get_all_posts()
    analyzer = PostAnalyzer(db, anthropic_client)

    for post in posts:
        print(f"Analyzing: {post['id'][:20]}...")

        try:
            analysis = await analyzer.analyze_post(post)
            await analyzer.process_analysis_results(post["id"], analysis)

            # Rate limit to avoid API throttling
            await asyncio.sleep(1)

        except Exception as e:
            print(f"  Error: {e}")
            continue

    print(f"Backfill complete. Analyzed {len(posts)} posts.")
```

### Phase 3: Telegram Bot Integration

Update `tools/telegram_bot.py`:

1. After user provides tags/topics/notes, call analyzer
2. Present analysis results with accept/edit/skip options
3. Handle edit flow (add/remove entities, change categories, etc.)
4. Save with knowledge graph links

### Phase 4: Web UI

Build thesis/entity pages as part of Next.js frontend work.

### Phase 5: Synthesis Engine

Enable auto-regeneration and on-demand regeneration.

---

## Cost Projections

### Per-Post Costs

| Operation | Tokens (est.) | Cost (Sonnet) |
|-----------|---------------|---------------|
| Post analysis | ~2K in, ~500 out | ~$0.005 |
| Contribution generation | Included above | - |
| Entity embedding | 384 dims | ~$0.0001 |
| Thesis embedding | 384 dims | ~$0.0001 |

**Total per post**: ~$0.005

### Monthly Projections

| Usage Level | Posts/Month | Analysis | Synthesis (est.) | Total |
|-------------|-------------|----------|------------------|-------|
| Light | 50 | $0.25 | $0.20 | ~$0.50 |
| Moderate | 150 | $0.75 | $0.50 | ~$1.25 |
| Heavy | 300 | $1.50 | $1.00 | ~$2.50 |

### Cost Controls

```python
# Implemented in analyzer
- Daily cap on synthesis regenerations (default: 20)
- Monthly cap on analysis calls (default: 500)
- Warning at 80% of caps
- Graceful degradation (skip analysis, save post without KG links)
```

---

## Success Criteria

- [ ] Entities and theses auto-detected for new posts
- [ ] User can accept/edit/skip knowledge graph suggestions
- [ ] Thesis synthesis regenerates after 3 new posts (or on-demand)
- [ ] Entity pages show all related posts
- [ ] Thesis pages show synthesis + contributing posts
- [ ] Corrections stored for future learning
- [ ] Existing posts backfilled into knowledge graph
- [ ] Cost stays within projections

---

## Open Questions

1. **Synthesis history**: Should we store previous synthesis versions? (Useful for tracking evolution, adds storage)

2. **Entity merging**: What happens when user realizes two entities are the same? (e.g., "Vitamin D3" and "Cholecalciferol")

3. **Thesis archival**: Can theses be "closed" or archived when no longer relevant?

4. **Collaborative potential**: Future multi-user? Shared theses?

---

## Appendix: Example Thesis Synthesis

**Thesis**: Sleep Optimization
**Category**: Health
**Entities**: Glycine, Magnesium, L-Theanine, Melatonin

### Current Synthesis

#### Current Understanding

Our sleep optimization thesis centers on a stack-based approach combining multiple compounds with complementary mechanisms. The core insight is that sleep quality improves more from addressing multiple pathways (GABA, body temperature, circadian rhythm) than from optimizing any single compound.

Glycine emerges as a foundational element, with research showing 3g before bed reduces core body temperature and improves subjective sleep quality. The temperature mechanism is distinct from GABAergic compounds, suggesting additive benefits.

#### Supporting Evidence

- Glycine 3g study showing temperature reduction and sleep quality improvement (Post from @hubaborelman, Nov 2024)
- Magnesium glycinate absorption data suggesting superior bioavailability (Post from @examine, Oct 2024)
- L-Theanine + Magnesium combination study in anxiety-related insomnia (Post from @sleepdiplomat, Dec 2024)

#### Recent Developments

The most recent addition highlights potential negative interactions between high-dose melatonin (>1mg) and natural melatonin production. This shifts our thesis toward lower melatonin doses (0.3-0.5mg) or eliminating it in favor of the glycine + magnesium + theanine stack.

#### Open Questions

- Optimal timing for glycine relative to sleep onset (current data suggests 30-60 min)
- Whether magnesium form (glycinate vs threonate) meaningfully impacts sleep outcomes
- Long-term adaptation effects of nightly L-theanine use

---

*Last updated: 2024-12-28 (8 posts)*
