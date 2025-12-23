"""
Post Parser - Reads and parses markdown posts with YAML frontmatter.

Expected post format:
---
id: "1234567890"
author: username
date: 2024-01-15
url: https://x.com/user/status/123
tags: [tag1, tag2]
topics: [topic1]
importance: medium
---

Tweet content here...
"""

import frontmatter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Iterator
from datetime import date
import logging

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"
DEFAULT_POSTS_DIR = DEFAULT_DATA_DIR / "posts"


@dataclass
class Post:
    """Represents a parsed post."""

    id: str
    content: str
    author: Optional[str] = None
    date: Optional[date] = None
    url: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    importance: Optional[str] = None
    notes: Optional[str] = None
    file_path: Optional[Path] = None

    def to_metadata(self) -> dict:
        """Convert to metadata dict for vector store."""
        return {
            "author": self.author,
            "date": self.date.isoformat() if self.date else None,
            "url": self.url,
            "tags": self.tags,
            "topics": self.topics,
            "importance": self.importance,
            "notes": self.notes,
        }

    def to_embedding_text(self) -> str:
        """
        Create text representation for embedding.

        Combines content with metadata for richer semantic representation.
        """
        parts = [self.content]

        if self.author:
            parts.append(f"Author: {self.author}")

        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")

        if self.topics:
            parts.append(f"Topics: {', '.join(self.topics)}")

        if self.notes:
            parts.append(f"Notes: {self.notes}")

        return "\n\n".join(parts)


class PostParser:
    """Parses markdown posts from the data directory."""

    def __init__(self, posts_dir: Optional[Path] = None):
        """
        Initialize the parser.

        Args:
            posts_dir: Directory containing markdown posts.
                      Defaults to data/posts/
        """
        self.posts_dir = posts_dir or DEFAULT_POSTS_DIR

    def parse_file(self, file_path: Path) -> Optional[Post]:
        """
        Parse a single markdown file into a Post.

        Args:
            file_path: Path to the markdown file

        Returns:
            Post object or None if parsing fails
        """
        try:
            post = frontmatter.load(file_path)

            # Extract metadata with defaults
            metadata = post.metadata
            post_id = metadata.get("id", file_path.stem)

            # Parse date if present
            post_date = metadata.get("date")
            if isinstance(post_date, str):
                try:
                    post_date = date.fromisoformat(post_date)
                except ValueError:
                    post_date = None

            return Post(
                id=str(post_id),
                content=post.content.strip(),
                author=metadata.get("author"),
                date=post_date,
                url=metadata.get("url"),
                tags=metadata.get("tags", []),
                topics=metadata.get("topics", []),
                importance=metadata.get("importance"),
                notes=metadata.get("notes"),
                file_path=file_path,
            )

        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None

    def iter_posts(self) -> Iterator[Post]:
        """
        Iterate over all posts in the posts directory.

        Yields:
            Post objects for each valid markdown file
        """
        if not self.posts_dir.exists():
            logger.warning(f"Posts directory does not exist: {self.posts_dir}")
            return

        # Find all markdown files recursively
        for md_file in self.posts_dir.rglob("*.md"):
            post = self.parse_file(md_file)
            if post:
                yield post

    def get_all_posts(self) -> list[Post]:
        """Get all posts as a list."""
        return list(self.iter_posts())

    def count_posts(self) -> int:
        """Count total markdown files in posts directory."""
        if not self.posts_dir.exists():
            return 0
        return len(list(self.posts_dir.rglob("*.md")))


def get_post_parser(posts_dir: Optional[Path] = None) -> PostParser:
    """Get a post parser instance."""
    return PostParser(posts_dir)
