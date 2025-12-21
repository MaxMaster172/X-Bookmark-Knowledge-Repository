#!/usr/bin/env python3
"""Search and retrieve posts from the archive."""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from utils import (
    load_index,
    load_tags,
    parse_post_file,
    format_post_for_llm,
    ARCHIVE_DIR,
    BASE_DIR,
)


def search_posts(
    query: str = None,
    tags: List[str] = None,
    topics: List[str] = None,
    author: str = None,
    importance: str = None,
    date_from: str = None,
    date_to: str = None,
    limit: int = None,
) -> List[dict]:
    """Search posts by various criteria."""
    index = load_index()
    results = []

    for post_id, post_info in index.get("posts", {}).items():
        # Load full post
        post_path = BASE_DIR / post_info["path"]
        if not post_path.exists():
            continue

        post = parse_post_file(post_path)
        meta = post.get("metadata", {})
        content = post.get("body", "")

        # Filter by author
        if author:
            post_author = meta.get("author", {}).get("handle", "")
            if author.lower() not in post_author.lower():
                continue

        # Filter by tags
        if tags:
            post_tags = [t.lower() for t in meta.get("tags", [])]
            if not any(t.lower() in post_tags for t in tags):
                continue

        # Filter by topics
        if topics:
            post_topics = [t.lower() for t in meta.get("topics", [])]
            if not any(t.lower() in post_topics for t in topics):
                continue

        # Filter by importance
        if importance:
            if meta.get("importance") != importance:
                continue

        # Filter by date range
        if date_from or date_to:
            post_date = meta.get("archived_at", meta.get("posted_at", ""))
            if post_date:
                try:
                    post_dt = datetime.fromisoformat(post_date.replace("Z", "+00:00"))
                    if date_from:
                        from_dt = datetime.fromisoformat(date_from)
                        if post_dt < from_dt:
                            continue
                    if date_to:
                        to_dt = datetime.fromisoformat(date_to)
                        if post_dt > to_dt:
                            continue
                except ValueError:
                    pass

        # Text search in content
        if query:
            search_text = f"{content} {meta.get('notes', '')}".lower()
            if query.lower() not in search_text:
                continue

        results.append({
            "id": post_id,
            "path": str(post_path),
            "metadata": meta,
            "body": content,
        })

    # Sort by archived date (newest first)
    results.sort(
        key=lambda x: x["metadata"].get("archived_at", ""),
        reverse=True
    )

    if limit:
        results = results[:limit]

    return results


def list_tags():
    """List all tags and their post counts."""
    tag_data = load_tags()
    print("\n📏 Tags:")
    print("-" * 30)
    for tag, posts in sorted(tag_data.get("tags", {}).items()):
        print(f"  {tag}: {len(posts)} posts")

    print("\n📚 Topics:")
    print("-" * 30)
    for topic, posts in sorted(tag_data.get("topics", {}).items()):
        print(f"  {topic}: {len(posts)} posts")


def list_authors():
    """List all authors and their post counts."""
    index = load_index()
    authors = {}
    for post_id, post_info in index.get("posts", {}).items():
        author = post_info.get("author", "unknown")
        authors[author] = authors.get(author, 0) + 1

    print("\n👤 Authors:")
    print("-" * 30)
    for author, count in sorted(authors.items(), key=lambda x: -x[1]):
        print(f"  @{author}: {count} posts")


def display_results(results: List[dict], format: str = "summary"):
    """Display search results."""
    if not results:
        print("\nNo posts found.")
        return

    print(f"\n📌 Found {len(results)} posts:\n")

    for i, post in enumerate(results, 1):
        meta = post["metadata"]

        if format == "summary":
            print(f"{i}. @{meta.get('author', {}).get('handle', 'unknown')}")
            print(f"   ID: {post['id']}")

            # Truncate content for summary
            content_preview = post["body"][:100].replace("\n", " ")
            if len(post["body"]) > 100:
                content_preview += "..."
            print(f"   {content_preview}")

            if meta.get("tags"):
                print(f"   Tags: {', '.join(meta['tags'])}")
            print()

        elif format == "full":
            print("-" * 60)
            print(format_post_for_llm(post))
            print()

        elif format == "json":
            print(json.dumps(post, indent=2, default=str))


def get_post(post_id: str) -> Optional[dict]:
    """Get a single post by ID."""
    index = load_index()
    if post_id not in index.get("posts", {}):
        return None

    post_info = index["posts"][post_id]
    post_path = BASE_DIR / post_info["path"]
    if not post_path.exists():
        return None

    post = parse_post_file(post_path)
    post["id"] = post_id
    post["path"] = str(post_path)
    return post


def main():
    parser = argparse.ArgumentParser(description="Search the X/Twitter archive")
    subparsers = parser.add_subparsers(dest="command")

    # Search command
    search_parser = subparsers.add_parser("find", help="Search posts")
    search_parser.add_argument("query", nargs="?", help="Text to search for")
    search_parser.add_argument("--tag", "-t", action="append", help="Filter by tag")
    search_parser.add_argument("--topic", "-T", action="append", help="Filter by topic")
    search_parser.add_argument("--author", "-a", help="Filter by author")
    search_parser.add_argument(
        "--importance", "-i",
        choices=["low", "medium", "high", "critical"],
        help="Filter by importance"
    )
    search_parser.add_argument("--from", dest="date_from", help="From date (YYYY-MM-DD)")
    search_parser.add_argument("--to", dest="date_to", help="To date (YYYY-MM-DD)")
    search_parser.add_argument("--limit", "-n", type=int, help="Limit results")
    search_parser.add_argument(
        "--format", "-f",
        choices=["summary", "full", "json"],
        default="summary",
        help="Output format"
    )

    # Get single post
    get_parser = subparsers.add_parser("get", help="Get a single post by ID")
    get_parser.add_argument("post_id", help="Post ID")
    get_parser.add_argument(
        "--format", "-f",
        choices=["full", "json"],
        default="full",
        help="Output format"
    )

    # List tags
    subparsers.add_parser("tags", help="List all tags and topics")

    # List authors
    subparsers.add_parser("authors", help="List all authors")

    # Stats
    subparsers.add_parser("stats", help="Show archive statistics")

    args = parser.parse_args()

    if args.command == "find":
        results = search_posts(
            query=args.query,
            tags=args.tag,
            topics=args.topic,
            author=args.author,
            importance=args.importance,
            date_from=args.date_from,
            date_to=args.date_to,
            limit=args.limit,
        )
        display_results(results, args.format)

    elif args.command == "get":
        post = get_post(args.post_id)
        if post:
            if args.format == "json":
                print(json.dumps(post, indent=2, default=str))
            else:
                print(format_post_for_llm(post))
        else:
            print(f"Post {args.post_id} not found")

    elif args.command == "tags":
        list_tags()

    elif args.command == "authors":
        list_authors()

    elif args.command == "stats":
        index = load_index()
        tag_data = load_tags()
        post_count = len(index.get("posts", {}))
        tag_count = len(tag_data.get("tags", {}))
        topic_count = len(tag_data.get("topics", {}))

        print("\n📊 Archive Statistics:")
        print("-" * 30)
        print(f"  Total posts: {post_count}")
        print(f"  Unique tags: {tag_count}")
        print(f"  Unique topics: {topic_count}")
        if index.get("last_updated"):
            print(f"  Last updated: {index['last_updated']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
