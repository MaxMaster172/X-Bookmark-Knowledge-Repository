"use client";

import { PostCard } from "./PostCard";
import { Skeleton } from "@/components/ui/skeleton";
import type { PostWithRelations, PostWithMedia, SearchResult } from "@/types/database";

// Type for posts that can be displayed - requires at least post_media
type DisplayablePost = PostWithRelations | PostWithMedia | SearchResult;

interface PostFeedProps {
  posts: DisplayablePost[];
  showSimilarity?: boolean;
  compact?: boolean;
  isLoading?: boolean;
  emptyMessage?: string;
}

function PostCardSkeleton({ compact = false }: { compact?: boolean }) {
  return (
    <div className="p-4 rounded-lg border">
      <div className="flex items-start gap-3 mb-3">
        <Skeleton className="w-10 h-10 rounded-full" />
        <div className="flex-1">
          <Skeleton className="h-4 w-32 mb-1" />
          <Skeleton className="h-3 w-48" />
        </div>
      </div>
      <Skeleton className={compact ? "h-16" : "h-24"} />
      <div className="flex gap-2 mt-3">
        <Skeleton className="h-5 w-16" />
        <Skeleton className="h-5 w-20" />
        <Skeleton className="h-5 w-14" />
      </div>
    </div>
  );
}

export function PostFeed({
  posts,
  showSimilarity = false,
  compact = false,
  isLoading = false,
  emptyMessage = "No posts found",
}: PostFeedProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <PostCardSkeleton key={i} compact={compact} />
        ))}
      </div>
    );
  }

  if (!posts || posts.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {posts.map((post) => (
        <PostCard
          key={post.id}
          post={post}
          showSimilarity={showSimilarity}
          compact={compact}
        />
      ))}
    </div>
  );
}
