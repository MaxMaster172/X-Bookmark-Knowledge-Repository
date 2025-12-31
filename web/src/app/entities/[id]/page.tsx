import { notFound } from "next/navigation";
import Link from "next/link";
import { getEntity } from "@/lib/queries/entities";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PostFeed } from "@/components/posts";
import { ThesisBadge } from "@/components/theses";
import type { PostWithRelations } from "@/types/database";

export const dynamic = "force-dynamic";

interface EntityPageProps {
  params: Promise<{ id: string }>;
}

export default async function EntityPage({ params }: EntityPageProps) {
  const { id } = await params;
  const entity = await getEntity(id);

  if (!entity) {
    notFound();
  }

  // Transform post_entities to PostWithRelations format
  const posts: PostWithRelations[] = entity.post_entities.map((pe) => ({
    ...pe.post,
    post_media: [],
    post_entities: [],
    post_theses: [],
  }));

  return (
    <main className="min-h-screen py-8">
      <div className="container max-w-4xl mx-auto px-4">
        {/* Back Link */}
        <Link
          href="/entities"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-6"
        >
          &larr; Back to entities
        </Link>

        {/* Entity Card */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <h1 className="text-3xl font-bold mb-2">{entity.name}</h1>
                {entity.category && (
                  <Badge variant="secondary" className="mb-3">
                    {entity.category.name}
                  </Badge>
                )}
              </div>
            </div>

            {entity.description && (
              <p className="text-muted-foreground mb-4">{entity.description}</p>
            )}

            {entity.aliases && entity.aliases.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-4 border-t">
                <span className="text-sm text-muted-foreground">Also known as:</span>
                {entity.aliases.map((alias) => (
                  <Badge key={alias} variant="outline">
                    {alias}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Related Theses */}
        {entity.entity_theses && entity.entity_theses.length > 0 && (
          <section className="mb-8">
            <h2 className="font-semibold text-xl mb-4">
              Related Theses ({entity.entity_theses.length})
            </h2>
            <div className="flex flex-wrap gap-3">
              {entity.entity_theses.map((et) => (
                <div key={et.thesis.id} className="flex items-center gap-2">
                  <ThesisBadge thesis={et.thesis} showCategory />
                  <Badge variant="outline" className="text-xs">
                    {et.role}
                  </Badge>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Posts */}
        <section>
          <h2 className="font-semibold text-xl mb-4">
            Posts ({posts.length})
          </h2>
          <PostFeed
            posts={posts}
            compact
            emptyMessage="No posts linked to this entity yet"
          />
        </section>
      </div>
    </main>
  );
}
