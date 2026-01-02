"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmbeddingLoader } from "@/components/search";
import {
  ChatMessage,
  StreamingMessage,
  ChatInput,
  ContextSidebar,
  ContextDrawer,
} from "@/components/chat";
import { useChat } from "@/hooks/useChat";
import { formatResetTime } from "@/lib/rateLimit";

/**
 * Example prompts for the empty chat state
 */
const EXAMPLE_PROMPTS = [
  "What do my bookmarks say about AI investing?",
  "Summarize the key insights from @username",
  "Find connections between topics X and Y",
  "What are the most common themes in my bookmarks?",
];

/**
 * Chat page component - RAG-powered chat interface for asking questions
 * about bookmarked content.
 *
 * Features:
 * - Full-screen chat layout with message history
 * - Streaming responses with real-time text display
 * - Context sidebar showing retrieved posts (collapsible)
 * - Mobile drawer for context on small screens
 * - Example prompts for empty state
 * - Auto-scroll to bottom when new messages arrive
 */
export default function ChatPage() {
  const {
    messages,
    streamingContent,
    isLoading,
    error,
    contextPosts,
    sendMessage,
    retry,
    clearMessages,
    embeddings,
    rateLimit,
  } = useChat({ autoInitialize: true });

  // Sidebar and drawer state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Ref for auto-scrolling
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive or streaming content updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  // Handle source citation clicks
  const handleSourceClick = useCallback(() => {
    // Open context drawer on mobile, otherwise the sidebar shows it
    if (window.innerWidth < 1024) {
      setDrawerOpen(true);
    }
  }, []);

  // Handle sending example prompts
  const handleExamplePrompt = useCallback(
    (prompt: string) => {
      if (!embeddings.isReady || isLoading) return;
      sendMessage(prompt);
    },
    [embeddings.isReady, isLoading, sendMessage]
  );

  // Show embedding loader if model is not ready
  const showEmbeddingLoader = !embeddings.isReady && embeddings.isLoading;

  // Determine if we have any messages or streaming content to show
  const hasContent = messages.length > 0 || streamingContent;

  return (
    <div className="flex h-[calc(100vh-8rem)] overflow-hidden">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="border-b px-4 py-3 flex items-center justify-between shrink-0">
          <div>
            <h1 className="text-lg font-semibold">Chat</h1>
            <p className="text-sm text-muted-foreground">
              Ask questions about your bookmarks
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Context toggle for mobile */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDrawerOpen(true)}
              className="lg:hidden"
            >
              <BookmarkIcon className="h-4 w-4 mr-1" />
              <Badge variant="secondary" className="text-xs">
                {contextPosts.length}
              </Badge>
            </Button>

            {/* Clear chat button */}
            {hasContent && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearMessages}
                disabled={isLoading}
              >
                Clear
              </Button>
            )}
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {/* Loading state - embedding model */}
          {showEmbeddingLoader && (
            <div className="flex items-center justify-center h-full">
              <EmbeddingLoader
                progress={embeddings.progress}
                status={embeddings.progressStatus}
              />
            </div>
          )}

          {/* Empty state */}
          {!showEmbeddingLoader && !hasContent && (
            <EmptyState
              prompts={EXAMPLE_PROMPTS}
              onPromptClick={handleExamplePrompt}
              disabled={!embeddings.isReady || isLoading}
            />
          )}

          {/* Messages */}
          {!showEmbeddingLoader && hasContent && (
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onSourceClick={handleSourceClick}
                />
              ))}

              {/* Streaming message */}
              {streamingContent && (
                <StreamingMessage content={streamingContent} />
              )}

              {/* Error state */}
              {error && (
                <div className="flex items-center justify-center">
                  <div className="p-4 rounded-lg bg-destructive/10 text-destructive max-w-md text-center">
                    <p className="font-medium">Something went wrong</p>
                    <p className="text-sm mt-1">{error}</p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={retry}
                      className="mt-3"
                      disabled={isLoading}
                    >
                      Retry
                    </Button>
                  </div>
                </div>
              )}

              {/* Scroll anchor */}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="border-t">
          {/* Rate limit indicator */}
          <div className="px-4 py-2 flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {rateLimit.canSend ? (
                <>
                  {rateLimit.remaining} message{rateLimit.remaining !== 1 ? "s" : ""} remaining this hour
                </>
              ) : (
                <>
                  Rate limit reached. Resets in{" "}
                  {rateLimit.resetInMs ? formatResetTime(rateLimit.resetInMs) : "soon"}
                </>
              )}
            </span>
            <span className="text-xs">
              {rateLimit.remaining}/{rateLimit.limit}
            </span>
          </div>
          <ChatInput
            onSend={sendMessage}
            disabled={!embeddings.isReady || !rateLimit.canSend}
            isLoading={isLoading}
            placeholder={
              !rateLimit.canSend
                ? "Rate limit reached. Please wait..."
                : embeddings.isReady
                  ? "Ask about your bookmarks..."
                  : "Loading model..."
            }
          />
        </div>
      </div>

      {/* Desktop sidebar */}
      <ContextSidebar
        contextPosts={contextPosts}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((prev) => !prev)}
        className="hidden lg:flex"
      />

      {/* Mobile drawer */}
      <ContextDrawer
        contextPosts={contextPosts}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}

/**
 * Empty state component with example prompts
 */
interface EmptyStateProps {
  prompts: string[];
  onPromptClick: (prompt: string) => void;
  disabled?: boolean;
}

function EmptyState({ prompts, onPromptClick, disabled }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
        <ChatBubbleIcon className="h-8 w-8 text-primary" />
      </div>

      <h2 className="text-xl font-semibold mb-2">Start a conversation</h2>
      <p className="text-muted-foreground mb-6 max-w-md">
        Ask questions about your bookmarked content. The AI will search through
        your posts and provide answers with citations.
      </p>

      <div className="flex flex-col gap-2 w-full max-w-md">
        <p className="text-sm font-medium text-muted-foreground mb-1">
          Try asking:
        </p>
        {prompts.map((prompt, index) => (
          <Button
            key={index}
            variant="outline"
            className="justify-start text-left h-auto py-3 px-4"
            onClick={() => onPromptClick(prompt)}
            disabled={disabled}
          >
            <span className="text-sm">{prompt}</span>
          </Button>
        ))}
      </div>
    </div>
  );
}

/**
 * Chat bubble icon for empty state
 */
function ChatBubbleIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

/**
 * Bookmark icon for context button
 */
function BookmarkIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z" />
    </svg>
  );
}
