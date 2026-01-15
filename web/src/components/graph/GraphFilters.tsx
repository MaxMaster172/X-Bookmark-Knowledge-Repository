"use client";

import { useGraphTheme } from "./useGraphTheme";

interface GraphFiltersProps {
  categories: Array<{ id: string; name: string }>;
  visibleCategories: Set<string>;
  onToggleCategory: (categoryId: string) => void;
  onToggleAll: (showAll: boolean) => void;
}

/**
 * Category filter checkboxes for filtering graph nodes
 */
export function GraphFilters({
  categories,
  visibleCategories,
  onToggleCategory,
  onToggleAll,
}: GraphFiltersProps) {
  const { getCategoryColor } = useGraphTheme();

  // Check if all categories are visible (or none are explicitly hidden)
  const allVisible = visibleCategories.size === 0 || visibleCategories.size === categories.length;

  return (
    <div className="bg-background/90 backdrop-blur-sm rounded-lg border p-3 shadow-sm">
      <div className="text-xs font-medium mb-2 text-muted-foreground">Filter by Category</div>
      <div className="space-y-1.5">
        {/* All toggle */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={allVisible}
            onChange={(e) => onToggleAll(e.target.checked)}
            className="h-3.5 w-3.5 rounded border-muted-foreground/50 accent-primary"
          />
          <span className="text-xs font-medium">All categories</span>
        </label>

        <div className="border-t my-2" />

        {/* Individual category checkboxes */}
        {categories.map((category) => {
          const isVisible = visibleCategories.size === 0 || visibleCategories.has(category.id);
          return (
            <label key={category.id} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isVisible}
                onChange={() => onToggleCategory(category.id)}
                className="h-3.5 w-3.5 rounded border-muted-foreground/50 accent-primary"
              />
              <div
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: getCategoryColor(category.id) }}
              />
              <span className="text-xs">{category.name}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
}
