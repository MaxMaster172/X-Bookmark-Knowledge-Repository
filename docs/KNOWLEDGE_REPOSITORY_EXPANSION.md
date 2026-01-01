# Knowledge Repository Expansion: Notes, Backlinks & Deep Research

**Status**: DRAFT - Pending Approval
**Created**: 2026-01-01
**Supersedes**: Extends ARCHITECTURE.md Phase 7+

---

## Executive Summary

Transform X-Bookmark Knowledge Repository from a "Twitter bookmark archive" into a **Relational Knowledge Repository** - a personal knowledge graph where:

1. **Multiple content types** feed the system (X posts, notes, research outputs)
2. **Backlinks** create bidirectional connections between documents
3. **Synthesis** (theses) becomes first-class searchable content
4. **Perplexity Deep Research** extends knowledge when gaps exist

**Priority Order**:
1. Notes + Backlinks (Phase 10)
2. Perplexity Integration (Phase 11)
3. Knowledge Graph Visualization (Phase 12)

---

## Table of Contents

1. [Vision & Goals](#1-vision--goals)
2. [Data Model Changes](#2-data-model-changes)
3. [Backlink System](#3-backlink-system)
4. [Note Editor](#4-note-editor)
5. [Perplexity Integration](#5-perplexity-integration)
6. [Knowledge Graph UI](#6-knowledge-graph-ui)
7. [Migration Strategy](#7-migration-strategy)
8. [Updated Roadmap](#8-updated-roadmap)
9. [Technical Specifications](#9-technical-specifications)
10. [Cost Analysis](#10-cost-analysis)

---

## 1. Vision & Goals

### Current State
- Archive X/Twitter bookmarks with semantic search
- Thesis system designed but not fully implemented
- RAG chat in progress (Phase 5)
- Content is consumption-only (no creation)

### Target State
```
┌─────────────────────────────────────────────────────────────────┐
│                  RELATIONAL KNOWLEDGE REPOSITORY                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   INPUTS                      CORE                    OUTPUTS   │
│   ───────                     ────                    ───────   │
│   • X Posts (existing)    ┌─────────────┐                       │
│   • Manual Notes (new)───►│  Documents  │───► Semantic Search   │
│   • Markdown Import (new) │  + Links    │───► RAG Chat          │
│   • Perplexity Research ─►│  + Entities │───► Knowledge Graph   │
│   • Thesis Synthesis ────►│  + Theses   │───► Thesis Synthesis  │
│                           └─────────────┘                       │
│                                 │                               │
│                                 ▼                               │
│                          [[Backlinks]]                          │
│                     Bidirectional connections                   │
│                     between all content types                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Success Criteria
- [ ] Can create notes in Notion-like editor with slash commands
- [ ] `[[backlinks]]` automatically create bidirectional connections
- [ ] All content types (posts, notes, research) searchable in unified RAG
- [ ] Perplexity research saves as documents, extends knowledge base
- [ ] Knowledge graph visualization shows connections
- [ ] Theses auto-index and become referenceable via backlinks

---

## 2. Data Model Changes

### 2.1 Current Schema (Simplified)

```sql
-- Current: X-post centric
posts (
  id TEXT PRIMARY KEY,        -- X post ID
  url TEXT,
  content TEXT,
  author_handle TEXT,
  author_name TEXT,
  posted_at TIMESTAMPTZ,
  archived_at TIMESTAMPTZ,
  tags TEXT[],
  topics TEXT[],
  notes TEXT,
  importance TEXT,
  embedding VECTOR(384),
  is_thread BOOLEAN,
  thread_position INTEGER,
  quoted_post_id TEXT,
  quoted_text TEXT
)
```

### 2.2 New Schema: Unified Documents

```sql
-- New: Type-discriminated documents
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Type discrimination
  type TEXT NOT NULL CHECK (type IN (
    'x_post',      -- Migrated from posts table
    'note',        -- User-created notes
    'research',    -- Perplexity deep research outputs
    'thesis',      -- Auto-generated thesis documents
    'import'       -- Imported markdown files
  )),

  -- Common fields (all types)
  title TEXT,                           -- NULL for x_posts, required for notes
  content TEXT NOT NULL,                -- Markdown content
  embedding VECTOR(384),                -- Semantic vector
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Categorization (all types)
  tags TEXT[] DEFAULT '{}',
  topics TEXT[] DEFAULT '{}',
  importance TEXT DEFAULT 'medium',

  -- Source tracking
  source_url TEXT,                      -- Original URL (X posts, web imports)
  source_type TEXT,                     -- 'x.com', 'perplexity', 'manual', 'import'

  -- Type-specific metadata (JSONB for flexibility)
  metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_embedding ON documents
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_documents_tags ON documents USING GIN(tags);
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);
```

### 2.3 Type-Specific Metadata

```typescript
// TypeScript interfaces for metadata field

interface XPostMetadata {
  author_handle: string;
  author_name: string;
  posted_at: string;          // ISO timestamp
  is_thread: boolean;
  thread_position?: number;
  quoted_post_id?: string;
  quoted_text?: string;
  original_id: string;        // Original X post ID (for deduplication)
}

interface NoteMetadata {
  created_via: 'web' | 'import' | 'api';
  word_count: number;
  reading_time_minutes: number;
}

interface ResearchMetadata {
  query: string;                        // Original question
  perplexity_model: string;             // 'sonar-deep-research'
  reasoning_effort: 'low' | 'medium' | 'high';
  citations: Citation[];
  research_duration_seconds: number;
  triggered_by: 'manual' | 'rag_suggestion';
}

interface Citation {
  url: string;
  title: string;
  snippet: string;
}

interface ThesisMetadata {
  synthesis_version: number;
  contributing_documents: string[];     // UUIDs of source documents
  confidence: number;                   // 0-1 synthesis confidence
  last_synthesis_at: string;
}

interface ImportMetadata {
  original_filename: string;
  imported_at: string;
  source_app?: string;                  // 'obsidian', 'notion', 'manual'
}
```

### 2.4 Document Links (Backlinks)

```sql
CREATE TABLE document_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Link endpoints
  source_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  target_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

  -- Link metadata
  link_type TEXT DEFAULT 'references' CHECK (link_type IN (
    'references',    -- Generic reference [[Page]]
    'extends',       -- This document extends/builds on target
    'contradicts',   -- This document contradicts target
    'supports',      -- This document provides evidence for target
    'quotes'         -- Direct quote from target
  )),

  -- Context (where in the source doc the link appears)
  context TEXT,                         -- Surrounding text snippet
  position_start INTEGER,               -- Character offset
  position_end INTEGER,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  created_by TEXT DEFAULT 'system',     -- 'system' (auto-parsed) or 'user' (manual)

  UNIQUE(source_id, target_id, link_type)
);

-- Indexes for bidirectional queries
CREATE INDEX idx_links_source ON document_links(source_id);
CREATE INDEX idx_links_target ON document_links(target_id);
```

### 2.5 Updated Junction Tables

```sql
-- Rename post_* to document_*
ALTER TABLE post_entities RENAME TO document_entities;
ALTER TABLE document_entities RENAME COLUMN post_id TO document_id;

ALTER TABLE post_theses RENAME TO document_theses;
ALTER TABLE document_theses RENAME COLUMN post_id TO document_id;

ALTER TABLE post_media RENAME TO document_media;
ALTER TABLE document_media RENAME COLUMN post_id TO document_id;
```

---

## 3. Backlink System

### 3.1 Syntax: `[[Page Title]]`

**Format**: `[[Document Title]]` or `[[Document Title|Display Text]]`

```markdown
# My Research Note

This builds on the ideas in [[HBM Memory Leadership]].

The data from [[SK Hynix Q3 Analysis|recent SK Hynix analysis]] supports this.

See also: [[Sleep Optimization Thesis]]
```

### 3.2 Parsing & Resolution

```typescript
// Backlink extraction regex
const BACKLINK_REGEX = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;

interface ParsedBacklink {
  fullMatch: string;           // "[[Page Title|Display]]"
  targetTitle: string;         // "Page Title"
  displayText: string | null;  // "Display" or null
  startIndex: number;
  endIndex: number;
}

function extractBacklinks(markdown: string): ParsedBacklink[] {
  const links: ParsedBacklink[] = [];
  let match;

  while ((match = BACKLINK_REGEX.exec(markdown)) !== null) {
    links.push({
      fullMatch: match[0],
      targetTitle: match[1].trim(),
      displayText: match[2]?.trim() || null,
      startIndex: match.index,
      endIndex: match.index + match[0].length
    });
  }

  return links;
}
```

### 3.3 Resolution Strategy

```typescript
async function resolveBacklink(title: string): Promise<UUID | null> {
  // 1. Exact title match (case-insensitive)
  let doc = await db.documents
    .select('id')
    .ilike('title', title)
    .single();

  if (doc) return doc.id;

  // 2. Fuzzy match (for typos)
  doc = await db.rpc('fuzzy_match_document', {
    search_title: title,
    threshold: 0.8
  });

  if (doc) return doc.id;

  // 3. Create placeholder (optional - user preference)
  // return await createPlaceholderDocument(title);

  return null; // Unresolved link
}
```

### 3.4 Link Synchronization

On document save:
1. Parse content for `[[backlinks]]`
2. Resolve each to document ID
3. Diff against existing links in `document_links`
4. Create new links, remove stale links
5. Update `context` field with surrounding text

```typescript
async function syncBacklinks(documentId: UUID, content: string) {
  const parsed = extractBacklinks(content);
  const existingLinks = await getOutgoingLinks(documentId);

  // Resolve all targets
  const resolvedLinks = await Promise.all(
    parsed.map(async (link) => ({
      ...link,
      targetId: await resolveBacklink(link.targetTitle)
    }))
  );

  // Filter to successfully resolved
  const validLinks = resolvedLinks.filter(l => l.targetId);

  // Compute diff
  const toCreate = validLinks.filter(
    l => !existingLinks.some(e => e.target_id === l.targetId)
  );
  const toRemove = existingLinks.filter(
    e => !validLinks.some(l => l.targetId === e.target_id)
  );

  // Apply changes
  await db.document_links.insert(toCreate.map(l => ({
    source_id: documentId,
    target_id: l.targetId,
    link_type: 'references',
    context: extractContext(content, l.startIndex, 100),
    position_start: l.startIndex,
    position_end: l.endIndex
  })));

  await db.document_links
    .delete()
    .in('id', toRemove.map(l => l.id));
}
```

### 3.5 Backlink UI Components

```
┌─────────────────────────────────────────────────┐
│ Document: HBM Memory Leadership                 │
├─────────────────────────────────────────────────┤
│                                                 │
│ [Document content...]                           │
│                                                 │
├─────────────────────────────────────────────────┤
│ 📎 Backlinks (3)                               │
├─────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐ │
│ │ 📝 My Research Note                         │ │
│ │ "...builds on the ideas in [[HBM Memory..." │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ 🐦 Tweet about SK Hynix                     │ │
│ │ "...related to [[HBM Memory Leadership]]..." │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ 🔬 Deep Research: Memory Market             │ │
│ │ "...thesis [[HBM Memory Leadership]] is..." │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 4. Note Editor

### 4.1 Technology: Novel.sh

**Novel** is an open-source Notion-style WYSIWYG editor built on:
- **Tiptap** (ProseMirror-based editor framework)
- **Tailwind CSS** (matches our styling)
- **TypeScript** (type-safe)

**Features**:
- Slash commands (`/heading`, `/bullet`, `/code`, `/quote`)
- Markdown shortcuts (`#`, `**`, `- `, etc.)
- AI autocomplete hooks (we can wire Claude)
- Link suggestions for `[[backlinks]]`
- ~5KB gzipped

**Repository**: https://github.com/steven-tey/novel

### 4.2 Installation

```bash
cd web
npm install novel
```

### 4.3 Custom Extensions

```typescript
// extensions/backlink.ts
import { Mark, mergeAttributes } from '@tiptap/core';
import { Plugin, PluginKey } from 'prosemirror-state';
import Suggestion from '@tiptap/suggestion';

export const Backlink = Mark.create({
  name: 'backlink',

  addOptions() {
    return {
      suggestion: {
        char: '[[',
        command: ({ editor, range, props }) => {
          editor
            .chain()
            .focus()
            .deleteRange(range)
            .insertContent(`[[${props.title}]]`)
            .run();
        },
      },
    };
  },

  parseHTML() {
    return [{ tag: 'span[data-backlink]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return ['span', mergeAttributes(HTMLAttributes, {
      'data-backlink': '',
      'class': 'backlink text-blue-600 hover:underline cursor-pointer'
    })];
  },

  addProseMirrorPlugins() {
    return [
      Suggestion({
        editor: this.editor,
        ...this.options.suggestion,
      }),
    ];
  },
});
```

### 4.4 Slash Commands Configuration

```typescript
const slashCommands = [
  {
    title: 'Heading 1',
    command: '/h1',
    icon: 'Heading1',
    action: (editor) => editor.chain().focus().setHeading({ level: 1 }).run(),
  },
  {
    title: 'Heading 2',
    command: '/h2',
    icon: 'Heading2',
    action: (editor) => editor.chain().focus().setHeading({ level: 2 }).run(),
  },
  {
    title: 'Bullet List',
    command: '/bullet',
    icon: 'List',
    action: (editor) => editor.chain().focus().toggleBulletList().run(),
  },
  {
    title: 'Numbered List',
    command: '/number',
    icon: 'ListOrdered',
    action: (editor) => editor.chain().focus().toggleOrderedList().run(),
  },
  {
    title: 'Code Block',
    command: '/code',
    icon: 'Code',
    action: (editor) => editor.chain().focus().setCodeBlock().run(),
  },
  {
    title: 'Quote',
    command: '/quote',
    icon: 'Quote',
    action: (editor) => editor.chain().focus().setBlockquote().run(),
  },
  {
    title: 'Divider',
    command: '/divider',
    icon: 'Minus',
    action: (editor) => editor.chain().focus().setHorizontalRule().run(),
  },
  // AI-powered (future)
  {
    title: 'AI Continue',
    command: '/ai',
    icon: 'Sparkles',
    action: (editor) => triggerAICompletion(editor),
  },
];
```

### 4.5 Page Structure

```
/notes              - Note list/grid view
/notes/new          - Create new note (editor)
/notes/[id]         - View note (read mode)
/notes/[id]/edit    - Edit note (editor mode)
```

### 4.6 Editor Component

```typescript
// components/editor/NoteEditor.tsx
'use client';

import { Editor } from 'novel';
import { useState, useCallback } from 'react';
import { Backlink } from './extensions/backlink';
import { BacklinkSuggestions } from './BacklinkSuggestions';

interface NoteEditorProps {
  initialContent?: string;
  onSave: (content: string, title: string) => Promise<void>;
}

export function NoteEditor({ initialContent, onSave }: NoteEditorProps) {
  const [title, setTitle] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = useCallback(async (content: string) => {
    setIsSaving(true);
    try {
      await onSave(content, title);
    } finally {
      setIsSaving(false);
    }
  }, [title, onSave]);

  return (
    <div className="max-w-3xl mx-auto">
      {/* Title input */}
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Untitled"
        className="w-full text-4xl font-bold border-none outline-none mb-4
                   bg-transparent placeholder:text-muted-foreground"
      />

      {/* Novel editor */}
      <Editor
        defaultValue={initialContent}
        extensions={[Backlink]}
        onUpdate={({ editor }) => {
          // Auto-save on change (debounced)
          handleSave(editor.storage.markdown.getMarkdown());
        }}
        className="prose dark:prose-invert max-w-none"
      />

      {/* Save indicator */}
      {isSaving && (
        <div className="fixed bottom-4 right-4 text-sm text-muted-foreground">
          Saving...
        </div>
      )}
    </div>
  );
}
```

---

## 5. Perplexity Integration

### 5.1 API Overview

**Endpoint**: `https://api.perplexity.ai/chat/completions`
**Model**: `sonar-deep-research` (async)
**Pricing**: ~$0.40 per deep research query

### 5.2 Integration Flow

```
┌────────────────────────────────────────────────────────────────┐
│                    PERPLEXITY INTEGRATION                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  TRIGGER PATHS                                                 │
│  ─────────────                                                 │
│                                                                │
│  1. Manual Trigger                                             │
│     User clicks "Deep Research" button                         │
│     → Opens research modal with query input                    │
│     → Submits to /api/research                                 │
│                                                                │
│  2. RAG Suggestion                                             │
│     User asks question in chat                                 │
│     → Claude finds insufficient context                        │
│     → Responds: "I don't have enough info. Research this?"     │
│     → User confirms → triggers /api/research                   │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  PROCESSING FLOW                                               │
│  ───────────────                                               │
│                                                                │
│  /api/research (POST)                                          │
│       │                                                        │
│       ▼                                                        │
│  ┌─────────────────────┐                                       │
│  │ 1. Start async job  │                                       │
│  │    POST /async/...  │                                       │
│  └──────────┬──────────┘                                       │
│             │ Returns job_id                                   │
│             ▼                                                  │
│  ┌─────────────────────┐                                       │
│  │ 2. Poll for result  │ ◄─── 10s intervals                   │
│  │    GET /async/...   │      2-4 min typical                  │
│  └──────────┬──────────┘                                       │
│             │ Returns research + citations                     │
│             ▼                                                  │
│  ┌─────────────────────┐                                       │
│  │ 3. Save as document │                                       │
│  │    type: 'research' │                                       │
│  │    + generate embed │                                       │
│  └──────────┬──────────┘                                       │
│             │                                                  │
│             ▼                                                  │
│  ┌─────────────────────┐                                       │
│  │ 4. Return to user   │                                       │
│  │    + show in UI     │                                       │
│  └─────────────────────┘                                       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 5.3 API Route Implementation

```typescript
// app/api/research/route.ts
import { createClient } from '@/lib/supabase/server';
import { generateEmbedding } from '@/lib/embeddings/server';

const PERPLEXITY_API = 'https://api.perplexity.ai';

export async function POST(request: Request) {
  const { query, reasoningEffort = 'medium' } = await request.json();

  // 1. Start async deep research
  const startResponse = await fetch(`${PERPLEXITY_API}/async/chat/completions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.PERPLEXITY_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'sonar-deep-research',
      messages: [{ role: 'user', content: query }],
      reasoning_effort: reasoningEffort,
    }),
  });

  const { id: jobId } = await startResponse.json();

  // 2. Poll for completion (with timeout)
  const result = await pollForResult(jobId, 300000); // 5 min timeout

  // 3. Extract content and citations
  const content = result.choices[0].message.content;
  const citations = result.citations || [];

  // 4. Generate embedding
  const embedding = await generateEmbedding(content);

  // 5. Save as document
  const supabase = createClient();
  const { data: document } = await supabase
    .from('documents')
    .insert({
      type: 'research',
      title: `Research: ${query.slice(0, 100)}`,
      content: formatResearchContent(content, citations),
      embedding,
      source_type: 'perplexity',
      metadata: {
        query,
        perplexity_model: 'sonar-deep-research',
        reasoning_effort: reasoningEffort,
        citations,
        research_duration_seconds: result.usage?.total_time || 0,
        triggered_by: 'manual',
      },
    })
    .select()
    .single();

  return Response.json({ document, citations });
}

async function pollForResult(jobId: string, timeout: number) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const response = await fetch(
      `${PERPLEXITY_API}/async/chat/completions/${jobId}`,
      {
        headers: {
          'Authorization': `Bearer ${process.env.PERPLEXITY_API_KEY}`,
        },
      }
    );

    const result = await response.json();

    if (result.status === 'completed') {
      return result;
    }

    if (result.status === 'failed') {
      throw new Error(`Research failed: ${result.error}`);
    }

    // Wait 10 seconds before next poll
    await new Promise(resolve => setTimeout(resolve, 10000));
  }

  throw new Error('Research timed out');
}

function formatResearchContent(content: string, citations: Citation[]): string {
  let formatted = content;

  // Add citations section
  if (citations.length > 0) {
    formatted += '\n\n---\n\n## Sources\n\n';
    citations.forEach((citation, i) => {
      formatted += `${i + 1}. [${citation.title}](${citation.url})\n`;
    });
  }

  return formatted;
}
```

### 5.4 RAG Integration

```typescript
// In chat API route
async function handleChatMessage(message: string, context: Document[]) {
  // Check if we have enough context
  const relevantDocs = context.filter(d => d.similarity > 0.7);

  if (relevantDocs.length < 2) {
    // Suggest deep research
    return {
      response: `I don't have enough information in your knowledge base to answer this well.
                 Would you like me to run a deep research query on "${message}"?`,
      suggestResearch: true,
      suggestedQuery: message,
    };
  }

  // Normal RAG response
  return generateRAGResponse(message, relevantDocs);
}
```

### 5.5 UI Components

```typescript
// components/research/ResearchButton.tsx
export function ResearchButton({ defaultQuery }: { defaultQuery?: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState(defaultQuery || '');
  const [isResearching, setIsResearching] = useState(false);
  const [progress, setProgress] = useState<string>('');

  const handleResearch = async () => {
    setIsResearching(true);
    setProgress('Starting deep research...');

    try {
      const response = await fetch('/api/research', {
        method: 'POST',
        body: JSON.stringify({ query }),
      });

      const { document } = await response.json();

      // Navigate to the new research document
      router.push(`/doc/${document.id}`);
    } catch (error) {
      toast.error('Research failed. Please try again.');
    } finally {
      setIsResearching(false);
    }
  };

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>
        <Search className="w-4 h-4 mr-2" />
        Deep Research
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Deep Research</DialogTitle>
            <DialogDescription>
              Run comprehensive research using Perplexity AI.
              Results will be saved to your knowledge base.
            </DialogDescription>
          </DialogHeader>

          <Textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What would you like to research?"
            rows={3}
          />

          {isResearching && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              {progress}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleResearch} disabled={isResearching || !query}>
              {isResearching ? 'Researching...' : 'Start Research (~$0.40)'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
```

---

## 6. Knowledge Graph UI

### 6.1 Visualization Library

**Recommended**: **React Flow** or **vis.js**

React Flow pros:
- React-native, fits our stack
- Highly customizable nodes/edges
- Built-in pan/zoom
- Good performance with 1000+ nodes

### 6.2 Graph Data Structure

```typescript
interface GraphNode {
  id: string;
  type: 'x_post' | 'note' | 'research' | 'thesis' | 'entity';
  label: string;
  data: {
    documentId?: string;
    entityId?: string;
    preview?: string;
  };
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: 'references' | 'extends' | 'supports' | 'contradicts' | 'tagged';
  label?: string;
}

async function buildKnowledgeGraph(centerId?: string): Promise<{
  nodes: GraphNode[];
  edges: GraphEdge[];
}> {
  // Fetch documents with their links
  const { data: documents } = await supabase
    .from('documents')
    .select(`
      id, type, title, content,
      outgoing_links:document_links!source_id(target_id, link_type),
      incoming_links:document_links!target_id(source_id, link_type),
      entities:document_entities(entity:entities(id, name, type))
    `)
    .limit(100);

  // Transform to graph format
  const nodes = documents.map(d => ({
    id: d.id,
    type: d.type,
    label: d.title || d.content.slice(0, 50) + '...',
    data: { documentId: d.id, preview: d.content.slice(0, 200) }
  }));

  const edges = documents.flatMap(d => [
    ...d.outgoing_links.map(l => ({
      id: `${d.id}-${l.target_id}`,
      source: d.id,
      target: l.target_id,
      type: l.link_type
    })),
  ]);

  return { nodes, edges };
}
```

### 6.3 Graph Page

```typescript
// app/graph/page.tsx
'use client';

import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState
} from 'reactflow';
import 'reactflow/dist/style.css';

export default function KnowledgeGraphPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    loadGraph();
  }, []);

  async function loadGraph() {
    const { nodes, edges } = await buildKnowledgeGraph();
    setNodes(nodes.map(n => ({
      ...n,
      position: calculatePosition(n), // Force-directed layout
    })));
    setEdges(edges);
  }

  return (
    <div className="w-full h-screen">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={customNodeTypes}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
```

---

## 7. Migration Strategy

### 7.1 Phase 1: Schema Migration

```sql
-- Step 1: Create new documents table
CREATE TABLE documents (...); -- As defined above

-- Step 2: Migrate posts to documents
INSERT INTO documents (
  id,
  type,
  title,
  content,
  embedding,
  created_at,
  updated_at,
  tags,
  topics,
  importance,
  source_url,
  source_type,
  metadata
)
SELECT
  gen_random_uuid(),
  'x_post',
  NULL,  -- X posts don't have titles
  content,
  embedding,
  archived_at,
  archived_at,
  tags,
  topics,
  importance,
  url,
  'x.com',
  jsonb_build_object(
    'author_handle', author_handle,
    'author_name', author_name,
    'posted_at', posted_at,
    'is_thread', is_thread,
    'thread_position', thread_position,
    'quoted_post_id', quoted_post_id,
    'quoted_text', quoted_text,
    'original_id', id
  )
FROM posts;

-- Step 3: Create ID mapping table (for foreign key updates)
CREATE TABLE _migration_post_to_document (
  old_post_id TEXT PRIMARY KEY,
  new_document_id UUID
);

INSERT INTO _migration_post_to_document
SELECT p.id, d.id
FROM posts p
JOIN documents d ON d.metadata->>'original_id' = p.id;

-- Step 4: Update junction tables
UPDATE post_entities SET post_id = (
  SELECT new_document_id FROM _migration_post_to_document
  WHERE old_post_id = post_id
);
-- Rename after
ALTER TABLE post_entities RENAME TO document_entities;
ALTER TABLE document_entities RENAME COLUMN post_id TO document_id;

-- Repeat for post_theses, post_media

-- Step 5: Create document_links table
CREATE TABLE document_links (...);

-- Step 6: Drop old tables (after verification)
-- DROP TABLE posts;
-- DROP TABLE _migration_post_to_document;
```

### 7.2 Phase 2: Code Updates

| Component | Changes Required |
|-----------|------------------|
| `src/supabase/client.py` | Update to use `documents` table, handle types |
| `tools/telegram_bot.py` | Insert as `type: 'x_post'` with metadata |
| `web/lib/queries/posts.ts` | Rename to `documents.ts`, update queries |
| `web/app/post/[id]/page.tsx` | Rename to `/doc/[id]`, handle all types |
| `web/components/PostCard.tsx` | Rename to `DocumentCard.tsx`, type-aware rendering |

### 7.3 Backward Compatibility

During migration:
- Create database view `posts_view` that maps documents back to old schema
- Gradually update code to use new schema
- Remove view after full migration

```sql
CREATE VIEW posts_view AS
SELECT
  metadata->>'original_id' as id,
  source_url as url,
  content,
  metadata->>'author_handle' as author_handle,
  metadata->>'author_name' as author_name,
  (metadata->>'posted_at')::timestamptz as posted_at,
  created_at as archived_at,
  tags,
  topics,
  notes,  -- Need to handle this
  importance,
  embedding,
  (metadata->>'is_thread')::boolean as is_thread,
  (metadata->>'thread_position')::integer as thread_position,
  metadata->>'quoted_post_id' as quoted_post_id,
  metadata->>'quoted_text' as quoted_text
FROM documents
WHERE type = 'x_post';
```

---

## 8. Updated Roadmap

### Current Phases (Unchanged)

| Phase | Status | Description |
|-------|--------|-------------|
| 1: Supabase Setup | ✅ | PostgreSQL + pgvector |
| 2: Telegram Bot | ✅ | Writes to Supabase |
| 3: Image Extraction | ✅ | Claude Vision |
| 4: Next.js App | ✅ | MVP with semantic search |
| 5: RAG Chat | ⏳ | Claude chat interface |
| 6: Vercel Deploy | ⏳ | Production deployment |
| 7: Thesis System | ⏳ | Entity/thesis detection |
| 8: Research Sessions | ⏳ | Save conversations |
| 9: Cleanup | ⏳ | Remove old code |

### New Phases (This Document)

| Phase | Description | Dependencies |
|-------|-------------|--------------|
| **10: Notes & Backlinks** | Unified document model, Novel editor, backlink parsing | Phase 5 (RAG needed for context) |
| **11: Perplexity Integration** | Deep research API, RAG suggestions, auto-save | Phase 10 (needs document model) |
| **12: Knowledge Graph** | React Flow visualization, entity connections | Phase 10, 11 |

### Phase 10 Breakdown: Notes & Backlinks

```
Phase 10A: Data Model Migration (2-3 sessions)
├── Create documents table
├── Migrate posts → documents
├── Update junction tables
├── Create document_links table
└── Update Python backend (supabase/client.py, telegram_bot.py)

Phase 10B: Note Editor (2-3 sessions)
├── Install Novel.sh
├── Create backlink extension
├── Build /notes pages (list, new, edit)
├── Implement auto-save
└── Add backlink suggestions UI

Phase 10C: Backlink System (1-2 sessions)
├── Implement backlink parser
├── Build resolution logic
├── Create sync function (on save)
├── Add backlinks UI panel
└── Update search to include notes

Phase 10D: Markdown Import (1 session)
├── File upload UI
├── Parse frontmatter
├── Extract backlinks
├── Batch import support
```

### Phase 11 Breakdown: Perplexity Integration

```
Phase 11A: API Integration (1-2 sessions)
├── Create /api/research route
├── Implement async polling
├── Save results as documents
└── Add error handling

Phase 11B: UI Integration (1-2 sessions)
├── Research button component
├── Progress indicator
├── Results display
└── Link to saved document

Phase 11C: RAG Integration (1 session)
├── Detect insufficient context
├── Suggest research in chat
├── One-click research trigger
└── Auto-cite in responses
```

---

## 9. Technical Specifications

### 9.1 Environment Variables (New)

```env
# Perplexity API
PERPLEXITY_API_KEY=pplx-...

# Feature flags
ENABLE_DEEP_RESEARCH=true
ENABLE_NOTE_EDITOR=true
```

### 9.2 Database Indexes

```sql
-- Full-text search on documents
CREATE INDEX idx_documents_content_fts ON documents
  USING GIN (to_tsvector('english', content));

-- Fast type filtering
CREATE INDEX idx_documents_type ON documents(type);

-- Backlink queries
CREATE INDEX idx_links_source ON document_links(source_id);
CREATE INDEX idx_links_target ON document_links(target_id);

-- Title lookup for backlink resolution
CREATE INDEX idx_documents_title_lower ON documents(lower(title));
```

### 9.3 RPC Functions

```sql
-- Updated search to handle all document types
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding VECTOR(384),
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 10,
  filter_types TEXT[] DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  type TEXT,
  title TEXT,
  content TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.type,
    d.title,
    d.content,
    1 - (d.embedding <=> query_embedding) as similarity
  FROM documents d
  WHERE
    1 - (d.embedding <=> query_embedding) > match_threshold
    AND (filter_types IS NULL OR d.type = ANY(filter_types))
  ORDER BY d.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Fuzzy title matching for backlinks
CREATE OR REPLACE FUNCTION fuzzy_match_document(
  search_title TEXT,
  threshold FLOAT DEFAULT 0.8
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
  result_id UUID;
BEGIN
  SELECT id INTO result_id
  FROM documents
  WHERE similarity(lower(title), lower(search_title)) > threshold
  ORDER BY similarity(lower(title), lower(search_title)) DESC
  LIMIT 1;

  RETURN result_id;
END;
$$;
```

### 9.4 TypeScript Types

```typescript
// types/document.ts
export type DocumentType = 'x_post' | 'note' | 'research' | 'thesis' | 'import';

export interface Document {
  id: string;
  type: DocumentType;
  title: string | null;
  content: string;
  embedding: number[] | null;
  created_at: string;
  updated_at: string;
  tags: string[];
  topics: string[];
  importance: 'low' | 'medium' | 'high' | 'critical';
  source_url: string | null;
  source_type: string | null;
  metadata: Record<string, unknown>;
}

export interface DocumentLink {
  id: string;
  source_id: string;
  target_id: string;
  link_type: 'references' | 'extends' | 'contradicts' | 'supports' | 'quotes';
  context: string | null;
  position_start: number | null;
  position_end: number | null;
  created_at: string;
  created_by: string;
}

export interface DocumentWithRelations extends Document {
  outgoing_links: DocumentLink[];
  incoming_links: DocumentLink[];
  entities: Entity[];
  theses: Thesis[];
  media: DocumentMedia[];
}
```

---

## 10. Cost Analysis

### 10.1 Current Costs

| Service | Monthly Cost |
|---------|--------------|
| Supabase (Free tier) | $0 |
| Vercel (Hobby) | $0 |
| Hetzner VPS | ~$5-10 |
| Claude API (vision + chat) | ~$5-20 |
| **Total** | ~$10-30 |

### 10.2 Additional Costs (This Expansion)

| Feature | Cost Driver | Estimated Monthly |
|---------|-------------|-------------------|
| Perplexity Deep Research | $0.40/query | $4-20 (10-50 queries) |
| Increased Supabase storage | Documents + embeddings | $0 (still within free tier) |
| Novel.sh | Open source | $0 |
| React Flow | Open source | $0 |
| **Additional Total** | | ~$4-20 |

### 10.3 Projected Total

| Scenario | Monthly Cost |
|----------|--------------|
| Light usage (10 research queries) | ~$15-35 |
| Medium usage (25 research queries) | ~$20-45 |
| Heavy usage (50 research queries) | ~$30-60 |

**Still well within budget** - Perplexity is the only variable cost, and deep research is valuable enough to justify $0.40/query.

---

## Appendix A: Novel.sh Customization

### Theme Integration

```typescript
// Extend Novel with our theme colors
const editorProps = {
  attributes: {
    class: `prose dark:prose-invert prose-headings:font-bold
            prose-a:text-primary hover:prose-a:text-primary/80
            prose-code:bg-muted prose-code:rounded prose-code:px-1
            max-w-none focus:outline-none`,
  },
};
```

### AI Autocomplete (Future)

```typescript
// Hook into Claude for /ai command
async function triggerAICompletion(editor: Editor) {
  const content = editor.storage.markdown.getMarkdown();
  const cursorPos = editor.state.selection.anchor;

  // Get context before cursor
  const contextBefore = content.slice(Math.max(0, cursorPos - 500), cursorPos);

  const completion = await fetch('/api/ai/complete', {
    method: 'POST',
    body: JSON.stringify({ context: contextBefore }),
  });

  const { text } = await completion.json();

  editor.commands.insertContent(text);
}
```

---

## Appendix B: Migration Checklist

### Pre-Migration
- [ ] Full database backup
- [ ] Document current row counts
- [ ] Test migration script on staging
- [ ] Update all environment variables

### Migration
- [ ] Run schema migration SQL
- [ ] Verify row counts match
- [ ] Run Python backend tests
- [ ] Run frontend tests
- [ ] Manual smoke test (search, view, create)

### Post-Migration
- [ ] Remove backward compatibility views (after 1 week)
- [ ] Drop old tables
- [ ] Update documentation
- [ ] Clean up migration artifacts

---

## Approval

- [ ] **Architecture Review**: Data model approved
- [ ] **UX Review**: Editor experience approved
- [ ] **Cost Review**: Perplexity costs acceptable
- [ ] **Timeline Review**: Phase sequencing approved

**Approved by**: _________________ **Date**: _________________
