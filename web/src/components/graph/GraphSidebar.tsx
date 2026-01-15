"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type { GraphNode } from "@/types/graph";
import { getNodePosts, type GraphPostSummary } from "@/lib/queries/graph";
import { SelectedNodeInfo } from "./SelectedNodeInfo";
import { PostList } from "./PostList";

interface GraphSidebarProps {
  selectedNode: GraphNode | null;
  onClose: () => void;
}

/**
 * Sidebar panel that shows details about the selected node and its associated posts
 */
export function GraphSidebar({ selectedNode, onClose }: GraphSidebarProps) {
  const [posts, setPosts] = useState<GraphPostSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch posts when selected node changes
  useEffect(() => {
    if (!selectedNode) {
      setPosts([]);
      return;
    }

    const nodeId = selectedNode.entityId ?? selectedNode.thesisId;
    if (!nodeId) {
      setPosts([]);
      return;
    }

    async function fetchPosts() {
      setIsLoading(true);
      try {
        const fetchedPosts = await getNodePosts(selectedNode!.type, nodeId!);
        setPosts(fetchedPosts);
      } catch (error) {
        console.error("Error fetching node posts:", error);
        setPosts([]);
      } finally {
        setIsLoading(false);
      }
    }

    fetchPosts();
  }, [selectedNode]);

  if (!selectedNode) {
    return null;
  }

  return (
    <Card className="w-80 h-full flex flex-col shrink-0">
      <CardHeader className="py-4 px-4 flex flex-row items-start justify-between space-y-0">
        <SelectedNodeInfo node={selectedNode} />
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={onClose}
          className="shrink-0 -mt-1 -mr-2"
          aria-label="Close sidebar"
        >
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>

      <Separator />

      <CardContent className="flex-1 overflow-y-auto py-4 px-4">
        <h4 className="text-sm font-medium mb-3">
          Related Posts {!isLoading && `(${posts.length})`}
        </h4>
        <PostList posts={posts} isLoading={isLoading} />
      </CardContent>
    </Card>
  );
}
