"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Thesis } from "@/types/database";

interface SynthesisCardProps {
  thesis: Thesis;
  showFull?: boolean;
  className?: string;
}

function formatDate(dateString: string | null): string {
  if (!dateString) return "Never";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function SynthesisCard({
  thesis,
  showFull = false,
  className,
}: SynthesisCardProps) {
  const hasSynthesis = thesis.current_synthesis && thesis.current_synthesis.trim().length > 0;

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg">{thesis.name}</CardTitle>
          {thesis.category && (
            <Badge variant="secondary" className="shrink-0">
              {thesis.category}
            </Badge>
          )}
        </div>
        {thesis.description && (
          <p className="text-sm text-muted-foreground">{thesis.description}</p>
        )}
      </CardHeader>
      <CardContent>
        {hasSynthesis ? (
          <div className="space-y-3">
            <div
              className={cn(
                "prose prose-sm dark:prose-invert max-w-none",
                !showFull && "line-clamp-6"
              )}
            >
              {/* Render synthesis as markdown-like paragraphs */}
              {thesis.current_synthesis!.split("\n\n").map((paragraph, i) => (
                <p key={i}>{paragraph}</p>
              ))}
            </div>
            <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
              <span>
                Based on {thesis.synthesis_post_count} post
                {thesis.synthesis_post_count !== 1 && "s"}
              </span>
              <span>Updated {formatDate(thesis.synthesis_updated_at)}</span>
            </div>
          </div>
        ) : (
          <div className="text-center py-6 text-muted-foreground">
            <p className="text-sm">No synthesis generated yet</p>
            <p className="text-xs mt-1">
              This thesis needs {thesis.synthesis_post_count > 0 ? "regeneration" : "linked posts"}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
