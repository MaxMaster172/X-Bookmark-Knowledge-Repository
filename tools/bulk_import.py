#!/usr/bin/env python3
"""
Bulk Import from Notion

Import X/Twitter posts from a Notion Markdown export file into the knowledge repository.
Extracts URLs from the markdown, fetches post content, saves to archive, and generates embeddings.

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

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.twitter_fetcher import fetch_thread, Thread, extract_tweet_id
from tools.utils import (
    ARCHIVE_DIR,
    get_post_path,
    load_index,
    save_index,
    load_tags,
    save_tags,
    check_duplicate,
    git_sync,
)

# Pattern to match X/Twitter URLs (including fxtwitter, vxtwitter variants)
X_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?(?:twitter\.com|x\.com|fxtwitter\.com|vxtwitter\.com|fixupx\.com)/(\w+)/status/(\d+)'
)


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
    """Check URLs against index, return (new_urls, duplicate_urls)."""
    new_urls = []
    duplicate_urls = []

    for url in urls:
        tweet_id = extract_tweet_id(url)
        if tweet_id and check_duplicate(tweet_id):
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
    print("\nBulk Import - X-Bookmark Knowledge Repository")
    print("-" * 45)
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
            content_parts.append(f"**[{i}/{thread.total_count}]**\n{tweet.text}")
        return "\n\n---\n\n".join(content_parts)
    else:
        return thread.tweets[0].text


def save_posts(posts: list[tuple[str, Thread]]) -> list[str]:
    """Save all posts, update index/tags once at end."""
    if not posts:
        return []

    index = load_index()
    tags_data = load_tags()
    saved_ids = []
    saved_paths = []

    print("\nSaving posts to archive...")
    for url, thread in posts:
        post_id = thread.tweets[0].id
        archived_at = datetime.now()
        file_path = get_post_path(post_id, archived_at)

        # Build content
        content = build_content(thread)

        # Build metadata (matching telegram_bot.py structure)
        metadata = {
            "id": post_id,
            "url": url,
            "author": {
                "handle": thread.author_handle,
                "name": thread.author_name,
            },
            "content": content,
            "archived_at": archived_at.isoformat(),
            "archived_via": "bulk_import",
        }

        # Thread info
        if thread.total_count > 1:
            metadata["thread"] = {
                "is_thread": True,
                "total": thread.total_count,
                "tweet_ids": [t.id for t in thread.tweets],
            }

        # Optional fields
        if thread.tweets[0].created_at:
            metadata["posted_at"] = thread.tweets[0].created_at

        # Empty tags/topics for bulk import
        metadata["tags"] = []
        metadata["topics"] = []

        # Collect media
        all_media = []
        for tweet in thread.tweets:
            for m in tweet.media:
                all_media.append({
                    "type": m.get("type", "image"),
                    "url": m.get("url", ""),
                })
        if all_media:
            metadata["media"] = all_media

        # Check for quoted tweets
        for tweet in thread.tweets:
            if tweet.quoted_tweet:
                metadata["quotes"] = {
                    "quoted_post_id": tweet.quoted_tweet.id,
                    "quoted_url": tweet.quoted_tweet.url,
                    "quoted_author": tweet.quoted_tweet.author_handle,
                    "quoted_text": tweet.quoted_tweet.text[:200],
                }
                break

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("---\n")
            yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)
            f.write("---\n\n")
            f.write(content)
            f.write("\n")

        # Update index
        index["posts"][post_id] = {
            "path": str(file_path.relative_to(ARCHIVE_DIR.parent.parent)),
            "author": thread.author_handle,
            "archived_at": archived_at.isoformat(),
            "tags": [],
            "topics": [],
            "is_thread": thread.total_count > 1,
        }

        saved_ids.append(post_id)
        saved_paths.append(file_path)
        print(f"  Saved: {post_id}")

    # Save index and tags ONCE at end
    save_index(index)
    save_tags(tags_data)

    return saved_ids


def generate_embeddings(saved_ids: list[str]) -> int:
    """Generate embeddings for all imported posts. Returns count of successful embeddings."""
    if not saved_ids:
        return 0

    print("\nGenerating embeddings...")

    try:
        from src.embeddings.service import get_embedding_service
        from src.embeddings.vector_store import get_vector_store
        from tools.utils import parse_post_file
    except ImportError as e:
        print(f"  Warning: Could not import embedding modules: {e}")
        print("  Skipping embedding generation. Run migrate_embeddings.py later.")
        return 0

    service = get_embedding_service()
    store = get_vector_store()
    success_count = 0

    index = load_index()

    for i, post_id in enumerate(saved_ids):
        print(f"  [{i+1}/{len(saved_ids)}] {post_id} ", end="", flush=True)

        try:
            # Get post path from index
            post_info = index["posts"].get(post_id)
            if not post_info:
                print("SKIP (not in index)")
                continue

            post_path = Path(ARCHIVE_DIR.parent.parent) / post_info["path"]
            post_data = parse_post_file(post_path)

            if not post_data:
                print("SKIP (parse failed)")
                continue

            # Build embedding text (content + author)
            content = post_data.get("content", "")
            author = post_data.get("author", {})
            author_handle = author.get("handle", "") if isinstance(author, dict) else str(author)

            embed_text = f"{content}\n\nAuthor: @{author_handle}"

            # Add tags/topics if present
            tags = post_data.get("tags", [])
            topics = post_data.get("topics", [])
            if tags:
                embed_text += f"\nTags: {', '.join(tags)}"
            if topics:
                embed_text += f"\nTopics: {', '.join(topics)}"

            # Generate and store embedding
            embedding = service.generate(embed_text)

            # Prepare metadata for vector store
            metadata = {
                "author_handle": author_handle,
                "archived_at": post_data.get("archived_at", ""),
                "archived_via": post_data.get("archived_via", "bulk_import"),
            }

            store.add_post(
                post_id=post_id,
                content=content,
                metadata=metadata,
                embedding=embedding
            )

            success_count += 1
            print("OK")

        except Exception as e:
            print(f"FAILED ({str(e)[:40]})")

    return success_count


def finalize(saved_ids: list[str], failures: list[tuple[str, str]], embed_count: int):
    """Single git commit and print summary."""
    # Git commit
    if saved_ids:
        print("\nCommitting changes...")
        git_sync(f"Bulk import: {len(saved_ids)} posts from Notion")

    # Write failures to log file
    if failures:
        log_path = Path("bulk_import_errors.log")
        with open(log_path, "w", encoding="utf-8") as f:
            for url, error in failures:
                f.write(f"{url}: {error}\n")
        print(f"\nErrors logged to: {log_path}")

    # Print summary
    print("\n" + "=" * 45)
    print("Import Complete!")
    print("=" * 45)
    print(f"\nSuccessfully imported: {len(saved_ids)}")
    if embed_count > 0:
        print(f"Embeddings generated: {embed_count}")
    if failures:
        print(f"Failed to fetch: {len(failures)}")
        for url, error in failures[:5]:  # Show first 5 failures
            print(f"  - {url}: {error}")
        if len(failures) > 5:
            print(f"  ... and {len(failures) - 5} more (see bulk_import_errors.log)")


def main():
    parser = argparse.ArgumentParser(
        description="Import X/Twitter posts from a Notion Markdown export",
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

    # Step 2: Check for duplicates
    print("Checking for duplicates...")
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

    # Step 5: Save posts
    saved_ids = save_posts(successes)

    # Step 6: Generate embeddings (optional)
    embed_count = 0
    if not args.no_embed and saved_ids:
        embed_count = generate_embeddings(saved_ids)

    # Step 7: Finalize
    finalize(saved_ids, failures, embed_count)


if __name__ == "__main__":
    main()
