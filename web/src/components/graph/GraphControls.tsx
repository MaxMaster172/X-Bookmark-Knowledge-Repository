"use client";

import { ZoomIn, ZoomOut, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface GraphControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetZoom: () => void;
}

/**
 * Zoom control buttons for the graph visualization
 */
export function GraphControls({ onZoomIn, onZoomOut, onResetZoom }: GraphControlsProps) {
  return (
    <div className="absolute top-4 left-4 flex flex-col gap-1 bg-background/90 backdrop-blur-sm rounded-lg border p-1 shadow-sm">
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onZoomIn}
        aria-label="Zoom in"
        title="Zoom in"
      >
        <ZoomIn className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onZoomOut}
        aria-label="Zoom out"
        title="Zoom out"
      >
        <ZoomOut className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onResetZoom}
        aria-label="Fit to view"
        title="Fit to view"
      >
        <Maximize2 className="h-4 w-4" />
      </Button>
    </div>
  );
}
