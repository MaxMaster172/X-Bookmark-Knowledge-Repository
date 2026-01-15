import Link from "next/link";
import { getGraphData, getGraphCategories } from "@/lib/queries/graph";
import { GraphClient } from "./GraphClient";

export const dynamic = "force-dynamic";

export default async function GraphPage() {
  const [graphData, categories] = await Promise.all([
    getGraphData(),
    getGraphCategories(),
  ]);

  const entityCount = graphData.nodes.filter((n) => n.type === "entity").length;
  const thesisCount = graphData.nodes.filter((n) => n.type === "thesis").length;

  return (
    <main className="min-h-screen py-8">
      <div className="container max-w-6xl mx-auto px-4">
        {/* Back Link */}
        <Link
          href="/"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-6"
        >
          &larr; Back to home
        </Link>

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Knowledge Graph</h1>
          <p className="text-muted-foreground">
            {entityCount} entities and {thesisCount} theses connected by{" "}
            {graphData.links.length} relationships
          </p>
        </div>

        {/* Graph Visualization */}
        <GraphClient data={graphData} categories={categories} />
      </div>
    </main>
  );
}
