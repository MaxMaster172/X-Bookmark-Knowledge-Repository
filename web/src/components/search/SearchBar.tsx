"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface SearchBarProps {
  defaultValue?: string;
  onSearch?: (query: string) => void;
  placeholder?: string;
  showButton?: boolean;
  autoFocus?: boolean;
  isLoading?: boolean;
  loadingText?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function SearchBar({
  defaultValue = "",
  onSearch,
  placeholder = "Search your knowledge base...",
  showButton = true,
  autoFocus = false,
  isLoading = false,
  loadingText = "Searching...",
  size = "md",
  className,
}: SearchBarProps) {
  const [query, setQuery] = useState(defaultValue);
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const trimmedQuery = query.trim();
      if (!trimmedQuery) return;

      if (onSearch) {
        onSearch(trimmedQuery);
      } else {
        // Default behavior: navigate to search page
        router.push(`/search?q=${encodeURIComponent(trimmedQuery)}`);
      }
    },
    [query, onSearch, router]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        handleSubmit(e);
      }
    },
    [handleSubmit]
  );

  return (
    <form onSubmit={handleSubmit} className={cn("flex gap-2", className)}>
      <div className="relative flex-1">
        <Input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading}
          className={cn(
            "pr-10 transition-all",
            size === "sm" && "h-9 text-sm",
            size === "md" && "h-10",
            size === "lg" && "h-12 text-lg"
          )}
        />
        {/* Search icon */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none">
          {isLoading ? (
            <svg
              className="h-4 w-4 animate-spin"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : (
            <svg
              className="h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          )}
        </div>
      </div>
      {showButton && (
        <Button
          type="submit"
          disabled={isLoading || !query.trim()}
          className={cn(
            size === "sm" && "h-9",
            size === "md" && "h-10",
            size === "lg" && "h-12 px-6"
          )}
        >
          {isLoading ? loadingText : "Search"}
        </Button>
      )}
    </form>
  );
}
