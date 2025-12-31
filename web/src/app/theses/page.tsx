import Link from "next/link";
import { getTheses } from "@/lib/queries/theses";
import { SynthesisCard } from "@/components/theses";
import { Badge } from "@/components/ui/badge";

export const dynamic = "force-dynamic";

export default async function ThesesPage() {
  const theses = await getTheses();

  // Group by category
  const byCategory = new Map<string, typeof theses>();
  theses.forEach((thesis) => {
    const cat = thesis.category ?? "uncategorized";
    const existing = byCategory.get(cat) || [];
    existing.push(thesis);
    byCategory.set(cat, existing);
  });

  const categories = Array.from(byCategory.keys()).sort();

  return (
    <main className="min-h-screen py-8">
      <div className="container max-w-4xl mx-auto px-4">
        {/* Back Link */}
        <Link
          href="/"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-6"
        >
          &larr; Back to home
        </Link>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold">Theses</h1>
            <Badge variant="secondary">{theses.length}</Badge>
          </div>
          <p className="text-muted-foreground">
            Synthesized knowledge themes from your bookmarks
          </p>
        </div>

        {/* Empty State */}
        {theses.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <p>No theses created yet</p>
            <p className="text-sm mt-2">
              Theses will be automatically detected and synthesized in a future update
            </p>
          </div>
        ) : (
          /* Theses by Category */
          <div className="space-y-12">
            {categories.map((category) => {
              const categoryTheses = byCategory.get(category) || [];
              return (
                <section key={category}>
                  <div className="flex items-center gap-3 mb-4">
                    <h2 className="font-semibold text-xl capitalize">
                      {category === "uncategorized" ? "Other" : category}
                    </h2>
                    <Badge variant="outline">{categoryTheses.length}</Badge>
                  </div>
                  <div className="grid md:grid-cols-2 gap-4">
                    {categoryTheses.map((thesis) => (
                      <Link key={thesis.id} href={`/theses/${thesis.id}`}>
                        <SynthesisCard thesis={thesis} className="h-full hover:shadow-md transition-shadow" />
                      </Link>
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
