"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Entity, EntityCategory } from "@/types/database";

interface EntityBadgeProps {
  entity: Entity & { category?: EntityCategory | null };
  confidence?: number;
  size?: "sm" | "md";
  showCategory?: boolean;
  asLink?: boolean;
}

// Category-based color mapping
const categoryColors: Record<string, string> = {
  person: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 hover:bg-blue-200 dark:hover:bg-blue-800",
  company: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 hover:bg-green-200 dark:hover:bg-green-800",
  product: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200 hover:bg-purple-200 dark:hover:bg-purple-800",
  concept: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 hover:bg-orange-200 dark:hover:bg-orange-800",
  technology: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200 hover:bg-cyan-200 dark:hover:bg-cyan-800",
  default: "bg-muted text-muted-foreground hover:bg-muted/80",
};

export function EntityBadge({
  entity,
  confidence,
  size = "md",
  showCategory = false,
  asLink = true,
}: EntityBadgeProps) {
  const categoryName = entity.category?.name?.toLowerCase() ?? "default";
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
    >
      {showCategory && entity.category && (
        <span className="opacity-60 mr-1">{entity.category.name}:</span>
      )}
      {entity.name}
      {confidence !== undefined && confidence < 1 && (
        <span className="ml-1 opacity-50">({Math.round(confidence * 100)}%)</span>
      )}
    </Badge>
  );

  if (asLink) {
    return (
      <Link href={`/entities/${entity.id}`} className="inline-block">
        {content}
      </Link>
    );
  }

  return content;
}
