import { getSupabaseClient } from "@/lib/supabase/client";
import type { Entity, EntityCategory, Thesis } from "@/types/database";
import type { GraphData, GraphNode, GraphEdge } from "@/types/graph";

/**
 * Get graph data with entities and theses as nodes, connected by entity_theses edges
 */
export async function getGraphData(): Promise<GraphData> {
  const supabase = getSupabaseClient();

  // Fetch all data in parallel
  const [entitiesResult, thesesResult, edgesResult, categoriesResult] = await Promise.all([
    supabase
      .from("entities")
      .select("id, name, category_id")
      .order("name", { ascending: true }),
    supabase
      .from("theses")
      .select("id, name, category")
      .order("name", { ascending: true }),
    supabase
      .from("entity_theses" as never)
      .select("entity_id, thesis_id, role"),
    supabase
      .from("entity_categories")
      .select("id, name"),
  ]);

  if (entitiesResult.error) {
    console.error("Error fetching entities for graph:", entitiesResult.error);
    throw entitiesResult.error;
  }

  if (thesesResult.error) {
    console.error("Error fetching theses for graph:", thesesResult.error);
    throw thesesResult.error;
  }

  if (edgesResult.error) {
    console.error("Error fetching entity_theses for graph:", edgesResult.error);
    throw edgesResult.error;
  }

  const entities = (entitiesResult.data as Array<Pick<Entity, "id" | "name" | "category_id">>) ?? [];
  const theses = (thesesResult.data as Array<Pick<Thesis, "id" | "name" | "category">>) ?? [];
  const edges = (edgesResult.data as Array<{ entity_id: string; thesis_id: string; role: string }>) ?? [];
  const categories = (categoriesResult.data as Array<Pick<EntityCategory, "id" | "name">>) ?? [];

  // Create category lookup
  const categoryMap = new Map<string, string>();
  for (const cat of categories) {
    categoryMap.set(cat.id, cat.name);
  }

  // Transform entities to nodes
  const entityNodes: GraphNode[] = entities.map((entity) => ({
    id: `entity-${entity.id}`,
    type: "entity" as const,
    label: entity.name,
    category: entity.category_id ? categoryMap.get(entity.category_id) : undefined,
    categoryId: entity.category_id ?? undefined,
    size: 4,
    entityId: entity.id,
  }));

  // Transform theses to nodes
  const thesisNodes: GraphNode[] = theses.map((thesis) => ({
    id: `thesis-${thesis.id}`,
    type: "thesis" as const,
    label: thesis.name,
    category: thesis.category ?? undefined,
    size: 8,
    thesisId: thesis.id,
  }));

  // Transform entity_theses to edges
  const graphEdges: GraphEdge[] = edges.map((edge) => ({
    source: `entity-${edge.entity_id}`,
    target: `thesis-${edge.thesis_id}`,
    type: "entity-thesis" as const,
    role: edge.role,
    weight: 1,
  }));

  return {
    nodes: [...entityNodes, ...thesisNodes],
    links: graphEdges,
  };
}

/**
 * Get unique entity categories for legend/filtering
 */
export async function getGraphCategories(): Promise<Array<{ id: string; name: string }>> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from("entity_categories")
    .select("id, name")
    .order("name", { ascending: true });

  if (error) {
    console.error("Error fetching graph categories:", error);
    throw error;
  }

  return (data as Array<{ id: string; name: string }>) ?? [];
}
