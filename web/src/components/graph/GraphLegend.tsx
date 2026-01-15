"use client";

import { useGraphTheme } from "./useGraphTheme";

interface GraphLegendProps {
  categories: Array<{ id: string; name: string }>;
}

export function GraphLegend({ categories }: GraphLegendProps) {
  const { colors, getCategoryColor } = useGraphTheme();

  return (
    <div className="absolute bottom-4 right-4 bg-background/90 backdrop-blur-sm rounded-lg border p-3 shadow-sm">
      <div className="text-xs font-medium mb-2 text-muted-foreground">Legend</div>
      <div className="space-y-1.5">
        {/* Node types */}
        <div className="flex items-center gap-2">
          <div
            className="w-4 h-4 rounded-full"
            style={{ backgroundColor: colors.thesis }}
          />
          <span className="text-xs">Thesis</span>
        </div>
        <div className="flex items-center gap-2">
          <div
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: colors.entity }}
          />
          <span className="text-xs">Entity (uncategorized)</span>
        </div>

        {/* Category colors */}
        {categories.length > 0 && (
          <>
            <div className="border-t my-2" />
            <div className="text-xs font-medium mb-1 text-muted-foreground">
              Entity Categories
            </div>
            {categories.map((category) => (
              <div key={category.id} className="flex items-center gap-2">
                <div
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: getCategoryColor(category.id) }}
                />
                <span className="text-xs">{category.name}</span>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
