"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useEmbeddings } from "./useEmbeddings";
import {
  checkRateLimit,
  recordMessage,
  type RateLimitState,
} from "@/lib/rateLimit";
import type {
  Message,
  ChatMessage,
  ChatState,
  StreamChunk,
  Source,
  ContextPost,
  ChatRequest,
} from "@/types/chat";
import {
  createUserMessage,
  createAssistantMessage,
  contextPostToSource,
  isTextChunk,
  isContextChunk,
  isErrorChunk,
} from "@/types/chat";

export interface UseChatOptions {
  /** Auto-initialize embeddings on mount */
  autoInitialize?: boolean;
}

export interface UseChatReturn {
  /** All messages in the conversation */
  messages: Message[];
  /** Whether the assistant is currently responding */
  isLoading: boolean;
  /** Error message if something went wrong */
  error: string | null;
  /** Context posts retrieved for the current query */
  contextPosts: ContextPost[];
  /** Currently streaming content (not yet added to messages) */
  streamingContent: string;
  /** Send a new message */
  sendMessage: (content: string) => Promise<void>;
  /** Retry the last failed message */
  retry: () => Promise<void>;
  /** Clear all messages */
  clearMessages: () => void;
  /** Embedding model state */
  embeddings: {
    isReady: boolean;
    isLoading: boolean;
    progress: number;
    progressStatus: string;
    initialize: () => Promise<void>;
  };
  /** Rate limiting state */
  rateLimit: RateLimitState;
}

const DEFAULT_OPTIONS: Required<UseChatOptions> = {
  autoInitialize: false,
};

/**
 * React hook for managing RAG-powered chat with streaming
 *
 * Features:
 * - Generates embeddings for semantic search
 * - Streams responses via SSE
 * - Tracks context posts for citations
 * - Supports retry and clear
 *
 * Usage:
 * ```tsx
 * const {
 *   messages,
 *   isLoading,
 *   sendMessage,
 *   contextPosts,
 *   embeddings
 * } = useChat();
 *
 * // Initialize embeddings first
 * await embeddings.initialize();
 *
 * // Send a message
 * await sendMessage("What did I bookmark about AI?");
 * ```
 */
