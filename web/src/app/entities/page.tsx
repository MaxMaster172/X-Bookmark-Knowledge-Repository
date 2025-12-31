import Link from "next/link";
import { getEntities, getEntityCategories } from "@/lib/queries/entities";
import { EntityCard } from "@/components/entities";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

export const dynamic = "force-dynamic";

export default async function EntitiesPage() {
  const [entities, categories] = await Promise.all([
    getEntities(),
    getEntityCategories(),
  ]);

  // Group entities by category
  const entityByCategory = new Map<string, typeof entities>();
  const uncategorized: typeof entities = [];

  entities.forEach((entity) => {
    if (entity.category_id) {
      const existing = entityByCategory.get(entity.category_id) || [];
      existing.push(entity);
      entityByCategory.set(entity.category_id, existing);
    } else {
      uncategorized.push(entity);
    }
  });

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
            <h1 className="text-3xl font-bold">Entities</h1>
            <Badge variant="secondary">{entities.length}</Badge>
          </div>
          <p className="text-muted-foreground">
            People, companies, products, and concepts mentioned in your bookmarks
          </p>
        </div>

        {/* Category Tabs */}
        {categories.length > 0 ? (
          <Tabs defaultValue="all" className="w-full">
            <TabsList className="w-full flex-wrap h-auto gap-2 bg-transparent">
              <TabsTrigger value="all" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                All ({entities.length})
              </TabsTrigger>
              {categories.map((category) => {
                const count = entityByCategory.get(category.id)?.length || 0;
                return (
                  <TabsTrigger
                    key={category.id}
                    value={category.id}
                    className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                  >
                    {category.name} ({count})
                  </TabsTrigger>
                );
              })}
              {uncategorized.length > 0 && (
                <TabsTrigger
                  value="uncategorized"
                  className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                >
                  Uncategorized ({uncategorized.length})
                </TabsTrigger>
              )}
            </TabsList>

            <TabsContent value="all" className="mt-6">
              <EntityGrid entities={entities} />
            </TabsContent>

            {categories.map((category) => (
              <TabsContent key={category.id} value={category.id} className="mt-6">
                <div className="mb-4">
                  {category.description && (
                    <p className="text-muted-foreground text-sm">
                      {category.description}
                    </p>
                  )}
                </div>
                <EntityGrid entities={entityByCategory.get(category.id) || []} />
              </TabsContent>
            ))}

            {uncategorized.length > 0 && (
              <TabsContent value="uncategorized" className="mt-6">
                <EntityGrid entities={uncategorized} />
              </TabsContent>
            )}
          </Tabs>
        ) : (
          <EntityGrid entities={entities} />
        )}
      </div>
    </main>
  );
}

function EntityGrid({
  entities,
}: {
  entities: Awaited<ReturnType<typeof getEntities>>;
}) {
  if (entities.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>No entities found in this category</p>
      </div>
    );
  }

  return (
    <div className="grid md:grid-cols-2 gap-4">
      {entities.map((entity) => (
        <EntityCard key={entity.id} entity={entity} />
      ))}
    </div>
  );
}
