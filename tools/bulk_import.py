#!/usr/bin/env python3
"""
Bulk Import from Notion

Import X/Twitter posts from a Notion Markdown export file into Supabase.
Extracts URLs from the markdown, fetches post content, saves to Supabase with embeddings.

Environment variables required:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_SERVICE_KEY: Your Supabase service role key

Usage:
    python tools/bulk_import.py notion_export.md
    python tools/bulk_import.py notion_export.md --dry-run
    python tools/bulk_import.py notion_export.md --delay 2 --skip-confirm
"""

import argparse
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    # Look for .env in both current directory and parent directory
    env_paths = [
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass  # dotenv not installed, use system environment variables

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.twitter_fetcher import fetch_thread, Thread, extract_tweet_id
from src.supabase.client import get_supabase_client, SupabaseClient
from src.embeddings.service import get_embedding_service, EmbeddingService

# Pattern to match X/Twitter URLs (including fxtwitter, vxtwitter variants)
X_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?(?:twitter\.com|x\.com|fxtwitter\.com|vxtwitter\.com|fixupx\.com)/(\w+)/status/(\d+)'
)

# Lazy-loaded singletons
_supabase_client: SupabaseClient = None
_embedding_service: EmbeddingService = None


def get_db() -> SupabaseClient:
    """Get the Supabase client (lazy singleton)."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client


def get_embeddings() -> EmbeddingService:
    """Get the embedding service (lazy singleton)."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = get_embedding_service()
    return _embedding_service


def normalize_twitter_url(url: str) -> str:
    """Normalize X/Twitter URL to canonical x.com format."""
    match = X_URL_PATTERN.search(url)
    if match:
        handle, tweet_id = match.groups()
        return f"https://x.com/{handle}/status/{tweet_id}"
    return url


def extract_urls_from_markdown(content: str) -> list[str]:
    """Extract X/Twitter URLs from Markdown content."""
    urls = []

    # Find markdown links: [text](url)
    md_links = re.findall(r'\[.*?\]\((https?://[^\)]+)\)', content)
    urls.extend(md_links)

    # Find bare URLs
    bare_urls = re.findall(
        r'https?://(?:www\.)?(?:twitter\.com|x\.com|fxtwitter\.com|vxtwitter\.com|fixupx\.com)/\w+/status/\d+',
        content
    )
    urls.extend(bare_urls)

    # Filter to only X/Twitter status URLs and normalize
    valid_urls = []
    for url in urls:
        if X_URL_PATTERN.search(url):
            normalized = normalize_twitter_url(url)
            valid_urls.append(normalized)

    return valid_urls


