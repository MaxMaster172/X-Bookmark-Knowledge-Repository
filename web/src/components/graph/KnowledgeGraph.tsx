"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import type { GraphData, GraphNode } from "@/types/graph";
import { useGraphTheme } from "./useGraphTheme";
import { GraphLegend } from "./GraphLegend";
import { Card } from "@/components/ui/card";

interface KnowledgeGraphProps {
  data: GraphData;
  categories: Array<{ id: string; name: string }>;
}

export function KnowledgeGraph({ data, categories }: KnowledgeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const { getNodeColor, getLinkColor, getBackgroundColor } = useGraphTheme();

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

  // Center graph after initial render
  useEffect(() => {
    const timer = setTimeout(() => {
      graphRef.current?.zoomToFit(400, 50);
    }, 500);
    return () => clearTimeout(timer);
  }, [data]);

  // Custom node rendering
  const nodeCanvasObject = useCallback(
    (node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const label = node.label;
      const fontSize = node.type === "thesis" ? 12 / globalScale : 10 / globalScale;
      const nodeSize = node.type === "thesis" ? 8 : 4;

      // Draw node circle
      ctx.beginPath();
      ctx.arc(node.x ?? 0, node.y ?? 0, nodeSize, 0, 2 * Math.PI);
      ctx.fillStyle = getNodeColor(node);
      ctx.fill();

      // Draw border for thesis nodes
      if (node.type === "thesis") {
        ctx.strokeStyle = "rgba(0, 0, 0, 0.3)";
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }

      // Draw label if zoomed in enough
      if (globalScale > 0.7) {
        ctx.font = `${fontSize}px Sans-Serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = getNodeColor(node);
        ctx.fillText(label, node.x ?? 0, (node.y ?? 0) + nodeSize + fontSize);
      }
    },
    [getNodeColor]
  );

  // Node hover tooltip
  const nodeLabel = useCallback((node: GraphNode) => {
    const type = node.type === "thesis" ? "Thesis" : "Entity";
    const category = node.category ? ` (${node.category})` : "";
    return `${type}: ${node.label}${category}`;
  }, []);

  return (
    <Card className="relative overflow-hidden">
      <div
        ref={containerRef}
        className="w-full"
        style={{ height: dimensions.height, backgroundColor: getBackgroundColor() }}
      >
        <ForceGraph2D
          ref={graphRef}
          graphData={data}
          width={dimensions.width}
          height={dimensions.height}
          nodeId="id"
          nodeLabel={nodeLabel}
          nodeVal={(node) => (node as GraphNode).size}
          nodeCanvasObject={nodeCanvasObject}
          nodePointerAreaPaint={(node, color, ctx) => {
            const nodeSize = (node as GraphNode).type === "thesis" ? 8 : 4;
            ctx.beginPath();
            ctx.arc(node.x ?? 0, node.y ?? 0, nodeSize + 2, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
          }}
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
}
