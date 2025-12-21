"""Shared utilities for the X/Twitter archive system."""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

# Base paths
BASE_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = BASE_DIR / "archive" / "posts"
DATA_DIR = BASE_DIR / "data"
EXPORTS_DIR = BASE_DIR / "exports"
COLLECTIONS_DIR = BASE_DIR / "archive" / "collections"

# Ensure directories exist
for d in [ARCHIVE_DIR, DATA_DIR, EXPORTS_DIR, COLLECTIONS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def extract_post_id(url: str) -> Optional[str]:
    """Extract post ID from an X/Twitter URL."""
    patterns = [
        r'(?:twitter|x)\.com/\w+/status/(\d+)',
        r'(?:twitter|x)\.com/i/web/status/(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_handle(url: str) -> Optional[str]:
    """Extract handle from an X/Twitter URL."""
    match = re.search(r'(?:twitter|x)\.com/(\w+)/status/', url)
    if match:
        return match.group(1)
    return None


def get_post_path(post_id: str, archived_at: datetime = None) -> Path:
    """Get the file path for a post based on its ID and archive date."""
    if archived_at is None:
        archived_at = datetime.now()
    year = archived_at.strftime("%Y")
    month = archived_at.strftime("%m")
    dir_path = ARCHIVE_DIR / year / month
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path / f"{post_id}.md"


def load_index() -> dict:
    """Load the main index file."""
    index_path = DATA_DIR / "index.json"
    if index_path.exists():
        with open(index_path) as f:
            return json.load(f)
    return {"posts": {}, "last_updated": None}


def save_index(index: dict):
    """Save the main index file."""
    index["last_updated"] = datetime.now().isoformat()
    index_path = DATA_DIR / "index.json"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)


def load_tags() -> dict:
    """Load the tags taxonomy file."""
    tags_path = DATA_DIR / "tags.json"
    if tags_path.exists():
        with open(tags_path) as f:
            return json.load(f)
    return {"tags": {}, "topics": {}}


def save_tags(tags: dict):
    """Save the tags taxonomy file."""
    tags_path = DATA_DIR / "tags.json"
    with open(tags_path, "w") as f:
        json.dump(tags, f, indent=2)


def parse_post_file(file_path: Path) -> dict:
    """Parse a post markdown file and extract frontmatter + content."""
    with open(file_path) as f:
        content = f.read()

    # Parse YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            import yaml
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
            return {"metadata": frontmatter, "body": body}

    return {"metadata": {}, "body": content}


def format_post_for_llm(post: dict, include_metadata: bool = True) -> str:
    """Format a post for LLM consumption."""
    lines = []
    meta = post.get("metadata", {})

    if include_metadata:
        lines.append(f"## Post by @{meta.get('author', {}).get('handle', 'unknown')}")
        if meta.get("posted_at"):
            lines.append(f"**Date:** {meta['posted_at']}")
        if meta.get("url"):
            lines.append(f"**URL:** {meta['url']}")
        if meta.get("tags"):
            lines.append(f"**Tags:** {', '.join(meta['tags'])}")
        if meta.get("topics"):
            lines.append(f"**Topics:** {', '.join(meta['topics'])}")
        lines.append("")

    lines.append("### Content")
    lines.append(post.get("body", meta.get("content", "")))

    if meta.get("notes"):
        lines.append("")
        lines.append("### Notes")
        lines.append(meta["notes"])

    return "\n".join(lines)
