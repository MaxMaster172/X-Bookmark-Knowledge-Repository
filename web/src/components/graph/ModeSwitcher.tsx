"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PanelRight, Expand } from "lucide-react";

export type GraphMode = "panel" | "expand";

interface ModeSwitcherProps {
  mode: GraphMode;
  onModeChange: (mode: GraphMode) => void;
}

/**
 * Mode tabs for switching between graph interaction modes
 * - Panel: Click node to show posts in sidebar panel
 * - Expand: Click node to expand posts as child nodes
 */
export function ModeSwitcher({ mode, onModeChange }: ModeSwitcherProps) {
  return (
    <Tabs value={mode} onValueChange={(value) => onModeChange(value as GraphMode)}>
      <TabsList>
        <TabsTrigger value="panel" title="Panel mode: Click to show posts in sidebar">
          <PanelRight className="h-4 w-4 mr-1" />
          <span className="hidden sm:inline">Panel</span>
        </TabsTrigger>
        <TabsTrigger value="expand" title="Expand mode: Click to show posts as nodes">
          <Expand className="h-4 w-4 mr-1" />
          <span className="hidden sm:inline">Expand</span>
        </TabsTrigger>
      </TabsList>
    </Tabs>
  );
}
