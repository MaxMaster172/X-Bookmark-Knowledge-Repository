"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { Stats } from "@/types/database";

interface QuickStatsProps {
  stats: Stats | null;
  isLoading?: boolean;
}

const statItems = [
  { key: "total_posts", label: "Posts", icon: "P" },
  { key: "unique_authors", label: "Authors", icon: "A" },
  { key: "total_entities", label: "Entities", icon: "E" },
  { key: "total_theses", label: "Theses", icon: "T" },
] as const;

export function QuickStats({ stats, isLoading = false }: QuickStatsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statItems.map((item) => (
          <Card key={item.key}>
            <CardContent className="p-4">
              <Skeleton className="h-8 w-16 mb-2" />
              <Skeleton className="h-4 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center text-muted-foreground py-8">
        Unable to load stats
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {statItems.map((item) => (
        <Card key={item.key} className="hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-semibold">
                {item.icon}
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {stats[item.key].toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">{item.label}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
