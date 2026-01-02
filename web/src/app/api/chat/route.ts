import { NextRequest } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { createServerClient } from "@/lib/supabase/server";
import {
  buildContextPosts,
  buildSystemPrompt,
  limitContextByTokens,
  type ContextPost,
} from "@/lib/rag";
import type { Post, SearchResult } from "@/types/database";

/**
 * Chat message from the client
 */
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/**
 * Request body for the chat API
 */
interface ChatRequest {
  message: string;
  history: ChatMessage[];
  embedding?: number[]; // 384-dimensional embedding from client
  contextPostIds?: string[]; // Optional: specific post IDs to include
}

/**
 * Response format for streaming
 */
interface StreamChunk {
  type: "text" | "context" | "error" | "done";
  content?: string;
  contextPosts?: ContextPost[];
  error?: string;
}

/**
 * Create a streaming response with SSE format
 */
function createStreamResponse(stream: ReadableStream): Response {
  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}

/**
 * Format an SSE message
 */
function formatSSE(data: StreamChunk): string {
  return `data: ${JSON.stringify(data)}\n\n`;
}

/**
 * Search for relevant posts using vector similarity
 */
async function searchRelevantPosts(
  embedding: number[],
  threshold: number = 0.5,
  limit: number = 5
): Promise<SearchResult[]> {
  const supabase = createServerClient();

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

  // Get full post data
  const postIds = matches.map((m: { id: string }) => m.id);

  const { data: posts, error: postsError } = await supabase
    .from("posts")
    .select("*")
    .in("id", postIds);

  if (postsError) {
    console.error("Error fetching post details:", postsError);
    throw postsError;
  }

  // Merge similarity scores with post data
  const similarityMap = new Map<string, number>(
    matches.map((m: { id: string; similarity: number }) => [m.id, m.similarity])
  );

  const results: SearchResult[] = ((posts ?? []) as Post[]).map((post) => ({
    ...post,
    post_media: [],
    post_entities: [],
    post_theses: [],
    similarity: similarityMap.get(post.id) ?? 0,
  }));

  // Sort by similarity (highest first)
  results.sort((a, b) => b.similarity - a.similarity);

  return results;
}

/**
 * Fetch specific posts by their IDs
 */
async function fetchPostsByIds(postIds: string[]): Promise<Post[]> {
  if (postIds.length === 0) return [];

  const supabase = createServerClient();
  const { data, error } = await supabase
    .from("posts")
    .select("*")
    .in("id", postIds);

  if (error) {
    console.error("Error fetching posts by IDs:", error);
    throw error;
  }

  return (data as Post[]) ?? [];
}

export async function POST(request: NextRequest) {
  const encoder = new TextEncoder();

  // Create a readable stream for streaming response
  const stream = new ReadableStream({
    async start(controller) {
      try {
        // Parse request body
        const body: ChatRequest = await request.json();
        const { message, history, embedding, contextPostIds } = body;

        if (!message || typeof message !== "string") {
          controller.enqueue(
            encoder.encode(
              formatSSE({ type: "error", error: "Message is required" })
            )
          );
          controller.enqueue(encoder.encode(formatSSE({ type: "done" })));
          controller.close();
          return;
        }

        // Check for Anthropic API key
        const apiKey = process.env.ANTHROPIC_API_KEY;
        if (!apiKey) {
          controller.enqueue(
            encoder.encode(
              formatSSE({
                type: "error",
                error:
                  "ANTHROPIC_API_KEY is not configured. Please add it to your .env.local file.",
              })
            )
          );
          controller.enqueue(encoder.encode(formatSSE({ type: "done" })));
          controller.close();
          return;
        }

        // Build context from posts
        let contextPosts: ContextPost[] = [];

        try {
          // If specific post IDs are provided, use those
          if (contextPostIds && contextPostIds.length > 0) {
            const posts = await fetchPostsByIds(contextPostIds);
            contextPosts = buildContextPosts(posts);
          }
          // Otherwise, if an embedding is provided, search for relevant posts
          else if (embedding && Array.isArray(embedding)) {
            const searchResults = await searchRelevantPosts(embedding);
            contextPosts = buildContextPosts(searchResults);
          }

          // Limit context to token budget
          contextPosts = limitContextByTokens(contextPosts, 4000);
        } catch (error) {
          console.error("Error building context:", error);
          // Continue without context on error
        }

        // Send context posts to client
        controller.enqueue(
          encoder.encode(formatSSE({ type: "context", contextPosts }))
        );

        // Build system prompt with context
        const systemPrompt = buildSystemPrompt(contextPosts);

        // Convert history to Anthropic format, filtering out any empty messages
        const messages: { role: "user" | "assistant"; content: string }[] = [
          ...history
            .filter((msg) => msg.content && msg.content.trim().length > 0)
            .map((msg) => ({
              role: msg.role,
              content: msg.content,
            })),
          { role: "user" as const, content: message },
        ];

        // Ensure we have at least one message
        if (messages.length === 0) {
          controller.enqueue(
            encoder.encode(
              formatSSE({ type: "error", error: "No valid messages to send" })
            )
          );
          controller.enqueue(encoder.encode(formatSSE({ type: "done" })));
          controller.close();
          return;
        }

        // Create Anthropic client
        const anthropic = new Anthropic({ apiKey });

        // Stream response from Claude
        // Use claude-sonnet-4-20250514 (Claude Sonnet 4, not 4.5)
        const response = await anthropic.messages.stream({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1024,
          system: systemPrompt,
          messages,
        });

        // Stream text chunks to client
        for await (const event of response) {
          if (
            event.type === "content_block_delta" &&
            event.delta.type === "text_delta"
          ) {
            controller.enqueue(
              encoder.encode(formatSSE({ type: "text", content: event.delta.text }))
            );
          }
        }

        // Signal completion
        controller.enqueue(encoder.encode(formatSSE({ type: "done" })));
        controller.close();
      } catch (error) {
        console.error("Chat API error:", error);

        const errorMessage =
          error instanceof Error ? error.message : "Unknown error occurred";

        controller.enqueue(
          encoder.encode(formatSSE({ type: "error", error: errorMessage }))
        );
        controller.enqueue(encoder.encode(formatSSE({ type: "done" })));
        controller.close();
      }
    },
  });

  return createStreamResponse(stream);
}
