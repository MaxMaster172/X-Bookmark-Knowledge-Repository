import { getSupabaseClient } from "@/lib/supabase/client";
import type {
  Entity,
  EntityCategory,
  EntityWithCategory,
  EntityWithRelations,
  Post,
  Thesis,
} from "@/types/database";

/**
 * Get all entities with their categories
 */
export async function getEntities(): Promise<EntityWithCategory[]> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from("entities")
    .select(
      `
      *,
      category:entity_categories (*)
    `
    )
    .order("name", { ascending: true });

  if (error) {
    console.error("Error fetching entities:", error);
    throw error;
  }

  return (data as unknown as EntityWithCategory[]) ?? [];
}

/**
 * Get entities grouped by category
 */
export async function getEntitiesByCategory(): Promise<
  Array<{
    category: EntityCategory | null;
    entities: EntityWithCategory[];
  }>
> {
  const entities = await getEntities();

  // Group by category
  const groups = new Map<
    string | null,
    { category: EntityCategory | null; entities: EntityWithCategory[] }
  >();

  for (const entity of entities) {
    const key = entity.category?.id ?? null;
    if (!groups.has(key)) {
      groups.set(key, {
        category: entity.category,
        entities: [],
      });
    }
    groups.get(key)!.entities.push(entity);
  }

  // Sort groups: named categories first, then uncategorized
  return Array.from(groups.values()).sort((a, b) => {
    if (!a.category && b.category) return 1;
    if (a.category && !b.category) return -1;
    return (a.category?.name ?? "").localeCompare(b.category?.name ?? "");
  });
}

/**
 * Get all entity categories
 */
export async function getEntityCategories(): Promise<EntityCategory[]> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from("entity_categories")
    .select("*")
    .order("name", { ascending: true });

  if (error) {
    console.error("Error fetching entity categories:", error);
    throw error;
  }

  return data ?? [];
}

/**
 * Get a single entity by ID with all relations
 */
export async function getEntity(id: string): Promise<EntityWithRelations | null> {
  const supabase = getSupabaseClient();

  // Get entity with category
  const { data: entity, error: entityError } = await supabase
    .from("entities")
    .select(
      `
      *,
      category:entity_categories (*)
    `
    )
    .eq("id", id)
    .single();

  if (entityError) {
    if (entityError.code === "PGRST116") {
      return null;
    }
    console.error("Error fetching entity:", entityError);
    throw entityError;
  }

  if (!entity) {
    return null;
  }

  // Get related post IDs
  const { data: postLinks } = await supabase
    .from("post_entities" as never)
    .select("post_id")
    .eq("entity_id", id);

  const postLinkData = postLinks as Array<{ post_id: string }> | null;

  // Fetch posts if we have links
  let postEntities: Array<{ post: Post }> = [];
  if (postLinkData && postLinkData.length > 0) {
    const postIds = postLinkData.map((l) => l.post_id);
    const { data: posts } = await supabase
      .from("posts")
      .select("*")
      .in("id", postIds);

    postEntities = (posts as Post[] | null)?.map((post) => ({ post })) ?? [];
  }

  // Get related thesis IDs
  const { data: thesisLinks } = await supabase
    .from("entity_theses" as never)
    .select("thesis_id, role")
    .eq("entity_id", id);

  const thesisLinkData = thesisLinks as Array<{ thesis_id: string; role: string }> | null;

  // Fetch theses if we have links
  let entityTheses: Array<{ thesis: Thesis; role: string }> = [];
  if (thesisLinkData && thesisLinkData.length > 0) {
    const thesisIds = thesisLinkData.map((l) => l.thesis_id);
    const { data: theses } = await supabase
      .from("theses")
      .select("*")
      .in("id", thesisIds);

    entityTheses = (theses as Thesis[] | null)?.map((thesis) => ({
      thesis,
      role: thesisLinkData.find((l) => l.thesis_id === thesis.id)?.role ?? "subject",
    })) ?? [];
  }

  // Construct the full entity with relations
  const entityData = entity as unknown as EntityWithCategory;

  return {
    ...entityData,
    post_entities: postEntities,
    entity_theses: entityTheses,
  } as EntityWithRelations;
}

/**
 * Get posts for a specific entity
 */
export async function getEntityPosts(entityId: string): Promise<Post[]> {
  const supabase = getSupabaseClient();

  // First get post IDs linked to this entity
  // Using explicit typing since junction tables aren't in generated types
  const { data: links, error: linksError } = await supabase
    .from("post_entities" as never)
    .select("post_id")
    .eq("entity_id", entityId);

  if (linksError) {
    console.error("Error fetching entity post links:", linksError);
    throw linksError;
  }

  const linkData = links as Array<{ post_id: string }> | null;
  if (!linkData || linkData.length === 0) {
    return [];
  }

  // Then fetch the actual posts
  const postIds = linkData.map((l) => l.post_id);
  const { data: posts, error: postsError } = await supabase
    .from("posts")
    .select("*")
    .in("id", postIds);

  if (postsError) {
    console.error("Error fetching entity posts:", postsError);
    throw postsError;
  }

  return (posts as Post[]) ?? [];
}

/**
 * Count total entities
 */
export async function countEntities(): Promise<number> {
  const supabase = getSupabaseClient();

  const { count, error } = await supabase
    .from("entities")
    .select("id", { count: "exact", head: true });

  if (error) {
    console.error("Error counting entities:", error);
    return 0;
  }

  return count ?? 0;
}

/**
 * Get entity post counts
 */
export async function getEntityPostCounts(): Promise<Map<string, number>> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from("post_entities" as never)
    .select("entity_id");

  if (error) {
    console.error("Error fetching entity post counts:", error);
    return new Map();
  }

  const rows = data as Array<{ entity_id: string }> | null;
  const counts = new Map<string, number>();
  for (const row of rows ?? []) {
    counts.set(row.entity_id, (counts.get(row.entity_id) ?? 0) + 1);
  }

  return counts;
}
