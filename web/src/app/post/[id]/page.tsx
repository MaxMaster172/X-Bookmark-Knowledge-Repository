import { notFound } from "next/navigation";
import Link from "next/link";
import { getPost } from "@/lib/queries/posts";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PostMedia } from "@/components/posts";
import { EntityBadge } from "@/components/entities";
import { ThesisBadge } from "@/components/theses";
import { MessageSquare } from "lucide-react";

export const dynamic = "force-dynamic";

interface PostPageProps {
  params: Promise<{ id: string }>;
}

function formatDate(dateString: string | null): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export default async function PostPage({ params }: PostPageProps) {
  const { id } = await params;
  const post = await getPost(id);

  if (!post) {
    notFound();
  }

  return (
    <main className="min-h-screen py-8">
      <div className="container max-w-4xl mx-auto px-4">
        {/* Navigation */}
        <div className="flex items-center justify-between mb-6">
          <Link
            href="/"
            className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
          >
            &larr; Back to home
          </Link>
          <Link href={`/chat?postId=${id}`}>
            <Button variant="outline" size="sm">
              <MessageSquare className="h-4 w-4 mr-2" />
              Chat about this
            </Button>
          </Link>
        </div>

        {/* Post Card */}
        <Card className="mb-8">
          <CardContent className="p-6">
            {/* Header */}
            <div className="flex items-start gap-4 mb-4">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium text-lg">
                {post.author_handle?.charAt(0).toUpperCase() ?? "?"}
              </div>
              <div className="flex-1">
                <p className="font-semibold text-lg">
                  {post.author_name ?? post.author_handle ?? "Unknown"}
                </p>
                <p className="text-muted-foreground">
                  @{post.author_handle ?? "unknown"}
                </p>
              </div>
              <a
                href={post.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline text-sm"
              >
                View on X
              </a>
            </div>

            {/* Content */}
            <div className="prose prose-lg dark:prose-invert max-w-none mb-6">
              <p className="whitespace-pre-wrap">{post.content}</p>
            </div>

            {/* Quoted Post */}
            {post.quoted_text && (
              <div className="p-4 rounded-lg bg-muted/50 border mb-6">
                <p className="text-sm text-muted-foreground mb-2">
                  Quoting @{post.quoted_author}
                </p>
                <p className="whitespace-pre-wrap">{post.quoted_text}</p>
                {post.quoted_url && (
                  <a
                    href={post.quoted_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline text-sm mt-2 inline-block"
                  >
                    View quoted post
                  </a>
                )}
              </div>
            )}

            {/* Media */}
            {post.post_media && post.post_media.length > 0 && (
              <div className="mb-6">
                <PostMedia media={post.post_media} />
              </div>
            )}

            {/* Metadata */}
            <div className="flex flex-wrap gap-4 text-sm text-muted-foreground border-t pt-4">
              {post.posted_at && (
                <span>Posted: {formatDate(post.posted_at)}</span>
              )}
              <span>Archived: {formatDate(post.archived_at)}</span>
              <span>via {post.archived_via}</span>
            </div>
          </CardContent>
        </Card>

        {/* Tags */}
        {post.tags && post.tags.length > 0 && (
          <section className="mb-8">
            <h2 className="font-semibold mb-3">Tags</h2>
            <div className="flex flex-wrap gap-2">
              {post.tags.map((tag) => (
                <Badge key={tag} variant="outline">
                  #{tag}
                </Badge>
              ))}
            </div>
          </section>
        )}

        {/* Topics */}
        {post.topics && post.topics.length > 0 && (
          <section className="mb-8">
            <h2 className="font-semibold mb-3">Topics</h2>
            <div className="flex flex-wrap gap-2">
              {post.topics.map((topic) => (
                <Badge key={topic} variant="secondary">
                  {topic}
                </Badge>
              ))}
            </div>
          </section>
        )}

        {/* Importance & Notes */}
        {(post.importance || post.notes) && (
          <section className="mb-8">
            {post.importance && (
              <div className="mb-4">
                <h2 className="font-semibold mb-2">Importance</h2>
                <Badge>{post.importance}</Badge>
              </div>
            )}
            {post.notes && (
              <div>
                <h2 className="font-semibold mb-2">Notes</h2>
                <p className="text-muted-foreground whitespace-pre-wrap">
                  {post.notes}
                </p>
              </div>
            )}
          </section>
        )}

        {/* Entities */}
        {post.post_entities && post.post_entities.length > 0 && (
          <section className="mb-8">
            <h2 className="font-semibold mb-3">
              Entities ({post.post_entities.length})
            </h2>
            <div className="flex flex-wrap gap-2">
              {post.post_entities.map((pe) => (
                <EntityBadge
                  key={pe.entity.id}
                  entity={pe.entity}
                  confidence={pe.confidence}
                  showCategory
                />
              ))}
            </div>
          </section>
        )}

        {/* Theses */}
        {post.post_theses && post.post_theses.length > 0 && (
          <section className="mb-8">
            <h2 className="font-semibold mb-3">
              Related Theses ({post.post_theses.length})
            </h2>
            <div className="space-y-4">
              {post.post_theses.map((pt) => (
                <div key={pt.thesis.id} className="flex items-start gap-4">
                  <ThesisBadge
                    thesis={pt.thesis}
                    contribution={pt.contribution}
                    showCategory
                  />
                  {pt.contribution && (
                    <p className="text-sm text-muted-foreground flex-1">
                      {pt.contribution}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
