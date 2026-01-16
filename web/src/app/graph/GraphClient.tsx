"use client";

import { useCallback, useRef, useState } from "react";
import dynamic from "next/dynamic";
import type { GraphData, GraphNode } from "@/types/graph";
import type { KnowledgeGraphRef } from "@/components/graph/KnowledgeGraph";
import { Skeleton } from "@/components/ui/skeleton";
import { GraphSidebar } from "@/components/graph/GraphSidebar";
import { GraphControls } from "@/components/graph/GraphControls";
import { GraphFilters } from "@/components/graph/GraphFilters";
import { ModeSwitcher, type GraphMode } from "@/components/graph/ModeSwitcher";
import { useExpandableGraph } from "@/components/graph/useExpandableGraph";

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
  const graphRef = useRef<KnowledgeGraphRef>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [mode, setMode] = useState<GraphMode>("panel");
  const [visibleCategories, setVisibleCategories] = useState<Set<string>>(new Set());

  // Expandable graph state management
  const { graphData, expandedNodes, toggleNodeExpansion, isLoading: isExpandLoading } = useExpandableGraph({
    baseData: data,
  });

  // Handle node click based on current mode
  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      if (mode === "panel") {
        // Toggle selection: deselect if clicking the same node
        setSelectedNode((prev) => (prev?.id === node.id ? null : node));
      } else if (mode === "expand") {
        // Post nodes: open in new tab
        if (node.type === "post" && node.postId) {
          window.open(`/post/${node.postId}`, "_blank");
          return;
        }
        // Entity/thesis nodes: toggle expansion (show/hide posts)
        toggleNodeExpansion(node);
      }
    },
    [mode, toggleNodeExpansion]
  );

  // Close sidebar
  const handleCloseSidebar = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    graphRef.current?.zoomIn();
  }, []);

  const handleZoomOut = useCallback(() => {
    graphRef.current?.zoomOut();
  }, []);

  const handleResetZoom = useCallback(() => {
    graphRef.current?.resetZoom();
  }, []);

  // Category filter handlers
  const handleToggleCategory = useCallback(
    (categoryId: string) => {
      setVisibleCategories((prev) => {
        const next = new Set(prev);
        // If we're in "show all" mode (empty set), switch to showing only this category
        if (prev.size === 0) {
          // Start with all categories except this one
          categories.forEach((cat) => {
            if (cat.id !== categoryId) {
              next.add(cat.id);
            }
          });
        } else if (next.has(categoryId)) {
          next.delete(categoryId);
        } else {
          next.add(categoryId);
        }
        return next;
      });
    },
    [categories]
  );

  const handleToggleAll = useCallback((showAll: boolean) => {
    if (showAll) {
      // Empty set means show all
      setVisibleCategories(new Set());
    } else {
      // Hide all - set to empty set that means "filter on"
      setVisibleCategories(new Set(["__none__"]));
    }
  }, []);

  return (
    <div className="space-y-4">
      {/* Mode switcher above graph */}
      <div className="flex items-center justify-between">
        <ModeSwitcher mode={mode} onModeChange={setMode} />
      </div>

      {/* Graph and sidebar layout */}
      <div className="flex gap-4">
        {/* Graph container */}
        <div className="flex-1 relative">
          <KnowledgeGraph
            ref={graphRef}
            data={graphData}
            categories={categories}
            selectedNodeId={selectedNode?.id}
            onNodeClick={handleNodeClick}
            visibleCategories={visibleCategories.size > 0 ? visibleCategories : null}
            expandedNodes={expandedNodes}
            isExpandLoading={isExpandLoading}
          />

          {/* Zoom controls overlay */}
          <GraphControls
            onZoomIn={handleZoomIn}
            onZoomOut={handleZoomOut}
            onResetZoom={handleResetZoom}
          />

          {/* Category filters overlay - positioned below legend on left */}
          {categories.length > 0 && (
            <div className="absolute bottom-4 left-4">
              <GraphFilters
                categories={categories}
                visibleCategories={visibleCategories}
                onToggleCategory={handleToggleCategory}
                onToggleAll={handleToggleAll}
              />
            </div>
          )}
        </div>

        {/* Sidebar for selected node */}
        {selectedNode && (
          <GraphSidebar selectedNode={selectedNode} onClose={handleCloseSidebar} />
        )}
      </div>
    </div>
  );
}
