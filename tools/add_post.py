#!/usr/bin/env python3
"""CLI tool to manually add X/Twitter posts to the archive."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import yaml

from utils import (
    extract_post_id,
    extract_handle,
    get_post_path,
    load_index,
    save_index,
    load_tags,
    save_tags,
    ARCHIVE_DIR,
)


def create_post_file(
    url: str,
    content: str,
    author_handle: str = None,
    author_name: str = None,
    posted_at: str = None,
    tags: list = None,
    topics: list = None,
    notes: str = None,
    importance: str = "medium",
    thread_position: int = None,
    thread_total: int = None,
    media_descriptions: list = None,
) -> Path:
    """Create a new post file in the archive."""

    post_id = extract_post_id(url)
    if not post_id:
        raise ValueError(f"Could not extract post ID from URL: {url}")

    if not author_handle:
        author_handle = extract_handle(url) or "unknown"

    archived_at = datetime.now()
    file_path = get_post_path(post_id, archived_at)

    # Check if already exists
    if file_path.exists():
        print(f"Warning: Post {post_id} already exists at {file_path}")
        response = input("Overwrite? [y/N]: ")
        if response.lower() != 'y':
            return None

    # Build metadata
    metadata = {
        "id": post_id,
        "url": url,
        "author": {
            "handle": author_handle,
        },
        "content": content,
        "archived_at": archived_at.isoformat(),
        "importance": importance,
    }

    if author_name:
        metadata["author"]["name"] = author_name

    if posted_at:
        metadata["posted_at"] = posted_at

    if tags:
        metadata["tags"] = tags

    if topics:
        metadata["topics"] = topics

    if notes:
        metadata["notes"] = notes

    if thread_position and thread_total:
        metadata["thread"] = {
            "is_thread": True,
            "position": thread_position,
            "total": thread_total,
        }

    if media_descriptions:
        metadata["media"] = [
            {"type": "image", "description": desc}
            for desc in media_descriptions
        ]

    # Write file with YAML frontmatter
    with open(file_path, "w") as f:
        f.write("---\n")
        yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)
        f.write("---\n\n")
        f.write(content)
        f.write("\n")

    # Update index
    index = load_index()
    index["posts"][post_id] = {
        "path": str(file_path.relative_to(ARCHIVE_DIR.parent.parent)),
        "author": author_handle,
        "archived_at": archived_at.isoformat(),
        "tags": tags or [],
        "topics": topics or [],
        "importance": importance,
    }
    save_index(index)

    # Update tags
    if tags or topics:
        tag_data = load_tags()
        for tag in (tags or []):
            if tag not in tag_data["tags"]:
                tag_data["tags"][tag] = []
            tag_data["tags"][tag].append(post_id)
        for topic in (topics or []):
            if topic not in tag_data["topics"]:
                tag_data["topics"][topic] = []
            tag_data["topics"][topic].append(post_id)
        save_tags(tag_data)

    return file_path


def interactive_add():
    """Interactive mode for adding a post."""
    print("\n📌 Add X/Twitter Post to Archive\n")
    print("-" * 40)

    url = input("Post URL: ").strip()
    if not url:
        print("Error: URL is required")
        return

    post_id = extract_post_id(url)
    if not post_id:
        print("Error: Invalid X/Twitter URL")
        return

    print(f"\nExtracted post ID: {post_id}")

    author_handle = extract_handle(url)
    author_input = input(f"Author handle [{author_handle}]: ").strip()
    if author_input:
        author_handle = author_input.lstrip("@")

    author_name = input("Author display name (optional): ").strip() or None

    print("\nPaste the post content (enter a blank line when done):")
    content_lines = []
    while True:
        line = input()
        if line == "":
            break
        content_lines.append(line)
    content = "\n".join(content_lines)

    if not content:
        print("Error: Content is required")
        return

    posted_at = input("\nPost date (YYYY-MM-DD, optional): ").strip() or None

    tags_input = input("Tags (comma-separated, e.g., 'ai,coding,insight'): ").strip()
    tags = [t.strip() for t in tags_input.split(",")] if tags_input else None

    topics_input = input("Topics (comma-separated, e.g., 'machine-learning,python'): ").strip()
    topics = [t.strip() for t in topics_input.split(",")] if topics_input else None

    print("\nImportance level:")
    print("  1. low")
    print("  2. medium")
    print("  3. high")
    print("  4. critical")
    importance_choice = input("Choose [2]: ").strip() or "2"
    importance_map = {"1": "low", "2": "medium", "3": "high", "4": "critical"}
    importance = importance_map.get(importance_choice, "medium")

    notes = input("\nYour notes about this post (optional): ").strip() or None

    # Thread info
    is_thread = input("\nIs this part of a thread? [y/N]: ").strip().lower() == 'y'
    thread_position = None
    thread_total = None
    if is_thread:
        thread_position = int(input("Position in thread: ").strip() or "1")
        thread_total = int(input("Total posts in thread: ").strip() or "1")

    # Media
    has_media = input("\nDoes this post have images? [y/N]: ").strip().lower() == 'y'
    media_descriptions = None
    if has_media:
        print("Describe each image (enter blank line when done):")
        media_descriptions = []
        while True:
            desc = input("Image description: ").strip()
            if not desc:
                break
            media_descriptions.append(desc)

    # Create the post
    try:
        file_path = create_post_file(
            url=url,
            content=content,
            author_handle=author_handle,
            author_name=author_name,
            posted_at=posted_at,
            tags=tags,
            topics=topics,
            notes=notes,
            importance=importance,
            thread_position=thread_position,
            thread_total=thread_total,
            media_descriptions=media_descriptions,
        )

        if file_path:
            print(f"\n✅ Post archived successfully!")
            print(f"   Location: {file_path}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def quick_add(args):
    """Quick add mode with command line arguments."""
    tags = args.tags.split(",") if args.tags else None
    topics = args.topics.split(",") if args.topics else None

    try:
        file_path = create_post_file(
            url=args.url,
            content=args.content,
            author_handle=args.author,
            posted_at=args.date,
            tags=tags,
            topics=topics,
            notes=args.notes,
            importance=args.importance,
        )

        if file_path:
            print(f"Archived: {file_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Add X/Twitter posts to your archive"
    )

    subparsers = parser.add_subparsers(dest="command")

    # Interactive mode (default)
    subparsers.add_parser("interactive", help="Interactive mode")

    # Quick add mode
    quick_parser = subparsers.add_parser("quick", help="Quick add with arguments")
    quick_parser.add_argument("url", help="Post URL")
    quick_parser.add_argument("content", help="Post content text")
    quick_parser.add_argument("--author", "-a", help="Author handle")
    quick_parser.add_argument("--date", "-d", help="Post date (YYYY-MM-DD)")
    quick_parser.add_argument("--tags", "-t", help="Comma-separated tags")
    quick_parser.add_argument("--topics", "-T", help="Comma-separated topics")
    quick_parser.add_argument("--notes", "-n", help="Your notes")
    quick_parser.add_argument(
        "--importance", "-i",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="Importance level"
    )

    args = parser.parse_args()

    if args.command == "quick":
        quick_add(args)
    else:
        interactive_add()


if __name__ == "__main__":
    main()
