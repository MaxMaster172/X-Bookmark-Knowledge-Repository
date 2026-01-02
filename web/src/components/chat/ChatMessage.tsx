"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { SourceCitation, SourceList } from "./SourceCitation";
import type { Message, Source } from "@/types/chat";

interface ChatMessageProps {
  /** The message to display */
  message: Message;
  /** Whether the message is currently streaming */
  isStreaming?: boolean;
  /** Click handler for source citations */
  onSourceClick?: (source: Source) => void;
  /** Additional class names */
  className?: string;
}

/**
 * Parse message content and replace citation markers with interactive components.
 * Converts [1], [2], etc. into clickable SourceCitation components.
 */
function useRenderedContent(
  content: string,
  sources: Source[],
  onSourceClick?: (source: Source) => void
) {
  return useMemo(() => {
    if (!sources || sources.length === 0) {
      return <>{content}</>;
    }

    // Create a map of index to source for quick lookup
    const sourceMap = new Map(sources.map((s) => [s.index, s]));

    // Split by citation pattern but keep the delimiters
    const parts = content.split(/(\[\d+\])/g);

    return (
      <>
        {parts.map((part, i) => {
          // Check if this part is a citation
          const match = part.match(/^\[(\d+)\]$/);
          if (match) {
            const index = parseInt(match[1], 10);
            const source = sourceMap.get(index);
            if (source) {
              return (
                <SourceCitation
                  key={`citation-${i}-${index}`}
                  source={source}
                  onClick={onSourceClick}
                  inline
                />
              );
            }
          }
          // Regular text
          return <span key={`text-${i}`}>{part}</span>;
        })}
      </>
    );
  }, [content, sources, onSourceClick]);
}

/**
 * Chat message bubble component.
 *
 * - User messages: Right-aligned with blue background
 * - Assistant messages: Left-aligned with gray background
 * - Supports inline source citations that are clickable
 */
export function ChatMessage({
  message,
  isStreaming = false,
  onSourceClick,
  className,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const sources = message.sources || [];

  const renderedContent = useRenderedContent(
    message.content,
    sources,
    onSourceClick
  );

  return (
    <div
      className={cn(
        "flex w-full",
        isUser ? "justify-end" : "justify-start",
        className
      )}
    >
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-4 py-3",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted dark:bg-muted/50",
          isStreaming && "animate-pulse"
        )}
      >
        {/* Message content with inline citations */}
        <div
          className={cn(
            "text-sm leading-relaxed whitespace-pre-wrap break-words",
            isUser ? "text-primary-foreground" : "text-foreground"
          )}
        >
          {renderedContent}
          {isStreaming && (
            <span className="inline-block w-1.5 h-4 ml-0.5 bg-current animate-blink" />
          )}
        </div>

        {/* Source citations list (only for assistant messages with sources) */}
        {!isUser && sources.length > 0 && !isStreaming && (
          <div className="mt-3 pt-2 border-t border-border/50">
            <p className="text-xs text-muted-foreground mb-1.5">Sources:</p>
            <SourceList sources={sources} onSourceClick={onSourceClick} />
          </div>
        )}

        {/* Timestamp */}
        <div
          className={cn(
            "text-xs mt-1",
            isUser ? "text-primary-foreground/70" : "text-muted-foreground"
          )}
        >
          {formatTime(message.createdAt)}
        </div>
      </div>
    </div>
  );
}

/**
 * Format a date for message timestamp display
 */
function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

interface StreamingMessageProps {
  /** The content currently being streamed */
  content: string;
  /** Additional class names */
  className?: string;
}

/**
 * Streaming message component for displaying in-progress responses.
 * Shows a minimal assistant message with the streaming content and a cursor.
 */
export function StreamingMessage({
  content,
  className,
}: StreamingMessageProps) {
  if (!content) return null;

  return (
    <div className={cn("flex w-full justify-start", className)}>
      <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-muted dark:bg-muted/50">
        <div className="text-sm leading-relaxed whitespace-pre-wrap break-words text-foreground">
          {content}
          <span className="inline-block w-1.5 h-4 ml-0.5 bg-foreground animate-blink" />
        </div>
      </div>
    </div>
  );
}
