"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { MODEL_INFO } from "@/lib/embeddings/transformers";

interface EmbeddingLoaderProps {
  progress: number;
  status: string;
  className?: string;
}

export function EmbeddingLoader({
  progress,
  status,
  className,
}: EmbeddingLoaderProps) {
  const isDownloading = status === "downloading" || status === "progress";
  const isInitializing = status === "initiate" || status === "loading";

  return (
    <Card className={cn("w-full max-w-md mx-auto", className)}>
      <CardContent className="p-6 text-center">
        <div className="mb-4">
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-primary/10 flex items-center justify-center">
            <svg
              className="h-6 w-6 text-primary animate-pulse"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
          </div>
          <h3 className="font-medium text-lg">
            {isDownloading
              ? "Downloading Search Model"
              : isInitializing
                ? "Initializing Search"
                : "Loading..."}
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            {isDownloading
              ? `First-time download (~${MODEL_INFO.approximateSize})`
              : "Cached in browser for future searches"}
          </p>
        </div>

        {/* Progress bar */}
        <div className="relative h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 bg-primary transition-all duration-300 ease-out rounded-full"
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          {Math.round(progress)}% complete
        </p>

        {/* Model info */}
        <p className="text-xs text-muted-foreground mt-4">
          Model: {MODEL_INFO.name} ({MODEL_INFO.dimensions}-dim)
        </p>
      </CardContent>
    </Card>
  );
}
