"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { EntityBadge } from "@/components/entities";
import { ThesisBadge } from "@/components/theses";
import { PostMedia } from "./PostMedia";
import type { PostWithRelations, PostWithMedia, SearchResult } from "@/types/database";

// Type for posts that can be displayed
type DisplayablePost = PostWithRelations | PostWithMedia | SearchResult;

interface PostCardProps {
  post: DisplayablePost;
  showSimilarity?: boolean;
  compact?: boolean;
}

function formatDate(dateString: string | null): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function truncateContent(content: string | null, maxLength: number = 280): string {
  if (!content) return "";
  if (content.length <= maxLength) return content;
  return content.slice(0, maxLength).trim() + "...";
}

export function PostCard({
  post,
  showSimilarity = false,
  compact = false,
}: PostCardProps) {
  const similarity = "similarity" in post ? (post as SearchResult).similarity : null;

  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardContent className={cn("p-4", compact && "p-3")}>
        {/* Header: Author + Date + Similarity */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            {/* Author avatar placeholder */}
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium">
              {post.author_handle?.charAt(0).toUpperCase() ?? "?"}
            </div>
            <div>
              <p className="font-medium leading-tight">
                {post.author_name ?? post.author_handle ?? "Unknown"}
              </p>
              <p className="text-sm text-muted-foreground">
                @{post.author_handle ?? "unknown"}
                {post.posted_at && (
                  <span className="mx-1">·</span>
                )}
                {post.posted_at && formatDate(post.posted_at)}
              </p>
            </div>
          </div>
          {showSimilarity && similarity !== null && (
            <Badge variant="secondary" className="text-xs">
              {Math.round(similarity * 100)}% match
            </Badge>
          )}
        </div>

        {/* Content */}
        <Link href={`/post/${post.id}`} className="block">
          <p
            className={cn(
              "text-foreground whitespace-pre-wrap",
              compact ? "text-sm line-clamp-3" : "line-clamp-6"
            )}
          >
            {compact ? truncateContent(post.content, 200) : post.content}
          </p>
        </Link>

        {/* Quoted post (if any) */}
        {post.quoted_text && (
          <div className="mt-3 p-3 rounded-lg bg-muted/50 border text-sm">
            <p className="text-muted-foreground mb-1">
              @{post.quoted_author ?? "quoted"}
            </p>
            <p className="line-clamp-2">{post.quoted_text}</p>
          </div>
        )}

        {/* Media */}
        {post.post_media && post.post_media.length > 0 && (
          <div className="mt-3">
            <PostMedia media={post.post_media} compact={compact} />
          </div>
        )}

        {/* Tags */}
        {post.tags && post.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {post.tags.map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                #{tag}
              </Badge>
            ))}
          </div>
        )}

        {/* Entities */}
        {"post_entities" in post && post.post_entities && post.post_entities.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {post.post_entities.slice(0, compact ? 3 : 10).map((pe) => (
              <EntityBadge
                key={pe.entity.id}
                entity={pe.entity}
                confidence={pe.confidence}
                size="sm"
              />
            ))}
            {compact && post.post_entities.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{post.post_entities.length - 3} more
              </Badge>
            )}
          </div>
        )}

        {/* Theses */}
        {"post_theses" in post && post.post_theses && post.post_theses.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {post.post_theses.slice(0, compact ? 2 : 5).map((pt) => (
              <ThesisBadge
                key={pt.thesis.id}
                thesis={pt.thesis}
                contribution={pt.contribution}
                confidence={pt.confidence}
                size="sm"
              />
            ))}
            {compact && post.post_theses.length > 2 && (
              <Badge variant="outline" className="text-xs">
                +{post.post_theses.length - 2} more
              </Badge>
            )}
          </div>
        )}

        {/* Footer: Importance + Notes indicator + Link to original */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t text-sm text-muted-foreground">
          <div className="flex items-center gap-3">
            {post.importance && (
              <span className="flex items-center gap-1">
                <span className="text-yellow-500">!</span>
                {post.importance}
              </span>
            )}
            {post.notes && (
              <span title={post.notes}>Has notes</span>
            )}
          </div>
          <a
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-primary transition-colors"
          >
            View on X
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