def parse_notion_export(file_path: str) -> list[str]:
    """Extract and deduplicate X/Twitter URLs from Notion export."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    urls = extract_urls_from_markdown(content)

    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def check_duplicates(urls: list[str]) -> tuple[list[str], list[str]]:
    """Check URLs against Supabase, return (new_urls, duplicate_urls)."""
    new_urls = []
    duplicate_urls = []
    db = get_db()

    for url in urls:
        tweet_id = extract_tweet_id(url)
        if tweet_id and db.post_exists(tweet_id):
            duplicate_urls.append(url)
        else:
            new_urls.append(url)

    return new_urls, duplicate_urls


def show_preflight_report(
    total: int,
    duplicates: list[str],
    new_urls: list[str],
    dry_run: bool,
    skip_confirm: bool
) -> bool:
    """Display what will be imported, ask for confirmation. Returns True to proceed."""
    # Show Supabase stats
    try:
        stats = get_db().get_stats()
        print("\nBulk Import - X-Bookmark Knowledge Repository (Supabase)")
        print("-" * 55)
        print(f"Current database: {stats.get('total_posts', 0)} posts")
    except Exception as e:
        print(f"\nWarning: Could not get Supabase stats: {e}")
        print("\nBulk Import - X-Bookmark Knowledge Repository (Supabase)")
        print("-" * 55)

    print(f"\nFound {total} URLs in export file")
    print(f"Already archived: {len(duplicates)} (will skip)")
    print(f"New posts to import: {len(new_urls)}")

    if dry_run:
        print("\n[DRY RUN] No changes will be made.")
        if new_urls:
            print("\nURLs that would be imported:")
            for url in new_urls:
                print(f"  - {url}")
        return False

    if not new_urls:
        print("\nNo new posts to import.")
        return False

    if skip_confirm:
        return True

    response = input("\nContinue with import? [Y/n] ").strip().lower()
    return response in ('', 'y', 'yes')


def fetch_posts(urls: list[str], delay: float) -> tuple[list, list]:
    """Fetch all posts, return (successes, failures)."""
    successes = []
    failures = []

    print("\nFetching posts...")
    for i, url in enumerate(urls):
        tweet_id = extract_tweet_id(url)
        print(f"[{i+1}/{len(urls)}] @.../{tweet_id} ", end="", flush=True)

        try:
            thread = fetch_thread(url)
            if thread:
                successes.append((url, thread))
                print("OK")
            else:
                failures.append((url, "Post not found or unavailable"))
                print("FAILED (not found)")
        except Exception as e:
            failures.append((url, str(e)))
            print(f"FAILED ({str(e)[:50]})")

        # Rate limiting between requests
        if i < len(urls) - 1:
            time.sleep(delay)

    return successes, failures


def build_content(thread: Thread) -> str:
    """Build content string from thread."""
    if thread.total_count > 1:
        content_parts = []
        for i, tweet in enumerate(thread.tweets, 1):
            content_parts.append(f"[{i}/{thread.total_count}]\n{tweet.text}")
        return "\n\n---\n\n".join(content_parts)
    else:
        return thread.tweets[0].text


def save_posts_to_supabase(posts: list[tuple[str, Thread]], no_embed: bool = False) -> tuple[list[str], int]:
    """Save all posts to Supabase with embeddings. Returns (saved_ids, embed_count)."""
    if not posts:
        return [], 0

    db = get_db()
    saved_ids = []
    embed_count = 0

    print("\nSaving posts to Supabase...")
    for url, thread in posts:
        post_id = thread.tweets[0].id
        archived_at = datetime.now()

        # Build content
        content = build_content(thread)

        # Build embedding text
        embed_text = content
        if thread.author_handle:
            embed_text += f"\n\nAuthor: @{thread.author_handle}"

        # Generate embedding
        embedding = None
        if not no_embed:
            try:
                embedding = get_embeddings().generate(embed_text)
                embed_count += 1
            except Exception as e:
                print(f"  Warning: Failed to generate embedding for {post_id}: {e}")

        # Handle quoted tweet
        quoted_post_id = None
        quoted_text = None
        quoted_author = None
        quoted_url = None
        for tweet in thread.tweets:
            if tweet.quoted_tweet:
                quoted_post_id = tweet.quoted_tweet.id
                quoted_url = tweet.quoted_tweet.url
                quoted_author = tweet.quoted_tweet.author_handle
                quoted_text = tweet.quoted_tweet.text[:200] if tweet.quoted_tweet.text else None
                break

        # Parse posted_at date
        posted_at = None
        if thread.tweets[0].created_at:
            try:
                posted_at_str = thread.tweets[0].created_at
                if isinstance(posted_at_str, str):
                    posted_at = posted_at_str
            except Exception:
                posted_at = None

        try:
            # Insert into Supabase
            db.insert_post(
                post_id=post_id,
                url=url,
                content=content,
                author_handle=thread.author_handle,
                author_name=thread.author_name,
                posted_at=posted_at,
                archived_at=archived_at,
                archived_via="bulk_import",
                tags=[],
                topics=[],
                notes=None,
                is_thread=thread.total_count > 1,
                quoted_post_id=quoted_post_id,
                quoted_text=quoted_text,
                quoted_author=quoted_author,
                quoted_url=quoted_url,
                embedding=embedding,
            )

            # Insert media items
            for tweet in thread.tweets:
                for m in tweet.media:
                    try:
                        db.insert_media(
                            post_id=post_id,
                            media_type=m.get("type", "image"),
                            url=m.get("url", ""),
                        )
                    except Exception:
                        pass  # Silently ignore media insertion failures

            saved_ids.append(post_id)
            status = "OK" if embedding else "OK (no embedding)"
            print(f"  Saved: {post_id} - {status}")

        except Exception as e:
            print(f"  FAILED: {post_id} - {str(e)[:50]}")

    return saved_ids, embed_count


def finalize(saved_ids: list[str], failures: list[tuple[str, str]], embed_count: int):
    """Print summary (no git operations)."""
    # Write failures to log file
    if failures:
        log_path = Path("bulk_import_errors.log")
        with open(log_path, "w", encoding="utf-8") as f:
            for url, error in failures:
                f.write(f"{url}: {error}\n")
        print(f"\nErrors logged to: {log_path}")

    # Print summary
    print("\n" + "=" * 55)
    print("Import Complete!")
    print("=" * 55)
    print(f"\nSuccessfully imported to Supabase: {len(saved_ids)}")
    if embed_count > 0:
        print(f"Embeddings generated: {embed_count}")
    if failures:
        print(f"Failed to fetch: {len(failures)}")
        for url, error in failures[:5]:  # Show first 5 failures
            print(f"  - {url}: {error}")
        if len(failures) > 5:
            print(f"  ... and {len(failures) - 5} more (see bulk_import_errors.log)")

    # Show final database stats
    try:
        stats = get_db().get_stats()
        print(f"\nDatabase now contains: {stats.get('total_posts', 0)} posts")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="Import X/Twitter posts from a Notion Markdown export to Supabase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/bulk_import.py notion_export.md
  python tools/bulk_import.py notion_export.md --dry-run
  python tools/bulk_import.py notion_export.md --delay 2 --skip-confirm
        """
    )
    parser.add_argument(
        "export_file",
        help="Path to Notion Markdown export file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without making changes"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Seconds between API requests (default: 1.5)"
    )
    parser.add_argument(
        "--skip-confirm",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--no-embed",
        action="store_true",
        help="Skip embedding generation"
    )

    args = parser.parse_args()

    # Validate input file
    export_path = Path(args.export_file)
    if not export_path.exists():
        print(f"Error: File not found: {args.export_file}")
        sys.exit(1)

    # Step 1: Parse export file and extract URLs
    print(f"Reading URLs from: {args.export_file}")
    urls = parse_notion_export(args.export_file)

    if not urls:
        print("No X/Twitter URLs found in export file.")
        sys.exit(0)

    # Step 2: Check for duplicates in Supabase
    print("Checking for duplicates in Supabase...")
    new_urls, duplicate_urls = check_duplicates(urls)

    # Step 3: Show pre-flight report
    proceed = show_preflight_report(
        total=len(urls),
        duplicates=duplicate_urls,
        new_urls=new_urls,
        dry_run=args.dry_run,
        skip_confirm=args.skip_confirm
    )

    if not proceed:
        sys.exit(0)

    # Step 4: Fetch posts
    successes, failures = fetch_posts(new_urls, args.delay)

    if not successes:
        print("\nNo posts were successfully fetched.")
        if failures:
            finalize([], failures, 0)
        sys.exit(1)

    # Step 5: Save posts to Supabase with embeddings
    saved_ids, embed_count = save_posts_to_supabase(successes, no_embed=args.no_embed)

    # Step 6: Finalize
    finalize(saved_ids, failures, embed_count)


if __name__ == "__main__":
    main()
