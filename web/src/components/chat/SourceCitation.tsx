"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Source } from "@/types/chat";

interface SourceCitationProps {
  /** The source to display */
  source: Source;
  /** Optional click handler (defaults to navigating to source URL) */
  onClick?: (source: Source) => void;
  /** Whether the citation is inline (within message) or standalone */
  inline?: boolean;
  /** Additional class names */
  className?: string;
}

/**
 * Inline citation badge that links to the source post.
 *
 * Displays as [1], [2], etc. and is clickable to navigate to the post.
 * Used within ChatMessage to render citations in assistant responses.
 */
export function SourceCitation({
  source,
  onClick,
  inline = true,
  className,
}: SourceCitationProps) {
  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      e.preventDefault();
      onClick(source);
    }
  };

  if (inline) {
    return (
      <Link
        href={`/post/${source.postId}`}
        onClick={handleClick}
        className={cn(
          "inline-flex items-center justify-center",
          "text-xs font-medium",
          "text-primary hover:text-primary/80",
          "hover:underline underline-offset-2",
          "transition-colors cursor-pointer",
          className
        )}
        title={`Source: ${source.authorHandle ? `@${source.authorHandle}` : "Unknown"}`}
      >
        [{source.index}]
      </Link>
    );
  }

  // Standalone variant - shows more info
  return (
    <Badge
      asChild
      variant="secondary"
      className={cn(
        "cursor-pointer hover:bg-secondary/80 transition-colors",
        className
      )}
    >
      <Link
        href={`/post/${source.postId}`}
        onClick={handleClick}
        title={source.title || undefined}
      >
        <span className="font-semibold">[{source.index}]</span>
        {source.authorHandle && (
          <span className="ml-1 text-muted-foreground">
            @{source.authorHandle}
          </span>
        )}
      </Link>
    </Badge>
  );
}

interface SourceListProps {
  /** Array of sources to display */
  sources: Source[];
  /** Click handler for source clicks */
  onSourceClick?: (source: Source) => void;
  /** Additional class names */
  className?: string;
}

/**
 * Display a list of source citations.
 * Used at the end of assistant messages or in the ContextSidebar.
 */
export function SourceList({
  sources,
  onSourceClick,
  className,
}: SourceListProps) {
  if (sources.length === 0) return null;

  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {sources.map((source) => (
        <SourceCitation
          key={source.postId}
          source={source}
          onClick={onSourceClick}
          inline={false}
        />
      ))}
    </div>
  );
}
