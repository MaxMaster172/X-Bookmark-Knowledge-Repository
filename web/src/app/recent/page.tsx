import Link from "next/link";
import { getRecentPosts } from "@/lib/queries/posts";
import { PostFeed } from "@/components/posts";

export const dynamic = "force-dynamic";

export default async function RecentPage() {
  const posts = await getRecentPosts(50);

  return (
    <main className="min-h-screen py-8">
      <div className="container max-w-4xl mx-auto px-4">
        {/* Back Link */}
        <Link
          href="/"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-6"
        >
          &larr; Back to home
        </Link>

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Recent Bookmarks</h1>
          <p className="text-muted-foreground">
            All your bookmarks in chronological order
          </p>
        </div>

        {/* Posts */}
        <PostFeed
          posts={posts}
          emptyMessage="No bookmarks yet. Start saving posts from Telegram!"
        />
      </div>
    </main>
  );
}
