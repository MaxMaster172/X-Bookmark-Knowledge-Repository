# Task 05 Handoff: Build Chat UI Components

## Status: COMPLETE

## What Was Done

Created all chat UI components for the RAG-powered chat interface:

### Files Created

1. **`web/src/components/chat/SourceCitation.tsx`**
   - `SourceCitation` - Inline citation badge `[1]`, `[2]` that links to the source post
   - `SourceList` - Display a list of source citations (for message footers)
   - Props: `source`, `onClick`, `inline` (inline vs standalone variant)
   - Uses shadcn Badge component for standalone variant

2. **`web/src/components/chat/ChatMessage.tsx`**
   - `ChatMessage` - Message bubble with role-based styling
     - User messages: Right-aligned with primary color background
     - Assistant messages: Left-aligned with muted background
   - `StreamingMessage` - Minimal message for in-progress streaming with blinking cursor
   - Features:
     - Parses `[1]`, `[2]` citations inline and replaces with clickable `SourceCitation`
     - Shows source list at bottom of assistant messages
     - Displays timestamp
     - Supports streaming animation

3. **`web/src/components/chat/ChatInput.tsx`**
   - Auto-resizing textarea (grows with content, max 200px)
   - Enter to send, Shift+Enter for new line
   - Disabled state while streaming
   - Send button with loading spinner
   - Custom SVG icons (SendIcon, LoadingSpinner)

4. **`web/src/components/chat/ContextSidebar.tsx`**
   - `ContextSidebar` - Collapsible sidebar showing context posts
     - Shows post preview with author, date, similarity score
     - Links to full post view
     - Empty state with bookmark icon
   - `ContextDrawer` - Mobile-friendly drawer version with backdrop

5. **`web/src/components/chat/index.ts`**
   - Barrel export for all components

### CSS Addition

Added to `web/src/app/globals.css`:
```css
/* Chat cursor blink animation */
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.animate-blink {
  animation: blink 1s step-end infinite;
}
```

## Type Integration

Components use types from `web/src/types/chat.ts`:
- `Message` - id, role, content, sources?, createdAt
- `Source` - postId, title, authorHandle, url, similarity, index
- `ContextPost` - id, index, content, authorHandle, postedAt, url, similarity

## Usage Example

```tsx
import {
  ChatMessage,
  StreamingMessage,
  ChatInput,
  ContextSidebar,
} from "@/components/chat";
import { useChat } from "@/hooks/useChat";

function ChatPage() {
  const {
    messages,
    streamingContent,
    isLoading,
    contextPosts,
    sendMessage,
  } = useChat({ autoInitialize: true });

  return (
    <div className="flex h-screen">
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}
          {streamingContent && (
            <StreamingMessage content={streamingContent} />
          )}
        </div>

        {/* Input */}
        <ChatInput
          onSend={sendMessage}
          isLoading={isLoading}
          disabled={isLoading}
        />
      </div>

      {/* Context sidebar */}
      <ContextSidebar contextPosts={contextPosts} />
    </div>
  );
}
```

## Dependencies Used

- `@/components/ui/badge` - For citation badges
- `@/components/ui/button` - For send button and toggle buttons
- `@/components/ui/card` - For context post cards
- `@/lib/utils` (cn) - For class merging
- `next/link` - For navigation to posts

## Design Decisions

1. **Inline Citation Parsing**: ChatMessage parses content with regex to find `[1]`, `[2]` patterns and replaces them with interactive SourceCitation components.

2. **Dual Message Display**: Separate `ChatMessage` (for finalized messages) and `StreamingMessage` (for in-progress) to keep concerns separate.

3. **Collapsible Sidebar + Drawer**: ContextSidebar has a collapsible mode for desktop and a separate ContextDrawer component for mobile-friendly overlay.

4. **Theme Support**: All components use theme-aware colors (dark:, etc.) for proper display across light, dark, sepia, and nord themes.

## Ready For Next Task

Task 06 can now build the chat page that composes these components together with the useChat hook.

## Files Changed

- `web/src/components/chat/SourceCitation.tsx` (new)
- `web/src/components/chat/ChatMessage.tsx` (new)
- `web/src/components/chat/ChatInput.tsx` (new)
- `web/src/components/chat/ContextSidebar.tsx` (new)
- `web/src/components/chat/index.ts` (new)
- `web/src/app/globals.css` (modified - added blink animation)
