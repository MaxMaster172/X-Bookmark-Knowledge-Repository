import { getSupabaseClient } from "@/lib/supabase/client";
import type { Stats } from "@/types/database";

/**
 * Get overall statistics for the knowledge base
 */
export async function getStats(): Promise<Stats> {
  const supabase = getSupabaseClient();

  // Run counts in parallel
  const [postsResult, entitiesResult, thesesResult, authorsResult] =
    await Promise.all([
      supabase.from("posts").select("id", { count: "exact", head: true }),
      supabase.from("entities").select("id", { count: "exact", head: true }),
      supabase.from("theses").select("id", { count: "exact", head: true }),
      supabase
        .from("posts")
        .select("author_handle")
        .not("author_handle", "is", null),
    ]);

  // Count unique authors
  const authorsData = authorsResult.data as Array<{ author_handle: string | null }> | null;
  const uniqueAuthors = new Set(
    authorsData?.map((p) => p.author_handle).filter(Boolean) ?? []
  ).size;

  return {
    total_posts: postsResult.count ?? 0,
    total_entities: entitiesResult.count ?? 0,
    total_theses: thesesResult.count ?? 0,
    unique_authors: uniqueAuthors,
  };
}
