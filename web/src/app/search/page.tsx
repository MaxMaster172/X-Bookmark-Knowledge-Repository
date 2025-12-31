"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, Suspense } from "react";
import { SearchBar, EmbeddingLoader } from "@/components/search";
import { PostFeed } from "@/components/posts";
import { Badge } from "@/components/ui/badge";
import { useSearch } from "@/hooks/useSearch";

function SearchContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  const {
    query,
    results,
    isSearching,
    isEmbedding,
    error,
    hasSearched,
    search,
    embeddings,
  } = useSearch({ autoInitialize: true });

  // Auto-search if query param provided
  useEffect(() => {
    if (initialQuery && !query) {
      search(initialQuery);
    }
  }, [initialQuery, query, search]);

  return (
    <main className="min-h-screen py-8">
      <div className="container max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Search</h1>
          <p className="text-muted-foreground">
            Find bookmarks using semantic search powered by AI
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <SearchBar
            defaultValue={initialQuery}
            onSearch={search}
            isLoading={isSearching}
            loadingText={isEmbedding ? "Generating embedding..." : "Searching..."}
            size="lg"
            autoFocus
          />
        </div>

        {/* Model Loading State */}
        {!embeddings.isReady && embeddings.isLoading && (
          <div className="mb-8">
            <EmbeddingLoader
              progress={embeddings.progress}
              status={embeddings.progressStatus}
            />
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="mb-8 p-4 rounded-lg bg-destructive/10 text-destructive">
            <p className="font-medium">Search error</p>
            <p className="text-sm">{error.message}</p>
          </div>
        )}

        {/* Results */}
        {hasSearched && !isSearching && (
          <div>
            {/* Results Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <h2 className="font-medium">Results</h2>
                <Badge variant="secondary">{results.length}</Badge>
              </div>
              {query && (
                <p className="text-sm text-muted-foreground">
                  Showing results for &ldquo;{query}&rdquo;
                </p>
              )}
            </div>

            {/* Results List */}
            <PostFeed
              posts={results}
              showSimilarity
              emptyMessage={`No results found for "${query}". Try different keywords or phrases.`}
            />
          </div>
        )}

        {/* Initial State */}
        {!hasSearched && !isSearching && embeddings.isReady && (
          <div className="text-center py-12 text-muted-foreground">
            <p>Enter a search query to find relevant bookmarks</p>
            <p className="text-sm mt-2">
              Try questions like &ldquo;AI investing strategies&rdquo; or &ldquo;health optimization tips&rdquo;
            </p>
          </div>
        )}
      </div>
    </main>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <SearchContent />
    </Suspense>
  );
}
