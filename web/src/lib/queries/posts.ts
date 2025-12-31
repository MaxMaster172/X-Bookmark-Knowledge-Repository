import { getSupabaseClient } from "@/lib/supabase/client";
import type {
  Post,
  PostMedia,
  PostWithMedia,
  PostWithRelations,
  SearchResult,
} from "@/types/database";

/**
 * Get recent posts ordered by archived_at descending
 */
export async function getRecentPosts(limit = 10): Promise<PostWithMedia[]> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from("posts")
    .select(
      `
      *,
      post_media (*)
    `
    )
    .order("archived_at", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("Error fetching recent posts:", error);
    throw error;
  }

  return (data as PostWithMedia[]) ?? [];
}

/**
 * Get a single post by ID with all relations
 */
export async function getPost(id: string): Promise<PostWithRelations | null> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from("posts")
    .select(
      `
      *,
      post_media (*),
      post_entities (
        confidence,
        entity:entities (
          *,
          category:entity_categories (*)
        )
      ),
      post_theses (
        contribution,
        confidence,
        thesis:theses (*)
      )
    `
    )
    .eq("id", id)
    .single();

  if (error) {
    if (error.code === "PGRST116") {
      return null; // Not found
    }
    console.error("Error fetching post:", error);
    throw error;
  }

  return data as unknown as PostWithRelations;
}

/**
 * Get media items for a post
 */
export async function getPostMedia(postId: string): Promise<PostMedia[]> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from("post_media")
    .select("*")
    .eq("post_id", postId)
    .order("id", { ascending: true });

  if (error) {
    console.error("Error fetching post media:", error);
    throw error;
  }

  return data ?? [];
}

/**
 * Get similar posts using vector similarity
 * Requires the post to have an embedding
 */
export async function getSimilarPosts(
  postId: string,
  limit = 5
): Promise<Post[]> {
  const supabase = getSupabaseClient();

  // First get the post's embedding
  const { data: post, error: postError } = await supabase
    .from("posts")
    .select("embedding")
    .eq("id", postId)
    .single();

  const postData = post as { embedding: number[] | null } | null;
  if (postError || !postData?.embedding) {
    return [];
  }

  // Use match_posts RPC but exclude the current post
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const { data, error } = await (supabase as any).rpc("match_posts", {
    query_embedding: postData.embedding,
    match_threshold: 0.5,
    match_count: limit + 1, // Get one extra to exclude self
  });

  if (error) {
    console.error("Error fetching similar posts:", error);
    return [];
  }

  // Exclude the original post and get full post data
  const similarIds = data
    .filter((r: { id: string }) => r.id !== postId)
    .slice(0, limit)
    .map((r: { id: string }) => r.id);

  if (similarIds.length === 0) {
    return [];
  }

  const { data: posts } = await supabase
    .from("posts")
    .select("*")
    .in("id", similarIds);

  return (posts as Post[]) ?? [];
}

/**
 * Search posts using vector similarity
 * Embedding should be 384-dimensional (BGE model)
 */
export async function searchPosts(
  embedding: number[],
  threshold = 0.7,
  limit = 20
): Promise<SearchResult[]> {
  const supabase = getSupabaseClient();

  // Get matching post IDs with similarity scores
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const { data: matches, error: matchError } = await (supabase as any).rpc(
    "match_posts",
    {
      query_embedding: embedding,
      match_threshold: threshold,
      match_count: limit,
    }
  );

  if (matchError) {
    console.error("Error searching posts:", matchError);
    throw matchError;
  }

  if (!matches || matches.length === 0) {
    return [];
  }

  // Get full post data with relations
  const postIds = matches.map((m: { id: string }) => m.id);

  const { data: posts, error: postsError } = await supabase
    .from("posts")
    .select(
      `
      *,
      post_media (*),
      post_entities (
        confidence,
        entity:entities (
          *,
          category:entity_categories (*)
        )
      ),
      post_theses (
        contribution,
        confidence,
        thesis:theses (*)
      )
    `
    )
    .in("id", postIds);

  if (postsError) {
    console.error("Error fetching post details:", postsError);
    throw postsError;
  }

  // Merge similarity scores with post data
  const similarityMap = new Map<string, number>(
    matches.map((m: { id: string; similarity: number }) => [m.id, m.similarity])
  );

  // Cast posts to the expected type before mapping
  const postsData = (posts ?? []) as PostWithRelations[];

  const results: SearchResult[] = postsData.map((post) => {
    const similarity = similarityMap.get(post.id) ?? 0;
    return {
      ...post,
      similarity,
    };
  });

  // Sort by similarity (highest first)
  results.sort((a, b) => b.similarity - a.similarity);

  return results;
}

/**
 * Count total posts
 */
export async function countPosts(): Promise<number> {
  const supabase = getSupabaseClient();

  const { count, error } = await supabase
    .from("posts")
    .select("id", { count: "exact", head: true });

  if (error) {
    console.error("Error counting posts:", error);
    return 0;
  }

  return count ?? 0;
}

/**
 * Get unique authors with post counts
 */
export async function getAuthors(): Promise<
  Array<{ author_handle: string; count: number }>
> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from("posts")
    .select("author_handle")
    .not("author_handle", "is", null);

  if (error) {
    console.error("Error fetching authors:", error);
    return [];
  }

  // Count by author
  const rows = data as Array<{ author_handle: string | null }> | null;
  const counts = new Map<string, number>();
  for (const post of rows ?? []) {
    const handle = post.author_handle;
    if (handle) {
      counts.set(handle, (counts.get(handle) ?? 0) + 1);
    }
  }

  return Array.from(counts.entries())
    .map(([author_handle, count]) => ({ author_handle, count }))
    .sort((a, b) => b.count - a.count);
}
