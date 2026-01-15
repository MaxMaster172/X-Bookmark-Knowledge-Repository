"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PanelRight, Expand, Search } from "lucide-react";

export type GraphMode = "panel" | "expand" | "zoom";

interface ModeSwitcherProps {
  mode: GraphMode;
  onModeChange: (mode: GraphMode) => void;
}

/**
 * Mode tabs for switching between graph interaction modes
 * - Panel: Click node to show posts in sidebar panel
 * - Expand: Click node to expand posts as child nodes (future)
 * - Zoom: Semantic zoom where zoom level controls visibility (future)
 */
export function ModeSwitcher({ mode, onModeChange }: ModeSwitcherProps) {
  return (
    <Tabs value={mode} onValueChange={(value) => onModeChange(value as GraphMode)}>
      <TabsList>
        <TabsTrigger value="panel" title="Panel mode: Click to show posts in sidebar">
          <PanelRight className="h-4 w-4 mr-1" />
          <span className="hidden sm:inline">Panel</span>
        </TabsTrigger>
        <TabsTrigger value="expand" title="Expand mode: Click to show posts as nodes (coming soon)" disabled>
          <Expand className="h-4 w-4 mr-1" />
          <span className="hidden sm:inline">Expand</span>
        </TabsTrigger>
        <TabsTrigger value="zoom" title="Zoom mode: Semantic zoom controls visibility (coming soon)" disabled>
          <Search className="h-4 w-4 mr-1" />
          <span className="hidden sm:inline">Zoom</span>
        </TabsTrigger>
      </TabsList>
    </Tabs>
  );
}
