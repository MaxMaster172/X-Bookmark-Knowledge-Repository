"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeSwitcher } from "@/components/theme";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/search", label: "Search" },
  { href: "/chat", label: "Chat" },
  { href: "/recent", label: "Recent" },
  { href: "/entities", label: "Entities" },
  { href: "/theses", label: "Theses" },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-6xl mx-auto items-center px-4">
        {/* Logo */}
        <Link href="/" className="mr-6 flex items-center space-x-2">
          <span className="font-bold text-lg">X-Bookmark</span>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center space-x-6 text-sm font-medium flex-1">
          {navItems.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "transition-colors hover:text-foreground/80",
                  isActive ? "text-foreground" : "text-foreground/60"
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Right side: Theme switcher */}
        <div className="flex items-center">
          <ThemeSwitcher />
        </div>
      </div>
    </header>
  );
}
