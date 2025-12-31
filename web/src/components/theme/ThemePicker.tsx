"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { themes, type Theme } from "./ThemeProvider";
import { cn } from "@/lib/utils";

const themeConfig: Record<
  Theme,
  { name: string; description: string; preview: { bg: string; fg: string; accent: string } }
> = {
  light: {
    name: "Light",
    description: "Clean and bright",
    preview: { bg: "#ffffff", fg: "#1a1a2e", accent: "#3b82f6" },
  },
  dark: {
    name: "Dark",
    description: "Easy on the eyes",
    preview: { bg: "#1a1a2e", fg: "#f8fafc", accent: "#60a5fa" },
  },
  sepia: {
    name: "Sepia",
    description: "Warm reading mode",
    preview: { bg: "#f5f0e1", fg: "#433422", accent: "#8b6914" },
  },
  nord: {
    name: "Nord",
    description: "Arctic blue-gray",
    preview: { bg: "#2e3440", fg: "#eceff4", accent: "#88c0d0" },
  },
};

export function ThemePicker() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {themes.map((t) => (
          <div key={t} className="h-32 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    );
  }

  const currentTheme = theme === "system" ? resolvedTheme : theme;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Theme</h3>
        <button
          onClick={() => setTheme("system")}
          className={cn(
            "text-sm text-muted-foreground hover:text-foreground",
            theme === "system" && "text-primary font-medium"
          )}
        >
          Use system theme
        </button>
      </div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {themes.map((t) => {
          const config = themeConfig[t];
          const isSelected = currentTheme === t;

          return (
            <Card
              key={t}
              className={cn(
                "cursor-pointer transition-all hover:shadow-md",
                isSelected && "ring-2 ring-primary"
              )}
              onClick={() => setTheme(t)}
            >
              <CardContent className="p-3">
                {/* Theme preview */}
                <div
                  className="mb-2 h-16 rounded-md border"
                  style={{ backgroundColor: config.preview.bg }}
                >
                  <div className="flex h-full flex-col justify-between p-2">
                    <div
                      className="h-2 w-12 rounded"
                      style={{ backgroundColor: config.preview.fg }}
                    />
                    <div className="flex gap-1">
                      <div
                        className="h-2 w-8 rounded"
                        style={{ backgroundColor: config.preview.accent }}
                      />
                      <div
                        className="h-2 w-6 rounded opacity-50"
                        style={{ backgroundColor: config.preview.fg }}
                      />
                    </div>
                  </div>
                </div>
                {/* Theme info */}
                <div>
                  <p className="font-medium">{config.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {config.description}
                  </p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
