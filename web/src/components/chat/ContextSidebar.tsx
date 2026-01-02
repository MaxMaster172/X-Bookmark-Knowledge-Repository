"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ContextPost } from "@/types/chat";

interface ContextSidebarProps {
  /** Context posts being used for the current conversation */
  contextPosts: ContextPost[];
  /** Whether the sidebar is collapsed */
  collapsed?: boolean;
  /** Handler for toggling collapsed state */
  onToggle?: () => void;
  /** Additional class names */
  className?: string;
}

/**
 * Sidebar showing the posts being used as context for the RAG chat.
 *
 * Features:
 * - Collapsible on smaller screens
 * - Shows post preview with author, date, and similarity score
 * - Links to full post view
 */
export function ContextSidebar({
  contextPosts,
  collapsed = false,
  onToggle,
  className,
}: ContextSidebarProps) {
  if (collapsed) {
    return (
      <div className={cn("w-10 border-l bg-muted/30 p-2", className)}>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={onToggle}
          className="w-6 h-6"
          aria-label="Expand context sidebar"
        >
          <ChevronLeftIcon className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "w-72 border-l bg-muted/30 flex flex-col overflow-hidden",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b">
        <h2 className="text-sm font-semibold">Context</h2>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-xs">
            {contextPosts.length}
          </Badge>
          {onToggle && (
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={onToggle}
              className="w-6 h-6"
              aria-label="Collapse context sidebar"
            >
              <ChevronRightIcon className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Context posts list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {contextPosts.length === 0 ? (
          <EmptyState />
        ) : (
          contextPosts.map((post) => (
            <ContextPostCard key={post.id} post={post} />
          ))
        )}
      </div>
    </div>
  );
}

interface ContextPostCardProps {
  post: ContextPost;
}

/**
 * Card showing a single context post in the sidebar.
 */
function ContextPostCard({ post }: ContextPostCardProps) {
  return (
    <Card className="py-0 gap-0">
      <CardHeader className="p-3 pb-1">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <Badge variant="outline" className="text-xs mb-1">
              [{post.index}]
            </Badge>
            <CardTitle className="text-xs font-medium truncate">
              {post.authorHandle ? `@${post.authorHandle}` : "Unknown"}
            </CardTitle>
          </div>
          {post.similarity !== undefined && (
            <Badge
              variant="secondary"
              className="text-xs shrink-0"
              title="Similarity score"
            >
              {Math.round(post.similarity * 100)}%
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-3 pt-0">
        <p className="text-xs text-muted-foreground line-clamp-3">
          {post.content || "(No content)"}
        </p>
        {post.postedAt && (
          <p className="text-xs text-muted-foreground/70 mt-1">
            {formatDate(post.postedAt)}
          </p>
        )}
        <Link
          href={`/post/${post.id}`}
          className="inline-block text-xs text-primary hover:underline mt-2"
        >
          View post
        </Link>
      </CardContent>
    </Card>
  );
}

/**
 * Empty state when no context posts are loaded.
 */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-32 text-center text-muted-foreground">
      <BookmarkIcon className="h-8 w-8 mb-2 opacity-50" />
      <p className="text-xs">No context loaded</p>
      <p className="text-xs opacity-70">
        Ask a question to retrieve relevant posts
      </p>
    </div>
  );
}

/**
 * Format a date string for display
 */
function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return "Unknown date";
  }
}

/**
 * Chevron left icon
 */
function ChevronLeftIcon({ className }: { className?: string }) {
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
      <path d="m15 18-6-6 6-6" />
    </svg>
  );
}

/**
 * Chevron right icon
 */
function ChevronRightIcon({ className }: { className?: string }) {
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
      <path d="m9 18 6-6-6-6" />
    </svg>
  );
}

/**
 * Bookmark icon for empty state
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

/**
 * Mobile-friendly version with a sheet/drawer instead of sidebar
 */
interface ContextDrawerProps {
  /** Context posts being used for the current conversation */
  contextPosts: ContextPost[];
  /** Whether the drawer is open */
  isOpen: boolean;
  /** Handler for closing the drawer */
  onClose: () => void;
}

export function ContextDrawer({
  contextPosts,
  isOpen,
  onClose,
}: ContextDrawerProps) {
  const [isClosing, setIsClosing] = useState(false);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      setIsClosing(false);
      onClose();
    }, 200);
  };

  if (!isOpen && !isClosing) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          "fixed inset-0 bg-black/50 z-40 transition-opacity duration-200",
          isClosing ? "opacity-0" : "opacity-100"
        )}
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        className={cn(
          "fixed right-0 top-0 bottom-0 w-80 max-w-[85vw] bg-background z-50",
          "border-l shadow-lg",
          "transform transition-transform duration-200",
          isClosing ? "translate-x-full" : "translate-x-0"
        )}
        role="dialog"
        aria-modal="true"
        aria-label="Context posts"
      >
        <ContextSidebar
          contextPosts={contextPosts}
          className="h-full border-l-0"
          onToggle={handleClose}
        />
      </div>
    </>
  );
}
