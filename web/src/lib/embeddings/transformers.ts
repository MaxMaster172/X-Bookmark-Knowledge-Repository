/**
 * Transformers.js Embedding Service
 *
 * Uses BGE-small-en-v1.5 model (384 dimensions) for browser-based embeddings.
 * Same model as Python backend = vector compatibility.
 *
 * Trade-offs documented in DESIGN_DECISIONS.md:
 * - PRO: Zero API costs, complete privacy
 * - PRO: Same model as Python backend = vector compatibility
 * - CON: Large initial download (~50MB)
 * - CON: Model loads on first search (2-3 seconds)
 */

// Model configuration (static - safe for SSR)
const MODEL_NAME = "Xenova/bge-small-en-v1.5";
const EMBEDDING_DIM = 384;

// Pipeline type - simplified to avoid complex union type inference
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Pipeline = any;

// Singleton state
let embeddingPipeline: Pipeline | null = null;
let isLoading = false;
let loadError: Error | null = null;
let loadProgress = 0;

// Progress callback type
export type ProgressCallback = (progress: {
  status: string;
  progress: number;
  file?: string;
}) => void;

/**
 * Initialize the embedding pipeline (singleton)
 * Downloads model on first call (~50MB, cached in IndexedDB)
 */
export async function initEmbeddings(
  onProgress?: ProgressCallback
): Promise<void> {
  // Already loaded
  if (embeddingPipeline) return;

  // Already loading - wait for completion
  if (isLoading) {
    return new Promise((resolve, reject) => {
      const checkInterval = setInterval(() => {
        if (embeddingPipeline) {
          clearInterval(checkInterval);
          resolve();
        } else if (loadError) {
          clearInterval(checkInterval);
          reject(loadError);
        }
      }, 100);
    });
  }

  isLoading = true;
  loadError = null;
  loadProgress = 0;

  try {
    // Dynamic import - only loads in browser context
    const { pipeline } = await import("@huggingface/transformers");

    embeddingPipeline = await pipeline("feature-extraction", MODEL_NAME, {
      progress_callback: (progress: { status: string; progress?: number; file?: string }) => {
        if (progress.progress !== undefined) {
          loadProgress = progress.progress;
        }
        onProgress?.({
          status: progress.status,
          progress: loadProgress,
          file: progress.file,
        });
      },
    });
  } catch (error) {
    loadError = error instanceof Error ? error : new Error(String(error));
    throw loadError;
  } finally {
    isLoading = false;
  }
}

/**
 * Generate embedding for text
 * Returns 384-dimensional vector matching Python backend
 */
export async function generateEmbedding(text: string): Promise<number[]> {
  if (!embeddingPipeline) {
    await initEmbeddings();
  }

  if (!embeddingPipeline) {
    throw new Error("Embedding pipeline not initialized");
  }

  // Generate embedding with mean pooling and normalization
  // This matches the Python implementation
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const output = await (embeddingPipeline as any)(text, {
    pooling: "mean",
    normalize: true,
  });

  // Convert to array
  const embedding = Array.from(output.data as Float32Array);

  // Verify dimensions
  if (embedding.length !== EMBEDDING_DIM) {
    throw new Error(
      `Unexpected embedding dimension: ${embedding.length}, expected ${EMBEDDING_DIM}`
    );
  }

  return embedding;
}

/**
 * Check if embeddings are ready
 */
export function isEmbeddingsReady(): boolean {
  return embeddingPipeline !== null;
}

/**
 * Check if embeddings are currently loading
 */
export function isEmbeddingsLoading(): boolean {
  return isLoading;
}

/**
 * Get current load progress (0-100)
 */
export function getLoadProgress(): number {
  return loadProgress;
}

/**
 * Get any load error
 */
export function getLoadError(): Error | null {
  return loadError;
}

/**
 * Model info
 */
export const MODEL_INFO = {
  name: MODEL_NAME,
  dimensions: EMBEDDING_DIM,
  approximateSize: "50MB",
  cacheLocation: "IndexedDB",
};
