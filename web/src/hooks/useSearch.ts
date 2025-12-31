"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useEmbeddings } from "./useEmbeddings";
import { searchPosts } from "@/lib/queries/posts";
import type { SearchResult } from "@/types/database";

export interface SearchState {
  query: string;
  results: SearchResult[];
  isSearching: boolean;
  isEmbedding: boolean;
  error: Error | null;
  hasSearched: boolean;
}

export interface UseSearchOptions {
  debounceMs?: number;
  threshold?: number;
  limit?: number;
  autoInitialize?: boolean;
}

export interface UseSearchReturn extends SearchState {
  search: (query: string) => Promise<void>;
  clearResults: () => void;
  embeddings: {
    isReady: boolean;
    isLoading: boolean;
    progress: number;
    progressStatus: string;
    initialize: () => Promise<void>;
  };
}

const DEFAULT_OPTIONS: Required<UseSearchOptions> = {
  debounceMs: 300,
  threshold: 0.5,
  limit: 20,
  autoInitialize: false,
};

/**
 * React hook for semantic search with Transformers.js embeddings
 *
 * Usage:
 * ```tsx
 * const { results, isSearching, search, embeddings } = useSearch();
 *
 * // Search
 * await search("AI investing strategies");
 *
 * // Check if model is ready
 * if (!embeddings.isReady && !embeddings.isLoading) {
 *   await embeddings.initialize();
 * }
 * ```
 */
export function useSearch(options: UseSearchOptions = {}): UseSearchReturn {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  const {
    isReady,
    isLoading: embeddingsLoading,
    progress,
    progressStatus,
    embed,
    initialize,
    error: embeddingError,
  } = useEmbeddings();

  const [state, setState] = useState<SearchState>({
    query: "",
    results: [],
    isSearching: false,
    isEmbedding: false,
    error: null,
    hasSearched: false,
  });

  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Auto-initialize if enabled
  useEffect(() => {
    if (opts.autoInitialize && !isReady && !embeddingsLoading) {
      initialize();
    }
  }, [opts.autoInitialize, isReady, embeddingsLoading, initialize]);

  // Search function
  const search = useCallback(
    async (query: string) => {
      // Clear any pending debounce
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      // Cancel any in-flight request
      if (abortRef.current) {
        abortRef.current.abort();
      }

      const trimmedQuery = query.trim();
      if (!trimmedQuery) {
        setState((prev) => ({
          ...prev,
          query: "",
          results: [],
          hasSearched: false,
        }));
        return;
      }

      setState((prev) => ({
        ...prev,
        query: trimmedQuery,
        isSearching: true,
        isEmbedding: true,
        error: null,
      }));

      // Debounce
      await new Promise<void>((resolve) => {
        debounceRef.current = setTimeout(resolve, opts.debounceMs);
      });

      try {
        // Generate embedding
        const embedding = await embed(trimmedQuery);

        setState((prev) => ({
          ...prev,
          isEmbedding: false,
        }));

        // Create abort controller for the search request
        abortRef.current = new AbortController();

        // Search Supabase
        const results = await searchPosts(embedding, opts.threshold, opts.limit);

        setState((prev) => ({
          ...prev,
          results,
          isSearching: false,
          hasSearched: true,
        }));
      } catch (error) {
        // Ignore abort errors
        if (error instanceof Error && error.name === "AbortError") {
          return;
        }

        setState((prev) => ({
          ...prev,
          isSearching: false,
          isEmbedding: false,
          error: error instanceof Error ? error : new Error(String(error)),
          hasSearched: true,
        }));
      }
    },
    [embed, opts.debounceMs, opts.threshold, opts.limit]
  );

  // Clear results
  const clearResults = useCallback(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    if (abortRef.current) {
      abortRef.current.abort();
    }
    setState({
      query: "",
      results: [],
      isSearching: false,
      isEmbedding: false,
      error: null,
      hasSearched: false,
    });
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, []);

  // Combine embedding error with search error
  const error = state.error || embeddingError;

  return {
    ...state,
    error,
    search,
    clearResults,
    embeddings: {
      isReady,
      isLoading: embeddingsLoading,
      progress,
      progressStatus,
      initialize,
    },
  };
}
