"use client";

import { useState, useCallback, useMemo } from "react";
import type { GraphData, GraphNode, GraphEdge } from "@/types/graph";
import { getNodePosts, type GraphPostSummary } from "@/lib/queries/graph";

export interface UseExpandableGraphProps {
  baseData: GraphData;
}

export interface UseExpandableGraphReturn {
  graphData: GraphData;
  expandedNodes: Set<string>;
  toggleNodeExpansion: (node: GraphNode) => Promise<void>;
  isLoading: boolean;
}

/**
 * Hook to manage expandable graph state.
 * When a node is expanded, its associated posts appear as child nodes around it.
 * When collapsed, the post nodes are removed.
 */
export function useExpandableGraph({ baseData }: UseExpandableGraphProps): UseExpandableGraphReturn {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [postNodes, setPostNodes] = useState<GraphNode[]>([]);
  const [postLinks, setPostLinks] = useState<GraphEdge[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Create post nodes positioned in a circle around the parent node
   */
  const createPostNodes = useCallback(
    (parentNode: GraphNode, posts: GraphPostSummary[]): { nodes: GraphNode[]; links: GraphEdge[] } => {
      const parentX = parentNode.x ?? 0;
      const parentY = parentNode.y ?? 0;
      const radius = 50; // Distance from parent

      const nodes: GraphNode[] = posts.map((post, index) => {
        // Position in a circle around the parent
        const angle = (2 * Math.PI * index) / posts.length;
        const x = parentX + radius * Math.cos(angle);
        const y = parentY + radius * Math.sin(angle);

        // Create truncated label from content
        const content = post.content ?? "";
        const label = content.length > 30 ? content.slice(0, 30) + "..." : content || post.author_handle || "Post";

        return {
          id: `post-${post.id}`,
          type: "post" as const,
          label,
          size: 2,
          postId: post.id,
          parentNodeId: parentNode.id,
          x,
          y,
        };
      });

      // Create links from parent to each post
      const edgeType = parentNode.type === "entity" ? "entity-post" : "thesis-post";
      const links: GraphEdge[] = nodes.map((postNode) => ({
        source: parentNode.id,
        target: postNode.id,
        type: edgeType as "entity-post" | "thesis-post",
        weight: 0.5,
      }));

      return { nodes, links };
    },
    []
  );

  /**
   * Toggle expansion state of a node
   */
  const toggleNodeExpansion = useCallback(
    async (node: GraphNode) => {
      // Only entity and thesis nodes can be expanded
      if (node.type === "post") return;

      const nodeId = node.id;
      const isExpanded = expandedNodes.has(nodeId);

      if (isExpanded) {
        // Collapse: Remove post nodes and links for this parent
        setExpandedNodes((prev) => {
          const next = new Set(prev);
          next.delete(nodeId);
          return next;
        });

        setPostNodes((prev) => prev.filter((n) => n.parentNodeId !== nodeId));
        setPostLinks((prev) => prev.filter((l) => l.source !== nodeId || l.type === "entity-thesis"));
      } else {
        // Expand: Fetch posts and create nodes
        setIsLoading(true);

        try {
          // Determine the node type and ID for fetching
          const nodeType = node.type as "entity" | "thesis";
          const actualId = nodeType === "entity" ? node.entityId : node.thesisId;

          if (!actualId) {
            console.error("No ID found for node:", node);
            return;
          }

          const posts = await getNodePosts(nodeType, actualId, 10); // Limit to 10 posts per node

          if (posts.length > 0) {
            const { nodes: newPostNodes, links: newPostLinks } = createPostNodes(node, posts);

            setExpandedNodes((prev) => {
              const next = new Set(prev);
              next.add(nodeId);
              return next;
            });

            setPostNodes((prev) => [...prev, ...newPostNodes]);
            setPostLinks((prev) => [...prev, ...newPostLinks]);
          }
        } catch (error) {
          console.error("Error fetching posts for node:", error);
        } finally {
          setIsLoading(false);
        }
      }
    },
    [expandedNodes, createPostNodes]
  );

  /**
   * Compute the final graph data by merging base data with post nodes
   */
  const graphData = useMemo<GraphData>(() => {
    return {
      nodes: [...baseData.nodes, ...postNodes],
      links: [...baseData.links, ...postLinks],
    };
  }, [baseData, postNodes, postLinks]);

  return {
    graphData,
    expandedNodes,
    toggleNodeExpansion,
    isLoading,
  };
}
