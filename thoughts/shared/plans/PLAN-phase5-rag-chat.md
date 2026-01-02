# Plan: Phase 5 - RAG Chat Interface

## Goal

Build a Claude-powered chat interface with streaming responses and source citations. Users can ask questions about their bookmarked knowledge, and the system retrieves relevant posts as context for Claude to answer.

## Technical Choices

- **LLM**: Claude 4.5 Sonnet (`claude-sonnet-4-5-20250514`) via Anthropic SDK - latest model
- **Streaming**: Server-Sent Events (native fetch streaming) - simpler than WebSockets
- **RAG**: Reuse existing `searchPosts()` with browser embeddings for context retrieval
- **Session Storage**: Use existing `sessions` table for conversation history
- **Rate Limiting**: Per-session limits (messages per hour) - simple, client-side tracking

## Current State Analysis

### Existing Infrastructure (from Phase 4):
- **Embeddings**: `lib/embeddings/transformers.ts` - browser-based BGE embeddings (384 dims)
- **Vector Search**: `lib/queries/posts.ts:searchPosts()` - Supabase RPC with match_posts
- **Hooks Pattern**: `hooks/useSearch.ts` - debounced search with embeddings
- **Types**: `types/database.ts` - includes Session, SearchResult types
- **UI Components**: PostCard, Badge, skeleton loaders exist

### Key Files:
- `web/src/lib/queries/posts.ts` - `searchPosts()` function to reuse for RAG
- `web/src/hooks/useSearch.ts` - pattern to follow for chat hook
- `web/src/types/database.ts` - Session type exists (lines 112-118)
- `web/src/app/search/page.tsx` - UI pattern to follow

## Tasks

### Task 1: Install Anthropic SDK

Add the Anthropic Node.js SDK for Claude API calls.

- [ ] Add `@anthropic-ai/sdk` to package.json
- [ ] Add `ANTHROPIC_API_KEY` to `.env.local` template

**Files to create:**
- None (just npm install)

**Files to modify:**
- `web/package.json`

---

### Task 2: Create Chat API Route

Build the `/api/chat` route that handles Claude API calls with streaming.

- [ ] Create route handler with POST method
- [ ] Accept message, history, and optional contextPostIds
- [ ] Generate embedding for user message (server-side via Python helper or pass from client)
- [ ] Retrieve relevant posts via Supabase RPC
- [ ] Build RAG prompt with post context
- [ ] Stream Claude response with source markers
- [ ] Handle errors gracefully

**Key implementation details:**
- Use `ReadableStream` for streaming response
- System prompt instructs Claude to cite sources as `[1]`, `[2]` etc.
- Post context includes id, content, author, and URL for citation building
- Rate limiting: check session message count in header/cookie

**Files to create:**
- `web/src/app/api/chat/route.ts`
- `web/src/lib/rag.ts` (RAG utilities: buildContext, parseSourceCitations)

---

### Task 3: Create Chat Message Types

Define TypeScript types for chat messages and streaming.

- [ ] Create Message type (role, content, sources)
- [ ] Create ChatState interface
- [ ] Create Source type (post_id, title, similarity)
- [ ] Create streaming event types

**Files to create:**
- `web/src/types/chat.ts`

---

### Task 4: Create useChat Hook

Build a React hook for managing chat state and streaming.

- [ ] Manage message history state
- [ ] Handle streaming response parsing
- [ ] Extract source citations from response
- [ ] Track loading/error states
- [ ] Support message retry
- [ ] Track context posts (manually added)

**Pattern to follow:** `useSearch.ts` hook structure

**Files to create:**
- `web/src/hooks/useChat.ts`

---

### Task 5: Build Chat UI Components

Create the chat interface components.

- [ ] ChatMessage - message bubble with role styling
- [ ] ChatInput - input with send button, disabled while streaming
- [ ] SourceCitation - inline citation badge (clickable, links to post)
- [ ] ContextSidebar - shows posts being used as context
- [ ] ChatContainer - full chat layout wrapper

