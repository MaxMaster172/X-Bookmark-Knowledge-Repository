import { Suspense } from "react";
import { getRecentPosts } from "@/lib/queries/posts";
import { getStats } from "@/lib/queries/stats";
import { HomeClient } from "./HomeClient";

// Force dynamic rendering - data changes frequently
export const dynamic = "force-dynamic";

export default async function Home() {
  // Fetch initial data server-side
  const [posts, stats] = await Promise.all([
    getRecentPosts(5),
    getStats(),
  ]);

  return (
    <Suspense fallback={<HomeLoading />}>
      <HomeClient initialPosts={posts} initialStats={stats} />
    </Suspense>
  );
}

function HomeLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-pulse text-muted-foreground">Loading...</div>
    </div>
  );
}
