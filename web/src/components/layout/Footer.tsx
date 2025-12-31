import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t py-6 md:py-8">
      <div className="container max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="text-sm text-muted-foreground">
          X-Bookmark Knowledge Base
        </div>
        <nav className="flex items-center gap-4 text-sm text-muted-foreground">
          <Link href="/search" className="hover:text-foreground transition-colors">
            Search
          </Link>
          <Link href="/entities" className="hover:text-foreground transition-colors">
            Entities
          </Link>
          <Link href="/theses" className="hover:text-foreground transition-colors">
            Theses
          </Link>
        </nav>
      </div>
    </footer>
  );
}
