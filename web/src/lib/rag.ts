/**
 * RAG (Retrieval Augmented Generation) utilities for the chat interface.
 *
 * This module handles:
 * - Building context prompts from retrieved posts
 * - Parsing source citations from Claude's responses
 */

import type { Post, SearchResult } from "@/types/database";

/**
 * Represents a post with context for RAG
 */
export interface ContextPost {
  id: string;
  index: number; // 1-based index for citation references
  content: string;
  authorHandle: string | null;
  postedAt: string | null;
  url: string;
  similarity?: number;
}

/**
 * Represents a parsed source citation from Claude's response
 */
export interface SourceCitation {
  index: number; // 1-based index matching the context posts
  postId: string;
  url: string;
  authorHandle: string | null;
}

/**
 * Build context posts array from search results
 */
export function buildContextPosts(
  results: SearchResult[] | Post[],
  startIndex: number = 1
): ContextPost[] {
  return results.map((post, i) => ({
    id: post.id,
    index: startIndex + i,
    content: post.content || "",
    authorHandle: post.author_handle,
    postedAt: post.posted_at,
    url: post.url,
    similarity: "similarity" in post ? post.similarity : undefined,
  }));
}

/**
 * Format a date for display in the context
 */
function formatDate(dateStr: string | null): string {
  if (!dateStr) return "Unknown date";
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "Unknown date";
  }
}

/**
 * Build the RAG system prompt with context posts
 */
export function buildSystemPrompt(contextPosts: ContextPost[]): string {
  if (contextPosts.length === 0) {
    return `You are a helpful assistant. The user is asking about their bookmarked knowledge, but no relevant bookmarks were found for this query. Let them know you couldn't find relevant bookmarks, and offer to help with general knowledge or suggest they try a different search query.`;
  }

  const postsContext = contextPosts
    .map((post) => {
      const author = post.authorHandle ? `@${post.authorHandle}` : "Unknown";
      const date = formatDate(post.postedAt);
      const content = post.content || "(No content)";

      return `[Post ${post.index}] ${author} (${date}):
"${content}"
URL: ${post.url}`;
    })
    .join("\n\n");

  return `You are a helpful assistant that answers questions based on the user's bookmarked knowledge. You have access to the following bookmarked posts:

${postsContext}

When answering, cite your sources using [1], [2], etc. to reference the posts above.
If you cannot find relevant information in the bookmarks, say so honestly.
Keep your responses concise and focused on what the bookmarks contain.`;
}

/**
 * Parse source citations from Claude's response text.
 *
 * Matches patterns like [1], [2], [3] in the response and maps them
 * to the corresponding context posts.
 */
export function parseSourceCitations(
  responseText: string,
  contextPosts: ContextPost[]
): SourceCitation[] {
  // Find all citation patterns [1], [2], etc.
  const citationPattern = /\[(\d+)\]/g;
  const citedIndices = new Set<number>();

  let match: RegExpExecArray | null;
  while ((match = citationPattern.exec(responseText)) !== null) {
    const index = parseInt(match[1], 10);
    if (index > 0 && index <= contextPosts.length) {
      citedIndices.add(index);
    }
  }

  // Map cited indices to source citations
  const citations: SourceCitation[] = [];
  for (const index of citedIndices) {
    const post = contextPosts.find((p) => p.index === index);
    if (post) {
      citations.push({
        index,
        postId: post.id,
        url: post.url,
        authorHandle: post.authorHandle,
      });
    }
  }

  // Sort by index
  return citations.sort((a, b) => a.index - b.index);
}

/**
 * Build context posts from specific post IDs
 * Used when user manually adds posts to context
 */
export function buildContextFromPosts(
  posts: Post[],
  startIndex: number = 1
): ContextPost[] {
  return posts.map((post, i) => ({
    id: post.id,
    index: startIndex + i,
    content: post.content || "",
    authorHandle: post.author_handle,
    postedAt: post.posted_at,
    url: post.url,
  }));
}

/**
 * Truncate content if it exceeds max length
 * Used to prevent context from getting too long
 */
export function truncateContent(content: string, maxLength: number = 1000): string {
  if (content.length <= maxLength) return content;
  return content.slice(0, maxLength - 3) + "...";
}

/**
 * Calculate estimated token count for context
 * Rough estimate: 1 token ~= 4 characters
 */
export function estimateTokenCount(text: string): number {
  return Math.ceil(text.length / 4);
}

/**
 * Limit context posts to stay within token budget
 */
export function limitContextByTokens(
  contextPosts: ContextPost[],
  maxTokens: number = 4000
): ContextPost[] {
  let totalTokens = 0;
  const limitedPosts: ContextPost[] = [];

  for (const post of contextPosts) {
    const postTokens = estimateTokenCount(post.content);
    if (totalTokens + postTokens > maxTokens) break;
    totalTokens += postTokens;
    limitedPosts.push(post);
  }

  return limitedPosts;
}
