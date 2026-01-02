"use client";

import Link from "next/link";
import { SearchBar } from "@/components/search";
import { PostFeed } from "@/components/posts";
import { QuickStats } from "@/components/QuickStats";
import type { PostWithMedia, Stats } from "@/types/database";

interface HomeClientProps {
  initialPosts: PostWithMedia[];
  initialStats: Stats | null;
}

export function HomeClient({ initialPosts, initialStats }: HomeClientProps) {
  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="py-16 md:py-24 bg-gradient-to-b from-primary/5 to-background">
        <div className="container max-w-4xl mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-bold text-center mb-4">
            X-Bookmark Knowledge Base
          </h1>
          <p className="text-lg text-muted-foreground text-center mb-8 max-w-2xl mx-auto">
            Your personal repository of Twitter/X bookmarks with semantic search.
            Find insights across all your saved content.
          </p>

          {/* Search Bar */}
          <div className="max-w-xl mx-auto">
            <SearchBar
              size="lg"
              placeholder="Search your knowledge base..."
              autoFocus
            />
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-8 border-b">
        <div className="container max-w-4xl mx-auto px-4">
          <QuickStats stats={initialStats} />
        </div>
      </section>

      {/* Recent Posts Section */}
      <section className="py-12">
        <div className="container max-w-4xl mx-auto px-4">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold">Recent Bookmarks</h2>
            <Link
              href="/recent"
              className="text-primary hover:underline text-sm"
            >
              View all
            </Link>
          </div>

          <PostFeed
            posts={initialPosts}
            compact
            emptyMessage="No bookmarks yet. Start saving posts from Telegram!"
          />
        </div>
      </section>

      {/* Quick Links */}
      <section className="py-12 bg-muted/30">
        <div className="container max-w-4xl mx-auto px-4">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <QuickLinkCard
              href="/search"
              title="Search"
              description="Semantic search across all your bookmarks"
              icon="S"
            />
            <QuickLinkCard
              href="/chat"
              title="Chat"
              description="Chat with your bookmarks using AI"
              icon="C"
            />
            <QuickLinkCard
              href="/entities"
              title="Entities"
              description="Browse people, companies, and concepts"
              icon="E"
            />
            <QuickLinkCard
              href="/theses"
              title="Theses"
              description="Explore synthesized knowledge themes"
              icon="T"
            />
          </div>
        </div>
      </section>
    </main>
  );
}

function QuickLinkCard({
  href,
  title,
  description,
  icon,
}: {
  href: string;
  title: string;
  description: string;
  icon: string;
}) {
  return (
    <Link
      href={href}
      className="block p-6 rounded-lg border bg-card hover:shadow-md transition-shadow"
    >
      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-semibold mb-3">
        {icon}
      </div>
      <h3 className="font-medium text-lg mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </Link>
  );
}
