# Phase 4: Next.js Application - Design Decisions

> **Created:** 2025-12-31
> **Phase:** 4 of 9
> **Status:** Implementation Complete

This document records the design decisions made during the Phase 4 implementation for future reference.

---

## 1. Embedding Strategy: Transformers.js (Browser)

**Decision:** Use `@xenova/transformers` with BGE-small-en-v1.5 model in browser

| Aspect | Details |
|--------|---------|
| **Model** | `Xenova/bge-small-en-v1.5` (384 dimensions) |
| **Location** | Client-side (browser) |
| **First load** | ~50MB download, cached in IndexedDB |
| **Latency** | 2-3 seconds for embedding generation |

### Trade-offs

**Advantages:**
- Zero API costs for embedding generation
- Complete privacy - queries never leave the browser
- Same model as Python backend = vector compatibility
- Works offline after initial download

**Disadvantages:**
- Large initial download (~50MB)
- Model loads on first search (2-3 seconds)
- Uses client CPU/memory for inference

### Alternative: OpenAI text-embedding-3-small

If switching to OpenAI embeddings is desired later:

| Aspect | OpenAI Alternative |
|--------|-------------------|
| **Model** | `text-embedding-3-small` |
| **Dimensions** | 1536 (configurable) |
| **Cost** | ~$0.02 per 1M tokens |
| **Latency** | <1 second (API call) |

**Migration steps:**
1. Add OpenAI API key to environment
2. Create new embedding generation endpoint
3. Run backfill script to regenerate all embeddings with new model
4. Update pgvector column dimension (1536 instead of 384)
5. Test vector search compatibility

**Important:** OpenAI and BGE embeddings are NOT compatible - switching requires re-embedding all content.

---

## 2. Authentication: None (Personal Use)

**Decision:** No authentication required

- Use Supabase anon key for all queries
- RLS policies restrict to read-only operations
- Simplest setup for personal knowledge base

**Future considerations:**
- If sharing with others, add Supabase Auth
- Consider row-level security for multi-user scenarios

---

## 3. Thesis/Entity Scope: Read-Only Pages

**Decision:** Build browse and detail pages that read from existing database data

- NO AI detection or synthesis in Phase 4 (that's Phase 7)
- Pages display existing data (may be empty initially)
- "Regenerate synthesis" functionality disabled until Phase 7

**Rationale:**
- Separates UI concerns from AI processing
- Allows testing UI with real data structure
- Phase 7 will add synthesis capabilities

---

## 4. Theming: Full Multi-Theme System

**Decision:** CSS variables + next-themes with 4 presets

### Implemented Themes

| Theme | Description | Primary Use |
|-------|-------------|-------------|
| Light | Clean white background | Daytime use |
| Dark | Deep blue-gray (oklch) | Night mode |
| Sepia | Warm book-like tones | Reading mode |
| Nord | Arctic blue-gray palette | Alternative dark |

### Implementation

- **CSS Variables:** All colors defined in `globals.css` using oklch color space
- **Theme Switching:** `next-themes` library with `attribute="class"`
- **Persistence:** localStorage via next-themes
- **System Theme:** Supported via `enableSystem`

### Adding New Themes

1. Add theme name to `themes` array in `ThemeProvider.tsx`
2. Add CSS class in `globals.css` with all color variables
3. Add theme config in `ThemePicker.tsx` for preview
4. Add icon/label in `ThemeSwitcher.tsx`

---

## 5. Component Library: shadcn/ui (Copied)

**Decision:** Copy components into codebase, not npm dependency

### Installed Components

- button, card, input, badge, skeleton
- dialog, dropdown-menu, select, tabs, separator

### Advantages

- Full customization control
- Components become "your code"
- No version lock-in
- Tree-shaking by default

### Adding New Components

```bash
cd web
npx shadcn@latest add [component-name]
```

---

## 6. Data Fetching Strategy

**Decision:** Server Components with `force-dynamic`

- All data pages use Server Components for initial fetch
- `export const dynamic = "force-dynamic"` prevents static generation
- Client components only for interactive features (search, theme switching)

### Rationale

- Data changes frequently (new bookmarks added via Telegram)
- No need for ISR complexity
- Simpler caching model
- Works well with Vercel deployment

---

## 7. Search Architecture

**Decision:** Client-side embedding generation + Supabase RPC

### Flow

1. User enters search query
2. Transformers.js generates 384-dim embedding in browser
3. Embedding sent to Supabase `match_posts` RPC function
4. PostgreSQL pgvector performs similarity search
5. Results returned with similarity scores

### Key Implementation Files

- `lib/embeddings/transformers.ts` - Singleton embedding service
- `hooks/useEmbeddings.ts` - React hook for initialization
- `hooks/useSearch.ts` - Search hook with debouncing
- `lib/queries/posts.ts` - `searchPosts()` function

---

## 8. TypeScript Patterns

### Junction Table Queries

Supabase generated types don't include junction tables. Pattern used:

```typescript
const { data } = await supabase
  .from("post_entities" as never)  // Type assertion
  .select("post_id, entity_id")
  .eq("entity_id", id);

const typedData = data as Array<{ post_id: string; entity_id: string }> | null;
```

### RPC Function Calls

```typescript
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const { data } = await (supabase as any).rpc("match_posts", {
  query_embedding: embedding,
  match_threshold: 0.7,
  match_count: 20,
});
```

---

## 9. Project Structure

```
web/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Home (dynamic)
│   ├── search/            # Search page (static shell)
│   ├── post/[id]/         # Post detail (dynamic)
│   ├── recent/            # Recent posts (dynamic)
│   ├── entities/          # Entity browse + detail
│   └── theses/            # Thesis browse + detail
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── layout/            # Header, Footer, PageContainer
│   ├── posts/             # PostCard, PostFeed, PostMedia
│   ├── search/            # SearchBar, EmbeddingLoader
│   ├── entities/          # EntityBadge, EntityCard
│   ├── theses/            # ThesisBadge, SynthesisCard
│   └── theme/             # ThemeProvider, ThemeSwitcher
├── lib/
│   ├── supabase/          # Supabase client
│   ├── embeddings/        # Transformers.js service
│   └── queries/           # posts, entities, theses, stats
├── hooks/                 # useEmbeddings, useSearch
├── types/                 # database.ts
└── docs/                  # This file
```

---

## Future Considerations

### Phase 5: RAG Chat Interface
- Add `/chat` page
- Create `/api/chat` route for Claude API
- Implement streaming responses with citations

### Phase 6: Vercel Deployment
- Connect to GitHub repository
- Configure environment variables
- Set up preview deployments

### Phase 7: Thesis System
- AI-powered entity detection
- Thesis synthesis generation
- Knowledge graph visualization

---

## References

- [Transformers.js Documentation](https://huggingface.co/docs/transformers.js)
- [next-themes GitHub](https://github.com/pacocoursey/next-themes)
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [Supabase pgvector Guide](https://supabase.com/docs/guides/ai/vector-search)
