"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Entity, EntityCategory } from "@/types/database";

interface EntityCardProps {
  entity: Entity & { category?: EntityCategory | null };
  postCount?: number;
  thesisCount?: number;
  className?: string;
}

export function EntityCard({
  entity,
  postCount,
  thesisCount,
  className,
}: EntityCardProps) {
  return (
    <Link href={`/entities/${entity.id}`}>
      <Card
        className={cn(
          "hover:shadow-md transition-shadow cursor-pointer h-full",
          className
        )}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="font-medium text-lg">{entity.name}</h3>
            {entity.category && (
              <Badge variant="secondary" className="shrink-0 text-xs">
                {entity.category.name}
              </Badge>
            )}
          </div>
          {entity.description && (
            <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
              {entity.description}
            </p>
          )}
          {entity.aliases && entity.aliases.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {entity.aliases.slice(0, 3).map((alias) => (
                <Badge key={alias} variant="outline" className="text-xs">
                  {alias}
                </Badge>
              ))}
              {entity.aliases.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{entity.aliases.length - 3}
                </Badge>
              )}
            </div>
          )}
          <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2 border-t">
            {postCount !== undefined && (
              <span>
                {postCount} post{postCount !== 1 && "s"}
              </span>
            )}
            {thesisCount !== undefined && (
              <span>
                {thesisCount} {thesisCount === 1 ? "thesis" : "theses"}
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