**Files to create:**
- `web/src/components/chat/ChatMessage.tsx`
- `web/src/components/chat/ChatInput.tsx`
- `web/src/components/chat/SourceCitation.tsx`
- `web/src/components/chat/ContextSidebar.tsx`
- `web/src/components/chat/index.ts` (barrel export)

---

### Task 6: Build Chat Page

Create the `/chat` route with full chat interface.

- [ ] Full-screen chat layout
- [ ] Message history display with streaming
- [ ] Context sidebar (collapsible on mobile)
- [ ] Example prompts for empty state
- [ ] Embedding model loading indicator (reuse EmbeddingLoader)

**Files to create:**
- `web/src/app/chat/page.tsx`

---

### Task 7: Add Chat Navigation

Add chat link to header and home page.

- [ ] Add "Chat" link to Header navigation
- [ ] Add "Chat with your bookmarks" CTA on home page
- [ ] Add "Chat about this" button on post detail page

**Files to modify:**
- `web/src/components/layout/Header.tsx`
- `web/src/app/page.tsx` or `HomeClient.tsx`
- `web/src/app/post/[id]/page.tsx`

---

### Task 8: Implement Rate Limiting (Simple)

Add basic client-side rate limiting to prevent API cost runaway.

- [ ] Track messages per session in localStorage
- [ ] Display remaining messages count
- [ ] Configurable via env var (NEXT_PUBLIC_CHAT_RATE_LIMIT)
- [ ] Reset counter hourly

**Files to modify:**
- `web/src/hooks/useChat.ts`
- `web/src/app/chat/page.tsx`

**Files to create:**
- `web/src/lib/rateLimit.ts`

---

## Success Criteria

### Automated Verification:
- [ ] TypeScript: `cd web && npm run build` - no type errors
- [ ] Lint: `cd web && npm run lint` - passes

### Manual Verification:
- [ ] Navigate to `/chat` - page loads with empty state
- [ ] Send a message - streaming response appears token-by-token
- [ ] Source citations appear as clickable badges
- [ ] Clicking citation navigates to post detail
- [ ] Context sidebar shows retrieved posts
- [ ] Rate limit indicator visible
- [ ] Works on mobile (responsive layout)

---

## Out of Scope

- **Session persistence** - save/load conversations (Phase 8)
- **Export functionality** - export chat as markdown (later)
- **Thread generation** - generate Twitter threads from chat (later)
- **Multi-turn RAG refinement** - retrieving more context mid-conversation
- **Thesis-aware context** - using thesis relationships for better retrieval (Phase 7)

---

## Rate Limiting Strategy (addressing open question)

Per the open question in ARCHITECTURE.md:

**Recommended approach:**
- **Limit**: 20 messages per hour per session
- **Enforcement**: Client-side (localStorage) - simple, good enough for personal use
- **Display**: "X messages remaining this hour" in chat UI
- **Reset**: Rolling window (hourly reset)

**Rationale:**
- At ~$0.01-0.02 per message (Sonnet 4.5), 20 msg/hr = ~$5-10/day max if used constantly
- Personal use = unlikely to hit limits often
- Client-side is sufficient (not protecting against abuse, just cost awareness)

---

## Implementation Notes

### RAG Prompt Structure

```
System: You are a helpful assistant that answers questions based on the user's
bookmarked knowledge. You have access to the following bookmarked posts:

[Post 1] @author_handle (2024-01-15):
"Content of the post..."
URL: https://x.com/...

[Post 2] @author_handle (2024-01-10):
"Content of the post..."
URL: https://x.com/...

When answering, cite your sources using [1], [2], etc. to reference the posts above.
If you cannot find relevant information in the bookmarks, say so honestly.

User: {message}
```

### Streaming Response Parsing

Parse Claude response in chunks, looking for citation markers `[1]`, `[2]` etc.
Replace with clickable badges linking to the corresponding post.

### Context Retrieval

1. Generate embedding for user message (browser-side, reuse existing)
2. Call `searchPosts(embedding, threshold=0.5, limit=5)` to get top 5 relevant posts
3. Build context string with post content and metadata
4. Optional: User can manually add posts to context from search page