export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const opts = { ...DEFAULT_OPTIONS, ...options };

  const {
    isReady,
    isLoading: embeddingsLoading,
    progress,
    progressStatus,
    embed,
    initialize,
    error: embeddingError,
  } = useEmbeddings();

  const [state, setState] = useState<ChatState>({
    messages: [],
    streamingContent: "",
    isLoading: false,
    error: null,
    contextPosts: [],
  });

  // Rate limit state - initialize with default, update on client
  const [rateLimitState, setRateLimitState] = useState<RateLimitState>({
    canSend: true,
    remaining: 20,
    limit: 20,
    resetInMs: null,
  });

  // Track the last user message for retry functionality
  const lastUserMessageRef = useRef<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Initialize rate limit state on client
  useEffect(() => {
    setRateLimitState(checkRateLimit());
  }, []);

  // Update rate limit state periodically (every 10 seconds) to refresh the countdown
  useEffect(() => {
    const interval = setInterval(() => {
      setRateLimitState(checkRateLimit());
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  // Auto-initialize if enabled
  useEffect(() => {
    if (opts.autoInitialize && !isReady && !embeddingsLoading) {
      initialize();
    }
  }, [opts.autoInitialize, isReady, embeddingsLoading, initialize]);

  /**
   * Parse SSE stream and process chunks
   */
  const processStream = useCallback(
    async (
      response: Response,
      onText: (text: string) => void,
      onContext: (posts: ContextPost[]) => void,
      onError: (error: string) => void,
      onDone: () => void,
      signal: AbortSignal
    ) => {
      const reader = response.body?.getReader();
      if (!reader) {
        onError("No response body");
        onDone();
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          if (signal.aborted) {
            reader.cancel();
            return;
          }

          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE messages
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || ""; // Keep incomplete message in buffer

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;

            try {
              const data = line.slice(6); // Remove "data: " prefix
              const chunk: StreamChunk = JSON.parse(data);

              if (isTextChunk(chunk)) {
                onText(chunk.content);
              } else if (isContextChunk(chunk)) {
                onContext(chunk.contextPosts);
              } else if (isErrorChunk(chunk)) {
                onError(chunk.error);
              } else if (chunk.type === "done") {
                onDone();
                return;
              }
            } catch (parseError) {
              console.error("Error parsing SSE chunk:", parseError);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    },
    []
  );

  /**
   * Send a message to the chat API
   */
  const sendMessage = useCallback(
    async (content: string) => {
      const trimmedContent = content.trim();
      if (!trimmedContent) return;

      // Check rate limit before sending
      const currentRateLimit = checkRateLimit();
      if (!currentRateLimit.canSend) {
        setState((prev) => ({
          ...prev,
          error: "Rate limit exceeded. Please wait before sending more messages.",
        }));
        setRateLimitState(currentRateLimit);
        return;
      }

      // Cancel any in-flight request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      // Store for retry
      lastUserMessageRef.current = trimmedContent;

      // Create user message
      const userMessage = createUserMessage(trimmedContent);

      // Update state with user message
      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        streamingContent: "",
        isLoading: true,
        error: null,
        contextPosts: [],
      }));

      let accumulatedContent = "";
      let retrievedContextPosts: ContextPost[] = [];

      try {
        // Generate embedding for the message
        const embedding = await embed(trimmedContent);

        // Build history from existing messages
        const history: ChatMessage[] = state.messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
        }));

        // Make API request
        const requestBody: ChatRequest = {
          message: trimmedContent,
          history,
          embedding,
        };

        const response = await fetch("/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
          signal: abortController.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`);
        }

        // Process the stream
        await processStream(
          response,
          // onText
          (text) => {
            accumulatedContent += text;
            setState((prev) => ({
              ...prev,
              streamingContent: accumulatedContent,
            }));
          },
          // onContext
          (posts) => {
            retrievedContextPosts = posts;
            setState((prev) => ({
              ...prev,
              contextPosts: posts,
            }));
          },
          // onError
          (error) => {
            setState((prev) => ({
              ...prev,
              error,
              isLoading: false,
            }));
          },
          // onDone
          () => {
            // Create assistant message with sources
            const sources: Source[] = retrievedContextPosts.map(contextPostToSource);
            const assistantMessage = createAssistantMessage(accumulatedContent, sources);

            // Record message for rate limiting (count user messages)
            recordMessage();
            setRateLimitState(checkRateLimit());

            setState((prev) => ({
              ...prev,
              messages: [...prev.messages, assistantMessage],
              streamingContent: "",
              isLoading: false,
            }));
          },
          abortController.signal
        );
      } catch (error) {
        // Ignore abort errors
        if (error instanceof Error && error.name === "AbortError") {
          return;
        }

        const errorMessage =
          error instanceof Error ? error.message : "Unknown error occurred";

        setState((prev) => ({
          ...prev,
          error: errorMessage,
          isLoading: false,
          streamingContent: "",
        }));
      }
    },
    [embed, processStream, state.messages]
  );

  /**
   * Retry the last failed message
   */
  const retry = useCallback(async () => {
    if (!lastUserMessageRef.current) return;

    // Remove the last user message if there was an error
    setState((prev) => {
      // Find the last user message
      const lastUserIdx = prev.messages.findLastIndex((m) => m.role === "user");
      if (lastUserIdx === -1) return prev;

      // Remove messages from last user message onwards
      return {
        ...prev,
        messages: prev.messages.slice(0, lastUserIdx),
        error: null,
      };
    });

    // Resend the message
    await sendMessage(lastUserMessageRef.current);
  }, [sendMessage]);

  /**
   * Clear all messages and reset state
   */
  const clearMessages = useCallback(() => {
    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    lastUserMessageRef.current = null;

    setState({
      messages: [],
      streamingContent: "",
      isLoading: false,
      error: null,
      contextPosts: [],
    });
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Combine embedding error with chat error
  const error = state.error || (embeddingError?.message ?? null);

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error,
    contextPosts: state.contextPosts,
    streamingContent: state.streamingContent,
    sendMessage,
    retry,
    clearMessages,
    embeddings: {
      isReady,
      isLoading: embeddingsLoading,
      progress,
      progressStatus,
      initialize,
    },
    rateLimit: rateLimitState,
  };
}
