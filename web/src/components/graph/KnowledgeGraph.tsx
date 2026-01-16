"use client";

import { useCallback, useEffect, useRef, useState, useImperativeHandle, forwardRef } from "react";
import ForceGraph2D from "react-force-graph-2d";
import type { GraphData, GraphNode } from "@/types/graph";
import { useGraphTheme } from "./useGraphTheme";
import { GraphLegend } from "./GraphLegend";
import { Card } from "@/components/ui/card";

interface KnowledgeGraphProps {
  data: GraphData;
  categories: Array<{ id: string; name: string }>;
  selectedNodeId?: string | null;
  onNodeClick?: (node: GraphNode) => void;
  visibleCategories?: Set<string> | null;
  expandedNodes?: Set<string>;
  isExpandLoading?: boolean;
}

/**
 * Graph control methods exposed via ref
 */
export interface KnowledgeGraphRef {
  zoomIn: () => void;
  zoomOut: () => void;
  resetZoom: () => void;
}

export const KnowledgeGraph = forwardRef<KnowledgeGraphRef, KnowledgeGraphProps>(
  function KnowledgeGraph({ data, categories, selectedNodeId, onNodeClick, visibleCategories, expandedNodes }, ref) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const { getNodeColor, getLinkColor, getBackgroundColor } = useGraphTheme();

  // Expose zoom control methods via ref
  useImperativeHandle(ref, () => ({
    zoomIn: () => {
      if (graphRef.current) {
        const currentZoom = graphRef.current.zoom();
        graphRef.current.zoom(currentZoom * 1.5, 300);
      }
    },
    zoomOut: () => {
      if (graphRef.current) {
        const currentZoom = graphRef.current.zoom();
        graphRef.current.zoom(currentZoom / 1.5, 300);
      }
    },
    resetZoom: () => {
      graphRef.current?.zoomToFit(400, 50);
    },
  }));

  // Filter nodes based on visible categories
  const filteredData = useCallback(() => {
    if (!visibleCategories || visibleCategories.size === 0) {
      return data;
    }

    // Filter nodes
    const filteredNodes = data.nodes.filter((node) => {
      // Always show theses
      if (node.type === "thesis") return true;
      // Always show post nodes (they are children of expanded nodes)
      if (node.type === "post") return true;
      // Show entities that match visible categories or have no category
      if (!node.categoryId) return true;
      return visibleCategories.has(node.categoryId);
    });

    // Filter links to only include links between visible nodes
    const visibleNodeIds = new Set(filteredNodes.map((n) => n.id));
    const filteredLinks = data.links.filter(
      (link) =>
        visibleNodeIds.has(typeof link.source === "string" ? link.source : (link.source as GraphNode).id) &&
        visibleNodeIds.has(typeof link.target === "string" ? link.target : (link.target as GraphNode).id)
    );

    return { nodes: filteredNodes, links: filteredLinks };
  }, [data, visibleCategories]);

  // Track container dimensions
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height: 600 });
      }
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  // Center graph on initial mount only (not on data changes from expansion)
  const initialZoomDone = useRef(false);
  useEffect(() => {
    if (initialZoomDone.current) return;
    const timer = setTimeout(() => {
      graphRef.current?.zoomToFit(400, 50);
      initialZoomDone.current = true;
    }, 500);
    return () => clearTimeout(timer);
  }, [data]);

  // Custom node rendering
  const nodeCanvasObject = useCallback(
    (node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const label = node.label;
      const isPost = node.type === "post";
      const isSelected = node.id === selectedNodeId;
      const isExpanded = expandedNodes?.has(node.id);

      // Base sizes
      const nodeSize = node.type === "thesis" ? 8 : isPost ? 3 : 4;
      const baseFontSize = node.type === "thesis" ? 12 : isPost ? 8 : 10;
      const fontSize = baseFontSize / globalScale;

      const x = node.x ?? 0;
      const y = node.y ?? 0;

      // Draw selection highlight ring
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(x, y, nodeSize + 4, 0, 2 * Math.PI);
        ctx.strokeStyle = "hsl(var(--primary))";
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Draw expanded node indicator ring
      if (isExpanded && !isPost) {
        ctx.beginPath();
        ctx.arc(x, y, nodeSize + 3, 0, 2 * Math.PI);
        ctx.strokeStyle = "hsl(var(--chart-2))";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 3]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Draw node circle
      ctx.beginPath();
      ctx.arc(x, y, nodeSize, 0, 2 * Math.PI);
      ctx.fillStyle = getNodeColor(node);
      ctx.fill();

      // Draw border for thesis nodes
      if (node.type === "thesis") {
        ctx.strokeStyle = "rgba(0, 0, 0, 0.3)";
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }

      // Draw dashed border for post nodes
      if (isPost) {
        ctx.strokeStyle = "rgba(128, 128, 128, 0.5)";
        ctx.lineWidth = 0.5;
        ctx.setLineDash([2, 2]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Draw label based on zoom threshold
      const labelZoomThreshold = isPost ? 1.2 : 0.7;
      const showLabel = globalScale > labelZoomThreshold || isSelected;

      if (showLabel) {
        ctx.font = `${isSelected ? "bold " : ""}${fontSize}px Sans-Serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = getNodeColor(node);
        ctx.fillText(label, x, y + nodeSize + fontSize);
      }
    },
    [getNodeColor, selectedNodeId, expandedNodes]
  );

  // Node hover tooltip
  const nodeLabel = useCallback((node: GraphNode) => {
    if (node.type === "post") {
      return `Post: ${node.label}`;
    }
    const type = node.type === "thesis" ? "Thesis" : "Entity";
    const category = node.category ? ` (${node.category})` : "";
    return `${type}: ${node.label}${category}`;
  }, []);

  // Handle node click
  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      onNodeClick?.(node);
    },
    [onNodeClick]
  );

  // Node pointer area for click detection
  const nodePointerAreaPaint = useCallback(
    (node: object, color: string, ctx: CanvasRenderingContext2D) => {
      const gNode = node as GraphNode;
      const nodeSize = gNode.type === "thesis" ? 8 : gNode.type === "post" ? 3 : 4;
      ctx.beginPath();
      ctx.arc(gNode.x ?? 0, gNode.y ?? 0, nodeSize + 2, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
    },
    []
  );

  return (
    <Card className="relative overflow-hidden">
      <div
        ref={containerRef}
        className="w-full"
        style={{ height: dimensions.height, backgroundColor: getBackgroundColor() }}
      >
        <ForceGraph2D
          ref={graphRef}
          graphData={filteredData()}
          width={dimensions.width}
          height={dimensions.height}
          nodeId="id"
          nodeLabel={nodeLabel}
          nodeVal={(node) => (node as GraphNode).size}
          nodeCanvasObject={nodeCanvasObject}
          nodePointerAreaPaint={nodePointerAreaPaint}
          onNodeClick={handleNodeClick}
          linkSource="source"
          linkTarget="target"
          linkColor={() => getLinkColor()}
          linkWidth={0.5}
          linkDirectionalParticles={0}
          cooldownTicks={100}
          warmupTicks={50}
          d3VelocityDecay={0.3}
          d3AlphaDecay={0.02}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          minZoom={0.2}
          maxZoom={8}
        />
      </div>
      <GraphLegend categories={categories} />
    </Card>
  );
});
