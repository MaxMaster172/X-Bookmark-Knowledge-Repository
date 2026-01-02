/**
 * Chat interface types for RAG-powered chat
 *
 * This module defines types for:
 * - Chat messages (user/assistant with sources)
 * - Chat state management
 * - Server-Sent Events (SSE) streaming
 */

import type { ContextPost, SourceCitation } from "@/lib/rag";

// Re-export RAG types for convenience
export type { ContextPost, SourceCitation } from "@/lib/rag";

// ============================================
// MESSAGE TYPES
// ============================================

/**
 * Role of a chat message sender
 */
export type MessageRole = "user" | "assistant";

/**
 * Source reference from a retrieved post
 */
export interface Source {
  postId: string;
  title: string | null;
  authorHandle: string | null;
  url: string;
  similarity?: number;
  index: number; // 1-based citation index
}

/**
 * A single chat message
 */
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  sources?: Source[]; // Only for assistant messages
  createdAt: Date;
}

/**
 * Message for API communication (without metadata)
 */
export interface ChatMessage {
  role: MessageRole;
  content: string;
}

// ============================================
// CHAT STATE TYPES
// ============================================

/**
 * State of the chat interface
 */
export interface ChatState {
  /** All messages in the conversation */
  messages: Message[];
  /** Currently streaming message content */
  streamingContent: string;
  /** Whether the assistant is currently responding */
  isLoading: boolean;
  /** Error message if something went wrong */
  error: string | null;
  /** Context posts retrieved for the current query */
  contextPosts: ContextPost[];
  /** Session ID for the conversation (optional) */
  sessionId?: string;
}

/**
 * Initial/default chat state
 */
export const initialChatState: ChatState = {
  messages: [],
  streamingContent: "",
  isLoading: false,
  error: null,
  contextPosts: [],
};

// ============================================
// STREAMING EVENT TYPES
// ============================================

/**
 * Types of streaming chunks from the chat API
 */
export type StreamChunkType = "text" | "context" | "error" | "done";

/**
 * Base streaming chunk interface
 */
interface BaseStreamChunk {
  type: StreamChunkType;
}

/**
 * Text chunk - contains streamed response text
 */
export interface TextStreamChunk extends BaseStreamChunk {
  type: "text";
  content: string;
}

/**
 * Context chunk - contains retrieved context posts
 */
export interface ContextStreamChunk extends BaseStreamChunk {
  type: "context";
  contextPosts: ContextPost[];
}

/**
 * Error chunk - contains error message
 */
export interface ErrorStreamChunk extends BaseStreamChunk {
  type: "error";
  error: string;
}

/**
 * Done chunk - signals end of stream
 */
export interface DoneStreamChunk extends BaseStreamChunk {
  type: "done";
}

/**
 * Union type for all streaming chunks
 */
export type StreamChunk =
  | TextStreamChunk
  | ContextStreamChunk
  | ErrorStreamChunk
  | DoneStreamChunk;

// ============================================
// API REQUEST/RESPONSE TYPES
// ============================================

/**
 * Request body for the chat API
 */
export interface ChatRequest {
  /** The user's message */
  message: string;
  /** Previous conversation history */
  history: ChatMessage[];
  /** 384-dimensional embedding for semantic search */
  embedding?: number[];
  /** Specific post IDs to include in context */
  contextPostIds?: string[];
}

/**
 * Parsed response from SSE stream
 */
export interface ParsedStreamResponse {
  /** Full accumulated text content */
  content: string;
  /** Context posts from the context chunk */
  contextPosts: ContextPost[];
  /** Error if one occurred */
  error: string | null;
  /** Whether the stream is complete */
  done: boolean;
}

// ============================================
// TYPE GUARDS
// ============================================

/**
 * Type guard for text stream chunk
 */
export function isTextChunk(chunk: StreamChunk): chunk is TextStreamChunk {
  return chunk.type === "text";
}

/**
 * Type guard for context stream chunk
 */
export function isContextChunk(chunk: StreamChunk): chunk is ContextStreamChunk {
  return chunk.type === "context";
}

/**
 * Type guard for error stream chunk
 */
export function isErrorChunk(chunk: StreamChunk): chunk is ErrorStreamChunk {
  return chunk.type === "error";
}

/**
 * Type guard for done stream chunk
 */
export function isDoneChunk(chunk: StreamChunk): chunk is DoneStreamChunk {
  return chunk.type === "done";
}

// ============================================
// UTILITY TYPES
// ============================================

/**
 * Convert ContextPost to Source for display
 */
export function contextPostToSource(post: ContextPost): Source {
  return {
    postId: post.id,
    title: post.content?.slice(0, 100) || null, // Use first 100 chars as title
    authorHandle: post.authorHandle,
    url: post.url,
    similarity: post.similarity,
    index: post.index,
  };
}

/**
 * Convert SourceCitation to Source
 */
export function sourceCitationToSource(
  citation: SourceCitation,
  contextPosts: ContextPost[]
): Source | null {
  const post = contextPosts.find((p) => p.index === citation.index);
  if (!post) return null;

  return {
    postId: citation.postId,
    title: post.content?.slice(0, 100) || null,
    authorHandle: citation.authorHandle,
    url: citation.url,
    similarity: post.similarity,
    index: citation.index,
  };
}

/**
 * Generate a unique message ID
 */
export function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

/**
 * Create a new user message
 */
export function createUserMessage(content: string): Message {
  return {
    id: generateMessageId(),
    role: "user",
    content,
    createdAt: new Date(),
  };
}

/**
 * Create a new assistant message
 */
export function createAssistantMessage(
  content: string,
  sources?: Source[]
): Message {
  return {
    id: generateMessageId(),
    role: "assistant",
    content,
    sources,
    createdAt: new Date(),
  };
}
