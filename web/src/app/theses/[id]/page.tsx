import { notFound } from "next/navigation";
import Link from "next/link";
import { getThesis } from "@/lib/queries/theses";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PostFeed } from "@/components/posts";
import { EntityBadge } from "@/components/entities";
import { ThesisBadge, SynthesisCard } from "@/components/theses";
import type { PostWithRelations } from "@/types/database";

export const dynamic = "force-dynamic";

interface ThesisPageProps {
  params: Promise<{ id: string }>;
}

export default async function ThesisPage({ params }: ThesisPageProps) {
  const { id } = await params;
  const thesis = await getThesis(id);

  if (!thesis) {
    notFound();
  }

  // Transform post_theses to PostWithRelations format
  const posts: PostWithRelations[] = thesis.post_theses.map((pt) => ({
    ...pt.post,
    post_media: [],
    post_entities: [],
    post_theses: [],
  }));

  return (
    <main className="min-h-screen py-8">
      <div className="container max-w-4xl mx-auto px-4">
        {/* Back Link */}
        <Link
          href="/theses"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-6"
        >
          &larr; Back to theses
        </Link>

        {/* Thesis Header */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <h1 className="text-3xl font-bold mb-2">{thesis.name}</h1>
                {thesis.category && (
                  <Badge variant="secondary" className="mb-3 capitalize">
                    {thesis.category}
                  </Badge>
                )}
              </div>
            </div>

            {thesis.description && (
              <p className="text-muted-foreground">{thesis.description}</p>
            )}
          </CardContent>
        </Card>

        {/* Synthesis */}
        <section className="mb-8">
          <h2 className="font-semibold text-xl mb-4">Synthesis</h2>
          <SynthesisCard thesis={thesis} showFull />
        </section>

        {/* Related Entities */}
        {thesis.entity_theses && thesis.entity_theses.length > 0 && (
          <section className="mb-8">
            <h2 className="font-semibold text-xl mb-4">
              Related Entities ({thesis.entity_theses.length})
            </h2>
            <div className="flex flex-wrap gap-3">
              {thesis.entity_theses.map((et) => (
                <div key={et.entity.id} className="flex items-center gap-2">
                  <EntityBadge entity={et.entity} showCategory />
                  <Badge variant="outline" className="text-xs">
                    {et.role}
                  </Badge>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Related Theses */}
        {thesis.related_theses && thesis.related_theses.length > 0 && (
          <section className="mb-8">
            <h2 className="font-semibold text-xl mb-4">
              Related Theses ({thesis.related_theses.length})
            </h2>
            <div className="flex flex-wrap gap-3">
              {thesis.related_theses.map((rt) => (
                <div key={rt.thesis.id} className="flex items-center gap-2">
                  <ThesisBadge thesis={rt.thesis} showCategory />
                  {rt.relationship_type && (
                    <Badge variant="outline" className="text-xs">
                      {rt.relationship_type}
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Contributing Posts */}
        <section>
          <h2 className="font-semibold text-xl mb-4">
            Contributing Posts ({posts.length})
          </h2>
          <PostFeed
            posts={posts}
            compact
            emptyMessage="No posts linked to this thesis yet"
          />
        </section>
      </div>
    </main>
  );
}
