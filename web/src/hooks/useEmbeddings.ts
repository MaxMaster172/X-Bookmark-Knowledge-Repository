"use client";

import { useState, useEffect, useCallback } from "react";
import {
  initEmbeddings,
  generateEmbedding,
  isEmbeddingsReady,
  isEmbeddingsLoading,
  getLoadProgress,
  MODEL_INFO,
  type ProgressCallback,
} from "@/lib/embeddings/transformers";

export interface EmbeddingState {
  isReady: boolean;
  isLoading: boolean;
  progress: number;
  progressStatus: string;
  error: Error | null;
}

export interface UseEmbeddingsReturn extends EmbeddingState {
  initialize: () => Promise<void>;
  embed: (text: string) => Promise<number[]>;
  modelInfo: typeof MODEL_INFO;
}

/**
 * React hook for Transformers.js embeddings
 *
 * Usage:
 * ```tsx
 * const { isReady, isLoading, progress, embed, initialize, error } = useEmbeddings();
 *
 * // Initialize on mount (optional - will auto-init on first embed)
 * useEffect(() => { initialize(); }, [initialize]);
 *
 * // Generate embedding
 * const embedding = await embed("search query");
 * ```
 */
export function useEmbeddings(): UseEmbeddingsReturn {
  const [state, setState] = useState<EmbeddingState>({
    isReady: isEmbeddingsReady(),
    isLoading: isEmbeddingsLoading(),
    progress: getLoadProgress(),
    progressStatus: "",
    error: null,
  });

  // Progress callback
  const handleProgress: ProgressCallback = useCallback((progress) => {
    setState((prev) => ({
      ...prev,
      progress: progress.progress,
      progressStatus: progress.status,
    }));
  }, []);

  // Initialize embeddings
  const initialize = useCallback(async () => {
    if (isEmbeddingsReady()) {
      setState((prev) => ({ ...prev, isReady: true, isLoading: false }));
      return;
    }

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      await initEmbeddings(handleProgress);
      setState((prev) => ({
        ...prev,
        isReady: true,
        isLoading: false,
        progress: 100,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error : new Error(String(error)),
      }));
    }
  }, [handleProgress]);

  // Generate embedding (auto-initializes if needed)
  const embed = useCallback(
    async (text: string): Promise<number[]> => {
      if (!isEmbeddingsReady()) {
        await initialize();
      }
      return generateEmbedding(text);
    },
    [initialize]
  );

  // Check ready state on mount
  useEffect(() => {
    setState((prev) => ({
      ...prev,
      isReady: isEmbeddingsReady(),
      isLoading: isEmbeddingsLoading(),
      progress: getLoadProgress(),
    }));
  }, []);

  return {
    ...state,
    initialize,
    embed,
    modelInfo: MODEL_INFO,
  };
}
