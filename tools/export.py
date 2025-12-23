#!/usr/bin/env python3
"""Export archive in LLM-optimized formats."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from utils import (
    load_index,
    load_tags,
    parse_post_file,
    format_post_for_llm,
    EXPORTS_DIR,
    BASE_DIR,
)
from search import search_posts


def export_markdown(
    posts: List[dict],
    output_path: Path,
    title: str = "X/Twitter Archive Export",
    include_toc: bool = True,
):
    """Export posts to a single markdown file optimized for LLM context."""
    lines = [
        f"# {title}",
        "",
        f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*Total posts: {len(posts)}*",
        "",
    ]

    if include_toc:
        lines.append("## Table of Contents")
        lines.append("")
        for i, post in enumerate(posts, 1):
            meta = post.get("metadata", {})
            author = meta.get("author", {}).get("handle", "unknown")
            preview = post.get("body", "")[:50].replace("\n", " ") + "..."
            lines.append(f"{i}. [@{author}] {preview}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Posts")
    lines.append("")

    for post in posts:
        lines.append(format_post_for_llm(post))
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return output_path


def export_json(posts: List[dict], output_path: Path):
    """Export posts to JSON format."""
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "post_count": len(posts),
        "posts": posts,
    }

    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2, default=str)

    return output_path


def export_llm_context(
    posts: List[dict],
    output_path: Path,
    system_prompt: str = None,
):
    """
    Export in a format optimized for LLM context injection.
    Creates a structured document designed to be pasted into LLM conversations.
    """
    lines = [
        "<archived_twitter_posts>",
        "",
    ]

    if system_prompt:
        lines.append(f"<context>{system_prompt}</context>")
        lines.append("")

    for post in posts:
        meta = post.get("metadata", {})
        lines.append("<post>")
        lines.append(f"  <id>{meta.get('id', 'unknown')}</id>")
        lines.append(f"  <author>@{meta.get('author', {}).get('handle', 'unknown')}</author>")
        if meta.get("posted_at"):
            lines.append(f"  <date>{meta['posted_at']}</date>")
        if meta.get("tags"):
            lines.append(f"  <tags>{', '.join(meta['tags'])}</tags>")
        if meta.get("topics"):
            lines.append(f"  <topics>{', '.join(meta['topics'])}</topics>")
        lines.append(f"  <content>{post.get('body', '')}</content>")
        if meta.get("notes"):
            lines.append(f"  <user_notes>{meta['notes']}</user_notes>")
        lines.append("</post>")
        lines.append("")

    lines.append("</archived_twitter_posts>")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return output_path


def export_summary(posts: List[dict], output_path: Path):
    """
    Export a condensed summary optimized for quick LLM reference.
    Good for when you need to fit many posts in limited context.
    """
    lines = [
        "# Twitter/X Archive Summary",
        "",
        f"Total: {len(posts)} posts",
        "",
    ]

    # Group by topic
    by_topic = {}
    for post in posts:
        meta = post.get("metadata", {})
        topics = meta.get("topics", ["uncategorized"])
        for topic in topics:
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(post)

    for topic, topic_posts in sorted(by_topic.items()):
        lines.append(f"## {topic.title()}")
        lines.append("")
        for post in topic_posts:
            meta = post.get("metadata", {})
            author = meta.get("author", {}).get("handle", "unknown")
            content = post.get("body", "")[:150].replace("\n", " ")
            if len(post.get("body", "")) > 150:
                content += "..."
            lines.append(f"- **@{author}**: {content}")
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return output_path


def export_by_author(posts: List[dict], output_dir: Path):
    """Export posts grouped by author into separate files."""
    by_author = {}
    for post in posts:
        meta = post.get("metadata", {})
        author = meta.get("author", {}).get("handle", "unknown")
        if author not in by_author:
            by_author[author] = []
        by_author[author].append(post)

    output_dir.mkdir(parents=True, exist_ok=True)

    for author, author_posts in by_author.items():
        output_path = output_dir / f"{author}.md"
        export_markdown(
            author_posts,
            output_path,
            title=f"Posts by @{author}",
            include_toc=False
        )
        print(f"  Exported {len(author_posts)} posts to {output_path}")


def export_by_topic(posts: List[dict], output_dir: Path):
    """Export posts grouped by topic into separate files."""
    by_topic = {}
    for post in posts:
        meta = post.get("metadata", {})
        topics = meta.get("topics", ["uncategorized"])
        for topic in topics:
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(post)

    output_dir.mkdir(parents=True, exist_ok=True)

    for topic, topic_posts in by_topic.items():
        output_path = output_dir / f"{topic}.md"
        export_markdown(
            topic_posts,
            output_path,
            title=f"Posts about {topic.title()}",
            include_toc=False
        )
        print(f"  Exported {len(topic_posts)} posts to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Export archive in LLM-optimized formats"
    )

    parser.add_argument(
        "format",
        choices=["markdown", "json", "llm", "summary", "by-author", "by-topic"],
        help="Export format"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file/directory path"
    )
    parser.add_argument(
        "--tag", "-t",
        action="append",
        help="Filter by tag"
    )
    parser.add_argument(
        "--topic", "-T",
        action="append",
        help="Filter by topic"
    )
    parser.add_argument(
        "--author", "-a",
        help="Filter by author"
    )
    parser.add_argument(
        "--importance", "-i",
        choices=["low", "medium", "high", "critical"],
        help="Filter by importance"
    )
    parser.add_argument(
        "--query", "-q",
        help="Text search query"
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        help="Limit number of posts"
    )
    parser.add_argument(
        "--context",
        help="System prompt/context for LLM export format"
    )

    args = parser.parse_args()

    # Get posts based on filters
    posts = search_posts(
        query=args.query,
        tags=args.tag,
        topics=args.topic,
        author=args.author,
        importance=args.importance,
        limit=args.limit,
    )

    if not posts:
        print("No posts found matching criteria.")
        return

    print(f"Exporting {len(posts)} posts...")

    # Determine output path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.format == "markdown":
        output_path = Path(args.output) if args.output else EXPORTS_DIR / f"export_{timestamp}.md"
        export_markdown(posts, output_path)
        print(f"Exported to: {output_path}")

    elif args.format == "json":
        output_path = Path(args.output) if args.output else EXPORTS_DIR / f"export_{timestamp}.json"
        export_json(posts, output_path)
        print(f"Exported to: {output_path}")

    elif args.format == "llm":
        output_path = Path(args.output) if args.output else EXPORTS_DIR / f"llm_context_{timestamp}.txt"
        export_llm_context(posts, output_path, args.context)
        print(f"Exported to: {output_path}")

    elif args.format == "summary":
        output_path = Path(args.output) if args.output else EXPORTS_DIR / f"summary_{timestamp}.md"
        export_summary(posts, output_path)
        print(f"Exported to: {output_path}")

    elif args.format == "by-author":
        output_dir = Path(args.output) if args.output else EXPORTS_DIR / "by_author"
        export_by_author(posts, output_dir)
        print(f"Exported to: {output_dir}/")

    elif args.format == "by-topic":
        output_dir = Path(args.output) if args.output else EXPORTS_DIR / "by_topic"
        export_by_topic(posts, output_dir)
        print(f"Exported to: {output_dir}/")


if __name__ == "__main__":
    main()
