"use client";

import Link from "next/link";
import type { GraphPostSummary } from "@/lib/queries/graph";

interface PostListProps {
  posts: GraphPostSummary[];
  isLoading?: boolean;
}

/**
 * Compact post list for displaying in the graph sidebar
 */
export function PostList({ posts, isLoading }: PostListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse">
            <div className="h-4 bg-muted rounded w-24 mb-1" />
            <div className="h-3 bg-muted rounded w-full mb-1" />
            <div className="h-3 bg-muted rounded w-3/4" />
          </div>
        ))}
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No posts found</p>
    );
  }

  return (
    <div className="space-y-3">
      {posts.map((post) => (
        <PostItem key={post.id} post={post} />
      ))}
    </div>
  );
}

interface PostItemProps {
  post: GraphPostSummary;
}

function PostItem({ post }: PostItemProps) {
  // Truncate content to ~100 chars
  const truncatedContent = post.content
    ? post.content.length > 100
      ? post.content.slice(0, 100) + "..."
      : post.content
    : "No content";

  // Format date
  const formattedDate = new Date(post.archived_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <Link
      href={`/posts/${post.id}`}
      className="block p-2 -mx-2 rounded-md hover:bg-muted/50 transition-colors"
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium text-muted-foreground">
          {post.author_handle ? `@${post.author_handle}` : "Unknown author"}
        </span>
        <span className="text-xs text-muted-foreground">{formattedDate}</span>
      </div>
      <p className="text-sm text-foreground line-clamp-2">{truncatedContent}</p>
    </Link>
  );
}
