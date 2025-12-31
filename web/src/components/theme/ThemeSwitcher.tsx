"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { themes, type Theme } from "./ThemeProvider";

const themeLabels: Record<Theme | "system", string> = {
  light: "Light",
  dark: "Dark",
  sepia: "Sepia",
  nord: "Nord",
  system: "System",
};

const themeIcons: Record<Theme | "system", string> = {
  light: "\u2600\ufe0f", // Sun
  dark: "\ud83c\udf19", // Moon
  sepia: "\ud83d\udcd6", // Book
  nord: "\u2744\ufe0f", // Snowflake
  system: "\ud83d\udcbb", // Computer
};

export function ThemeSwitcher() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Avoid hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" className="h-9 w-9">
        <span className="sr-only">Toggle theme</span>
      </Button>
    );
  }

  const currentTheme = theme === "system" ? "system" : (resolvedTheme as Theme);
  const icon = themeIcons[currentTheme] || themeIcons.system;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-9 w-9">
          <span className="text-lg">{icon}</span>
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem
          onClick={() => setTheme("system")}
          className={theme === "system" ? "bg-accent" : ""}
        >
          <span className="mr-2">{themeIcons.system}</span>
          System
        </DropdownMenuItem>
        {themes.map((t) => (
          <DropdownMenuItem
            key={t}
            onClick={() => setTheme(t)}
            className={theme === t ? "bg-accent" : ""}
          >
            <span className="mr-2">{themeIcons[t]}</span>
            {themeLabels[t]}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
