"use client";

import { Badge } from "@/components/ui/badge";
import type { GraphNode } from "@/types/graph";
import { useGraphTheme } from "./useGraphTheme";

interface SelectedNodeInfoProps {
  node: GraphNode;
}

/**
 * Displays detailed information about the selected node
 */
export function SelectedNodeInfo({ node }: SelectedNodeInfoProps) {
  const { getNodeColor } = useGraphTheme();
  const nodeColor = getNodeColor(node);

  return (
    <div className="space-y-3">
      {/* Node type badge */}
      <div className="flex items-center gap-2">
        <div
          className="w-3 h-3 rounded-full shrink-0"
          style={{ backgroundColor: nodeColor }}
        />
        <Badge variant="secondary" className="capitalize">
          {node.type}
        </Badge>
        {node.category && (
          <Badge variant="outline" className="text-xs">
            {node.category}
          </Badge>
        )}
      </div>

      {/* Node name/label */}
      <h3 className="text-lg font-semibold leading-tight">{node.label}</h3>

      {/* Connection count could be added here if we had edge count per node */}
    </div>
  );
}
