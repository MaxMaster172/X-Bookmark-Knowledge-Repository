# Task 04 Handoff: Create useChat Hook

## Completed: 2026-01-02

## Summary

Created `web/src/hooks/useChat.ts` - a React hook for managing RAG-powered chat with streaming responses.

## Files Created

- `web/src/hooks/useChat.ts`

## Implementation Details

### Hook Interface

```typescript
export interface UseChatReturn {
  messages: Message[];           // All messages in conversation
  isLoading: boolean;            // Assistant is responding
  error: string | null;          // Error message if any
  contextPosts: ContextPost[];   // Retrieved context for current query
  streamingContent: string;      // Streaming content (not yet in messages)
  sendMessage: (content: string) => Promise<void>;
  retry: () => Promise<void>;
  clearMessages: () => void;
  embeddings: {
    isReady: boolean;
    isLoading: boolean;
    progress: number;
    progressStatus: string;
    initialize: () => Promise<void>;
  };
}
```

### Key Features

1. **Embedding Generation**: Uses `useEmbeddings` hook to generate 384-dimensional vectors for user messages before API calls

2. **SSE Stream Processing**: Custom `processStream` function parses Server-Sent Events:
   - `text` chunks - accumulated into `streamingContent`
   - `context` chunks - stored in `contextPosts` for citation rendering
   - `error` chunks - sets error state
   - `done` chunks - finalizes assistant message with sources

3. **Message Management**:
   - `sendMessage(content)` - generates embedding, POSTs to `/api/chat`, processes stream
   - `retry()` - removes failed user message and re-sends
   - `clearMessages()` - resets all state

4. **Abort Controller**: Cancels in-flight requests when:
   - New message sent before previous completes
   - Component unmounts
   - `clearMessages()` called

5. **Source Citation Integration**: When stream completes, converts `ContextPost[]` to `Source[]` for the assistant message

### Pattern Followed

Based on `useSearch.ts`:
- Same `useEmbeddings` integration pattern
- Same abort controller cleanup pattern
- Same auto-initialize option
- Exposes embedding state to consumers

### Usage Example

```tsx
const { messages, sendMessage, isLoading, embeddings, contextPosts } = useChat();

// Initialize model
useEffect(() => {
  embeddings.initialize();
}, []);

// Send message
const handleSend = async (input: string) => {
  await sendMessage(input);
};

// Render messages with sources from contextPosts
```

## Testing Notes

- TypeScript compiles without errors
- Hook follows existing patterns in codebase
- Requires `/api/chat` endpoint (Task 02) and types (Task 03)

## Dependencies Used

- `@/hooks/useEmbeddings` - embedding generation
- `@/types/chat` - all type definitions and helpers

## Next Task

Task 05: Build ChatInterface Component
- Use this hook to manage state
- Render messages with streaming support
- Display source citations from `contextPosts`
- Show embedding model loading state
