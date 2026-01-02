# Task 03: Create Chat Message Types - COMPLETED

## Summary

Created comprehensive TypeScript types for the RAG chat interface in `web/src/types/chat.ts`.

## Files Created

- `web/src/types/chat.ts` - Chat interface types

## Types Defined

### Message Types
- `MessageRole` - "user" | "assistant"
- `Source` - Reference to a retrieved post (postId, title, authorHandle, url, similarity, index)
- `Message` - Full chat message with id, role, content, optional sources, createdAt
- `ChatMessage` - Lightweight message for API communication

### State Types
- `ChatState` - Full chat interface state:
  - `messages: Message[]` - Conversation history
  - `streamingContent: string` - Currently streaming text
  - `isLoading: boolean` - Loading state
  - `error: string | null` - Error state
  - `contextPosts: ContextPost[]` - Retrieved posts
  - `sessionId?: string` - Optional session tracking
- `initialChatState` - Default state constant

### Streaming Types (aligned with API route)
- `StreamChunkType` - "text" | "context" | "error" | "done"
- `TextStreamChunk` - { type: "text", content: string }
- `ContextStreamChunk` - { type: "context", contextPosts: ContextPost[] }
- `ErrorStreamChunk` - { type: "error", error: string }
- `DoneStreamChunk` - { type: "done" }
- `StreamChunk` - Union of all chunk types

### API Types
- `ChatRequest` - Request body (message, history, embedding?, contextPostIds?)
- `ParsedStreamResponse` - Accumulated stream response

### Type Guards
- `isTextChunk()`, `isContextChunk()`, `isErrorChunk()`, `isDoneChunk()`

### Utility Functions
- `contextPostToSource()` - Convert ContextPost to Source
- `sourceCitationToSource()` - Convert SourceCitation to Source
- `generateMessageId()` - Generate unique message ID
- `createUserMessage()` - Factory for user messages
- `createAssistantMessage()` - Factory for assistant messages

## Re-exports

The file re-exports `ContextPost` and `SourceCitation` from `@/lib/rag` for convenience.

## Integration Notes

1. **Import pattern**:
   ```typescript
   import type { Message, ChatState, StreamChunk } from "@/types/chat";
   import { isTextChunk, createUserMessage } from "@/types/chat";
   ```

2. **State management**: Use `initialChatState` as default state in React hooks/components

3. **Type guards**: Use type guards when processing SSE chunks:
   ```typescript
   if (isTextChunk(chunk)) {
     setContent(prev => prev + chunk.content);
   }
   ```

## Verification

- TypeScript compiles without errors (`npx tsc --noEmit` passes)
- Types align with API route's StreamChunk interface
- Re-exports from `lib/rag.ts` work correctly

## Next Task

Task 04: Create useChat custom hook that uses these types for state management and SSE streaming.
