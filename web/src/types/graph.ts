export type NodeType = "entity" | "thesis" | "post";

export type EdgeType = "entity-thesis" | "entity-post" | "thesis-post";

export interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  category?: string;
  categoryId?: string;
  size: number;
  entityId?: string;
  thesisId?: string;
  postId?: string;
  parentNodeId?: string; // For post nodes, tracks which node they expanded from
  // Runtime properties added by force-graph
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: EdgeType;
  role?: string;
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphEdge[];
}
