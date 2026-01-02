"use client";

import { useState, useCallback, useRef, useEffect, type KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  /** Handler for sending messages */
  onSend: (message: string) => void;
  /** Whether the input should be disabled (e.g., while streaming) */
  disabled?: boolean;
  /** Whether a message is currently being processed */
  isLoading?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Additional class names */
  className?: string;
}

/**
 * Chat input component with auto-resizing textarea and send button.
 *
 * Features:
 * - Auto-resizing textarea that grows with content
 * - Enter to send (Shift+Enter for new line)
 * - Disabled state while streaming
 * - Send button with loading state
 */
export function ChatInput({
  onSend,
  disabled = false,
  isLoading = false,
  placeholder = "Ask about your bookmarks...",
  className,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = "auto";
    // Set height to scrollHeight (with max limit handled by CSS)
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }, [value]);

  const handleSubmit = useCallback(() => {
    const trimmedValue = value.trim();
    if (!trimmedValue || disabled || isLoading) return;

    onSend(trimmedValue);
    setValue("");

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, disabled, isLoading, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Enter without Shift sends the message
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  const isDisabled = disabled || isLoading;
  const canSend = value.trim().length > 0 && !isDisabled;

  return (
    <div
      className={cn(
        "flex items-end gap-2 p-3 border-t bg-background",
        className
      )}
    >
      <div className="relative flex-1">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isDisabled}
          placeholder={placeholder}
          rows={1}
          className={cn(
            "w-full resize-none rounded-xl border border-input bg-background px-4 py-3",
            "text-sm placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "max-h-[200px] min-h-[44px]"
          )}
          aria-label="Chat message input"
        />
      </div>

      <Button
        type="button"
        onClick={handleSubmit}
        disabled={!canSend}
        size="icon"
        className={cn(
          "shrink-0 rounded-xl h-11 w-11",
          "transition-all duration-200",
          canSend && "hover:scale-105"
        )}
        aria-label={isLoading ? "Sending..." : "Send message"}
      >
        {isLoading ? (
          <LoadingSpinner className="h-5 w-5" />
        ) : (
          <SendIcon className="h-5 w-5" />
        )}
      </Button>
    </div>
  );
}

/**
 * Send icon for the send button
 */
function SendIcon({ className }: { className?: string }) {
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
      <path d="m22 2-7 20-4-9-9-4Z" />
      <path d="M22 2 11 13" />
    </svg>
  );
}

/**
 * Loading spinner for the send button
 */
function LoadingSpinner({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("animate-spin", className)}
      aria-hidden="true"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}
