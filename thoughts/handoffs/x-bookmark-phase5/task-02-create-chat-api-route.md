# Task 02 Handoff: Create Chat API Route

**Status**: Complete
**Date**: 2026-01-02

## Summary

Created the `/api/chat` API route with streaming response support, RAG context building, and the supporting utilities.

## Files Created

### 1. `web/src/lib/rag.ts`
RAG (Retrieval Augmented Generation) utilities for the chat interface:

- **`ContextPost`** interface - Represents a post with context for RAG (id, index, content, author, URL, similarity)
- **`SourceCitation`** interface - Parsed source citation from Claude's response
- **`buildContextPosts()`** - Convert search results to context posts with 1-based indices
- **`buildSystemPrompt()`** - Build the system prompt with post context for Claude
- **`parseSourceCitations()`** - Extract `[1]`, `[2]` style citations from response text
- **`buildContextFromPosts()`** - Build context from specific post IDs
- **`truncateContent()`** - Truncate long content to max length
- **`estimateTokenCount()`** - Rough token estimation (chars / 4)
- **`limitContextByTokens()`** - Limit context posts to stay within token budget

### 2. `web/src/lib/supabase/server.ts`
Server-side Supabase client for API routes:

- **`createServerClient()`** - Create a Supabase client for server-side operations
- Uses the same anon key as browser client (no service role key needed for read-only operations)

### 3. `web/src/app/api/chat/route.ts`
The main chat API route with:

- **POST handler** with streaming SSE response
- **Request body**: `{ message, history, embedding?, contextPostIds? }`
- **Streaming response format**: SSE with chunk types:
  - `type: "context"` - Sends the context posts being used
  - `type: "text"` - Streamed text chunks from Claude
  - `type: "error"` - Error messages
  - `type: "done"` - Completion signal

**Key features**:
- Accepts embedding vector from client for vector search
- Falls back to specific post IDs if provided
- Limits context to ~4000 tokens to leave room for response
- Graceful error handling with user-friendly messages
- Model: `claude-sonnet-4-5-20250514`

## API Usage

### Request
```typescript
POST /api/chat
Content-Type: application/json

{
  "message": "What are the best AI investing strategies?",
  "history": [
    { "role": "user", "content": "previous message" },
    { "role": "assistant", "content": "previous response" }
  ],
  "embedding": [0.1, 0.2, ...], // 384-dim vector from Transformers.js
  "contextPostIds": ["post-id-1", "post-id-2"] // Optional: override auto-search
}
```

### Response (SSE Stream)
```
data: {"type":"context","contextPosts":[...]}

data: {"type":"text","content":"Based on"}

data: {"type":"text","content":" your bookmarks"}

data: {"type":"text","content":", the key strategies [1] are..."}

data: {"type":"done"}

```

## Verification

- TypeScript build: `npm run build` - passes
- ESLint: No errors on new files
- Route registered at `/api/chat` (visible in build output)

## Dependencies

- Task 01's `@anthropic-ai/sdk` package (already installed)
- Existing `match_posts` Supabase RPC function
- Existing database types from `@/types/database`

## Next Task

Task 03: Create Chat Message Types (`web/src/types/chat.ts`)

The types needed:
- `Message` (role, content, sources)
- `ChatState` interface
- `Source` type (post_id, title, similarity)
- Streaming event types (already partially defined in route.ts)

## Notes for Client Implementation

The client (useChat hook) should:
1. Generate embedding for user message using `useEmbeddings` hook
2. Call `/api/chat` with `EventSource` or `fetch` with response streaming
3. Parse SSE chunks and update UI as tokens stream in
4. Extract context posts from `type: "context"` chunk for sidebar display
5. Use `parseSourceCitations()` from `@/lib/rag` to make citations clickable
