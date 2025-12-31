"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Thesis } from "@/types/database";

interface ThesisBadgeProps {
  thesis: Thesis;
  contribution?: string | null;
  confidence?: number;
  size?: "sm" | "md";
  showCategory?: boolean;
  asLink?: boolean;
}

// Category-based color mapping for theses
const categoryColors: Record<string, string> = {
  investing: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200 hover:bg-emerald-200 dark:hover:bg-emerald-800",
  health: "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200 hover:bg-rose-200 dark:hover:bg-rose-800",
  tech: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200 hover:bg-indigo-200 dark:hover:bg-indigo-800",
  default: "bg-muted text-muted-foreground hover:bg-muted/80",
};

export function ThesisBadge({
  thesis,
  contribution,
  confidence,
  size = "md",
  showCategory = false,
  asLink = true,
}: ThesisBadgeProps) {
  const categoryName = thesis.category?.toLowerCase() ?? "default";
  const colorClass = categoryColors[categoryName] || categoryColors.default;

  const content = (
    <Badge
      variant="outline"
      className={cn(
        "transition-colors cursor-pointer border-0",
        colorClass,
        size === "sm" && "text-xs px-1.5 py-0",
        size === "md" && "text-sm px-2 py-0.5"
      )}
      title={contribution ?? thesis.description ?? undefined}
    >
      {showCategory && thesis.category && (
        <span className="opacity-60 mr-1">{thesis.category}:</span>
      )}
      {thesis.name}
      {confidence !== undefined && confidence < 1 && (
        <span className="ml-1 opacity-50">({Math.round(confidence * 100)}%)</span>
      )}
    </Badge>
  );

  if (asLink) {
    return (
      <Link href={`/theses/${thesis.id}`} className="inline-block">
        {content}
      </Link>
    );
  }

  return content;
}
