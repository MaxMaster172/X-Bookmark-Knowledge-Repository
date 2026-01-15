"use client";

import { useCallback, useMemo } from "react";
import { useTheme } from "next-themes";
import type { GraphNode } from "@/types/graph";

// Theme-specific color palettes
const THEME_COLORS = {
  light: {
    entity: "#3b82f6", // blue-500
    thesis: "#8b5cf6", // violet-500
    link: "rgba(0, 0, 0, 0.15)",
    background: "#ffffff",
    categories: [
      "#f97316", // chart-1: orange
      "#14b8a6", // chart-2: teal
      "#1e3a5f", // chart-3: dark blue
      "#eab308", // chart-4: yellow
      "#f59e0b", // chart-5: amber
    ],
  },
  dark: {
    entity: "#60a5fa", // blue-400
    thesis: "#a78bfa", // violet-400
    link: "rgba(255, 255, 255, 0.15)",
    background: "#18181b",
    categories: [
      "#818cf8", // chart-1: indigo
      "#4ade80", // chart-2: green
      "#facc15", // chart-3: yellow
      "#e879f9", // chart-4: fuchsia
      "#fb923c", // chart-5: orange
    ],
  },
  sepia: {
    entity: "#a16207", // amber-700
    thesis: "#854d0e", // yellow-800
    link: "rgba(92, 64, 51, 0.2)",
    background: "#f5f0e6",
    categories: [
      "#b45309", // chart-1
      "#4d7c0f", // chart-2
      "#1e40af", // chart-3
      "#ca8a04", // chart-4
      "#c2410c", // chart-5
    ],
  },
  nord: {
    entity: "#88c0d0", // nord8
    thesis: "#b48ead", // nord15
    link: "rgba(216, 222, 233, 0.2)",
    background: "#2e3440",
    categories: [
      "#5e81ac", // chart-1: nord10
      "#8fbcbb", // chart-2: nord7
      "#ebcb8b", // chart-3: nord13
      "#bf616a", // chart-4: nord11
      "#d08770", // chart-5: nord12
    ],
  },
};

export function useGraphTheme() {
  const { resolvedTheme } = useTheme();

  const colors = useMemo(() => {
    const themeName = resolvedTheme as keyof typeof THEME_COLORS;
    return THEME_COLORS[themeName] || THEME_COLORS.light;
  }, [resolvedTheme]);

  const getNodeColor = useCallback(
    (node: GraphNode): string => {
      if (node.type === "thesis") {
        return colors.thesis;
      }

      // For entities, use category-based colors
      if (node.categoryId) {
        // Use a hash of the category ID to pick a consistent color
        const hash = node.categoryId.split("").reduce((acc, char) => {
          return acc + char.charCodeAt(0);
        }, 0);
        const colorIndex = hash % colors.categories.length;
        return colors.categories[colorIndex];
      }

      return colors.entity;
    },
    [colors]
  );

  const getLinkColor = useCallback((): string => {
    return colors.link;
  }, [colors]);

  const getBackgroundColor = useCallback((): string => {
    return colors.background;
  }, [colors]);

  const getCategoryColor = useCallback(
    (categoryId: string): string => {
      const hash = categoryId.split("").reduce((acc, char) => {
        return acc + char.charCodeAt(0);
      }, 0);
      const colorIndex = hash % colors.categories.length;
      return colors.categories[colorIndex];
    },
    [colors]
  );

  return {
    colors,
    getNodeColor,
    getLinkColor,
    getBackgroundColor,
    getCategoryColor,
  };
}
