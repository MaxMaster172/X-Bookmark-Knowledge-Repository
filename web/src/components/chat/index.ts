/**
 * Chat UI Components
 *
 * This module exports the chat interface components for the RAG-powered chat.
 *
 * Components:
 * - ChatMessage: Message bubble with role styling and inline citations
 * - StreamingMessage: Display for in-progress streaming responses
 * - ChatInput: Input with send button, disabled while streaming
 * - SourceCitation: Inline citation badge [1], [2], etc.
 * - SourceList: Display a list of source citations
 * - ContextSidebar: Shows posts being used as context (collapsible)
 * - ContextDrawer: Mobile-friendly drawer version of ContextSidebar
 */

export { ChatMessage, StreamingMessage } from "./ChatMessage";
export { ChatInput } from "./ChatInput";
export { SourceCitation, SourceList } from "./SourceCitation";
export { ContextSidebar, ContextDrawer } from "./ContextSidebar";
