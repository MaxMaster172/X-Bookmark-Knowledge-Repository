"use client";

import dynamic from "next/dynamic";
import type { GraphData } from "@/types/graph";
import { Skeleton } from "@/components/ui/skeleton";

interface GraphClientProps {
  data: GraphData;
  categories: Array<{ id: string; name: string }>;
}

// Loading skeleton for the graph
function GraphSkeleton() {
  return (
    <div className="w-full h-[600px] rounded-lg border bg-muted/30 flex items-center justify-center">
      <div className="text-center space-y-4">
        <Skeleton className="h-8 w-48 mx-auto" />
        <p className="text-sm text-muted-foreground">Loading graph...</p>
      </div>
    </div>
  );
}

// Dynamic import to avoid SSR issues with canvas
const KnowledgeGraph = dynamic(
  () => import("@/components/graph/KnowledgeGraph").then((mod) => mod.KnowledgeGraph),
  {
    ssr: false,
    loading: () => <GraphSkeleton />,
  }
);

export function GraphClient({ data, categories }: GraphClientProps) {
  return <KnowledgeGraph data={data} categories={categories} />;
}
