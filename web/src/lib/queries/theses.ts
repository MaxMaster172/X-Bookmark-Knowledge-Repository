import { getSupabaseClient } from "@/lib/supabase/client";
import type { Post, Thesis, ThesisWithRelations, Entity, EntityCategory } from "@/types/database";

/**
 * Get all theses
 */
export async function getTheses(): Promise<Thesis[]> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from("theses")
    .select("*")
    .order("name", { ascending: true });

  if (error) {
    console.error("Error fetching theses:", error);
    throw error;
  }

  return (data as Thesis[]) ?? [];
}

/**
 * Get theses grouped by category
 */
export async function getThesesByCategory(): Promise<
  Record<string, Thesis[]>
> {
  const theses = await getTheses();

  const groups: Record<string, Thesis[]> = {};

  for (const thesis of theses) {
    const category = thesis.category ?? "uncategorized";
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(thesis);
  }

  return groups;
}

/**
 * Get a single thesis by ID with all relations
 */
export async function getThesis(id: string): Promise<ThesisWithRelations | null> {
  const supabase = getSupabaseClient();

  // Get thesis
  const { data: thesis, error: thesisError } = await supabase
    .from("theses")
    .select("*")
    .eq("id", id)
    .single();

  if (thesisError) {
    if (thesisError.code === "PGRST116") {
      return null;
    }
    console.error("Error fetching thesis:", thesisError);
    throw thesisError;
  }

  if (!thesis) {
    return null;
  }

  // Get related post IDs
  const { data: postLinks } = await supabase
    .from("post_theses" as never)
    .select("post_id, contribution")
    .eq("thesis_id", id);

  const postLinkData = postLinks as Array<{ post_id: string; contribution: string | null }> | null;

  // Fetch posts if we have links
  let postTheses: Array<{ post: Post; contribution: string | null }> = [];
  if (postLinkData && postLinkData.length > 0) {
    const postIds = postLinkData.map((l) => l.post_id);
    const { data: posts } = await supabase
      .from("posts")
      .select("*")
      .in("id", postIds);

    postTheses = (posts as Post[] | null)?.map((post) => ({
      post,
      contribution: postLinkData.find((l) => l.post_id === post.id)?.contribution ?? null,
    })) ?? [];
  }

  // Get related entity IDs
  const { data: entityLinks } = await supabase
    .from("entity_theses" as never)
    .select("entity_id, role")
    .eq("thesis_id", id);

  const entityLinkData = entityLinks as Array<{ entity_id: string; role: string }> | null;

  // Fetch entities if we have links
  let entityTheses: Array<{ entity: Entity & { category: EntityCategory | null }; role: string }> = [];
  if (entityLinkData && entityLinkData.length > 0) {
    const entityIds = entityLinkData.map((l) => l.entity_id);
    const { data: entities } = await supabase
      .from("entities")
      .select(`*, category:entity_categories (*)`)
      .in("id", entityIds);

    entityTheses = (entities as Array<Entity & { category: EntityCategory | null }> | null)?.map((entity) => ({
      entity,
      role: entityLinkData.find((l) => l.entity_id === entity.id)?.role ?? "subject",
    })) ?? [];
  }

  // Get related theses (both directions)
  const { data: relatedA } = await supabase
    .from("thesis_relationships" as never)
    .select("thesis_b_id, relationship_type")
    .eq("thesis_a_id", id);

  const { data: relatedB } = await supabase
    .from("thesis_relationships" as never)
    .select("thesis_a_id, relationship_type")
    .eq("thesis_b_id", id);

  const relatedAData = relatedA as Array<{ thesis_b_id: string; relationship_type: string | null }> | null;
  const relatedBData = relatedB as Array<{ thesis_a_id: string; relationship_type: string | null }> | null;

  // Fetch related theses
  const relatedIds = [
    ...(relatedAData?.map((r) => r.thesis_b_id) ?? []),
    ...(relatedBData?.map((r) => r.thesis_a_id) ?? []),
  ];

  let relatedTheses: Array<{ thesis: Thesis; relationship_type: string | null }> = [];
  if (relatedIds.length > 0) {
    const { data: related } = await supabase
      .from("theses")
      .select("*")
      .in("id", relatedIds);

    const getRelType = (thesisId: string): string | null => {
      const fromA = relatedAData?.find((r) => r.thesis_b_id === thesisId);
      if (fromA) return fromA.relationship_type;
      const fromB = relatedBData?.find((r) => r.thesis_a_id === thesisId);
      return fromB?.relationship_type ?? null;
    };

    relatedTheses = (related as Thesis[] | null)?.map((t) => ({
      thesis: t,
      relationship_type: getRelType(t.id),
    })) ?? [];
  }

  const thesisData = thesis as Thesis;

  return {
    ...thesisData,
    post_theses: postTheses,
    entity_theses: entityTheses,
    related_theses: relatedTheses,
  } as ThesisWithRelations;
}

/**
 * Get posts for a specific thesis
 */
export async function getThesisPosts(
  thesisId: string
): Promise<Array<Post & { contribution: string | null }>> {
  const supabase = getSupabaseClient();

  // Get post IDs and contributions
  const { data: links, error: linksError } = await supabase
    .from("post_theses" as never)
    .select("post_id, contribution")
    .eq("thesis_id", thesisId);

  if (linksError) {
    console.error("Error fetching thesis post links:", linksError);
    throw linksError;
  }

  const linkData = links as Array<{ post_id: string; contribution: string | null }> | null;
  if (!linkData || linkData.length === 0) {
    return [];
  }

  // Fetch posts
  const postIds = linkData.map((l) => l.post_id);
  const { data: posts, error: postsError } = await supabase
    .from("posts")
    .select("*")
    .in("id", postIds);

  if (postsError) {
    console.error("Error fetching thesis posts:", postsError);
    throw postsError;
  }

  return (posts as Post[] | null)?.map((post) => ({
    ...post,
    contribution: linkData.find((l) => l.post_id === post.id)?.contribution ?? null,
  })) ?? [];
}

/**
 * Count total theses
 */
export async function countTheses(): Promise<number> {
  const supabase = getSupabaseClient();

  const { count, error } = await supabase
    .from("theses")
    .select("id", { count: "exact", head: true });

  if (error) {
    console.error("Error counting theses:", error);
    return 0;
  }

  return count ?? 0;
}

/**
 * Get thesis post counts
 */
export async function getThesisPostCounts(): Promise<Map<string, number>> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from("post_theses" as never)
    .select("thesis_id");

  if (error) {
    console.error("Error fetching thesis post counts:", error);
    return new Map();
  }

  const rows = data as Array<{ thesis_id: string }> | null;
  const counts = new Map<string, number>();
  for (const row of rows ?? []) {
    counts.set(row.thesis_id, (counts.get(row.thesis_id) ?? 0) + 1);
  }

  return counts;
}

/**
 * Get thesis categories with counts
 */
export async function getThesisCategories(): Promise<
  Array<{ category: string; count: number }>
> {
  const theses = await getTheses();

  const counts = new Map<string, number>();
  for (const thesis of theses) {
    const cat = thesis.category ?? "uncategorized";
    counts.set(cat, (counts.get(cat) ?? 0) + 1);
  }

  return Array.from(counts.entries())
    .map(([category, count]) => ({ category, count }))
    .sort((a, b) => b.count - a.count);
}
