"use client";

import { useState } from "react";
import Image from "next/image";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import type { PostMedia as PostMediaType } from "@/types/database";

interface PostMediaProps {
  media: PostMediaType[];
  compact?: boolean;
}

const categoryIcons: Record<string, string> = {
  text_heavy: "Aa",
  chart: "C",
  general: "G",
};

export function PostMedia({ media, compact = false }: PostMediaProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  if (!media || media.length === 0) return null;

  const imageMedia = media.filter(
    (m) => m.type === "image" || m.type === "photo"
  );

  if (imageMedia.length === 0) return null;

  // Grid layout based on number of images
  const gridClass =
    imageMedia.length === 1
      ? "grid-cols-1"
      : imageMedia.length === 2
        ? "grid-cols-2"
        : imageMedia.length === 3
          ? "grid-cols-2"
          : "grid-cols-2";

  return (
    <div className={cn("grid gap-2", gridClass, compact && "max-w-md")}>
      {imageMedia.map((item, index) => (
        <Dialog key={item.id}>
          <DialogTrigger asChild>
            <button
              className={cn(
                "relative overflow-hidden rounded-lg border bg-muted group cursor-zoom-in",
                compact ? "aspect-video" : "aspect-[4/3]",
                imageMedia.length === 3 && index === 0 && "row-span-2 aspect-[3/4]"
              )}
              onClick={() => setSelectedIndex(index)}
            >
              {item.url && (
                <Image
                  src={item.url}
                  alt={item.description ?? "Post media"}
                  fill
                  className="object-cover transition-transform group-hover:scale-105"
                  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                />
              )}
              {/* Category indicator */}
              {item.category && (
                <span
                  className="absolute top-2 right-2 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded"
                  title={`Category: ${item.category}`}
                >
                  {categoryIcons[item.category] || item.category}
                </span>
              )}
              {/* Description preview on hover */}
              {item.description && !compact && (
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                  <p className="text-white text-xs line-clamp-2">
                    {item.description}
                  </p>
                </div>
              )}
            </button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl p-0 overflow-hidden">
            <div className="flex flex-col md:flex-row">
              {/* Image */}
              <div className="relative flex-1 min-h-[300px] md:min-h-[500px] bg-black">
                {item.url && (
                  <Image
                    src={item.url}
                    alt={item.description ?? "Post media"}
                    fill
                    className="object-contain"
                    sizes="(max-width: 768px) 100vw, 80vw"
                    priority
                  />
                )}
              </div>
              {/* Description panel */}
              {item.description && (
                <div className="w-full md:w-80 p-4 bg-card">
                  <div className="mb-2 flex items-center gap-2">
                    {item.category && (
                      <span className="text-xs px-2 py-1 rounded bg-muted">
                        {item.category}
                      </span>
                    )}
                    {item.extraction_model && (
                      <span className="text-xs text-muted-foreground">
                        by {item.extraction_model}
                      </span>
                    )}
                  </div>
                  <p className="text-sm">{item.description}</p>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      ))}
    </div>
  );
}
