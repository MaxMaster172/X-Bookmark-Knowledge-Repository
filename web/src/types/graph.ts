export type NodeType = "entity" | "thesis";

export interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  category?: string;
  categoryId?: string;
  size: number;
  entityId?: string;
  thesisId?: string;
  // Runtime properties added by force-graph
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: "entity-thesis";
  role?: string;
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphEdge[];
}
