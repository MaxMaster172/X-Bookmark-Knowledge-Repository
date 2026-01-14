#!/usr/bin/env python3
"""
Export X-Bookmark posts to Obsidian vault.

USAGE:
    # Incremental export (only new posts since last export)
    python scripts/export_to_obsidian.py --vault-path "C:\\Users\\maxma\\Obsidian"

    # Full export (re-export all posts)
    python scripts/export_to_obsidian.py --vault-path "C:\\Users\\maxma\\Obsidian" --full

    # Dry run (preview without writing)
    python scripts/export_to_obsidian.py --vault-path "C:\\Users\\maxma\\Obsidian" --dry-run --verbose

Exports posts to: {vault}/Clippings/X-Bookmark/
State file: {vault}/.x-bookmark-export-state.json
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_paths = [
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

from src.supabase import get_supabase_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def sanitize_filename(name: str) -> str:
    """Convert a string to a safe filename."""
    # Remove or replace problematic characters
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", "-", name)
    return name[:100]  # Limit length


def load_state(vault_path: Path) -> dict:
    """Load export state from vault."""
    state_file = vault_path / ".x-bookmark-export-state.json"
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_export": None, "exported_post_ids": []}


def save_state(vault_path: Path, state: dict) -> None:
    """Save export state to vault."""
    state_file = vault_path / ".x-bookmark-export-state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def format_frontmatter(post: dict, entities: list, theses: list) -> str:
    """Generate YAML frontmatter for a post."""
    # Parse dates
    posted_at = post.get("posted_at", "")
    if posted_at:
        try:
            posted_dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
            published = posted_dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            published = ""
    else:
        published = ""

    created = datetime.now().strftime("%Y-%m-%d")
    author_handle = post.get("author_handle", "unknown")

    lines = [
        "---",
        f'title: "Post by @{author_handle}"',
        f'source: "{post.get("url", "")}"',
        "author:",
        f'  - "[[@{author_handle}]]"',
    ]

    if published:
        lines.append(f"published: {published}")
    lines.append(f"created: {created}")

    lines.append("tags:")
    lines.append('  - "clippings"')
    lines.append('  - "x-bookmark"')

    # Add entity detections if present
    if entities:
        lines.append("detected_entities:")
        for e in entities:
            lines.append(f'  - name: "{e["name"]}"')
            if e.get("category"):
                lines.append(f'    category: "{e["category"]}"')
            lines.append(f'    confidence: {e.get("confidence", 1.0):.2f}')

    # Add thesis detections if present
    if theses:
        lines.append("detected_theses:")
        for t in theses:
            lines.append(f'  - name: "{t["name"]}"')
            if t.get("category"):
                lines.append(f'    category: "{t["category"]}"')
            lines.append(f'    confidence: {t.get("confidence", 1.0):.2f}')
            if t.get("contribution"):
                # Escape quotes in contribution
                contribution = t["contribution"].replace('"', '\\"')
                lines.append(f'    contribution: "{contribution}"')

    lines.append("---")
    return "\n".join(lines)


def format_body(post: dict, media: list) -> str:
    """Generate markdown body for a post."""
    author_name = post.get("author_name", post.get("author_handle", "Unknown"))
    author_handle = post.get("author_handle", "unknown")
    url = post.get("url", "")
    content = post.get("content", "")

    # Format posted date
    posted_at = post.get("posted_at", "")
    if posted_at:
        try:
            posted_dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
            date_str = posted_dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            date_str = "Unknown date"
    else:
        date_str = "Unknown date"

    lines = [
        f"**{author_name}** @{author_handle} [{date_str}]({url})",
        "",
        content,
    ]

    # Add quoted tweet if present
    quoted_text = post.get("quoted_text")
    quoted_author = post.get("quoted_author")
    if quoted_text:
        lines.append("")
        lines.append(f"> {quoted_text}")
        if quoted_author:
            lines.append(f"> — @{quoted_author}")

    # Add image descriptions
    image_descriptions = [
        m.get("description")
        for m in media
        if m.get("type") == "photo" and m.get("description")
    ]
    if image_descriptions:
        lines.append("")
        lines.append("---")
        for desc in image_descriptions:
            lines.append(f"*Image: {desc}*")

    return "\n".join(lines)


def export_post(
    post: dict,
    entities: list,
    theses: list,
    media: list,
    output_dir: Path,
    dry_run: bool = False,
) -> str:
    """Export a single post to markdown file."""
    frontmatter = format_frontmatter(post, entities, theses)
    body = format_body(post, media)
    content = f"{frontmatter}\n{body}\n"

    # Generate filename
    author = sanitize_filename(post.get("author_handle", "unknown"))
    post_id = post.get("id", "unknown")[:12]

    posted_at = post.get("posted_at", "")
    if posted_at:
        try:
            posted_dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
            date_str = posted_dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            date_str = "unknown-date"
    else:
        date_str = "unknown-date"

    filename = f"{author}-{date_str}-{post_id}.md"
    filepath = output_dir / filename

    if not dry_run:
        filepath.write_text(content, encoding="utf-8")

    return str(filepath)


def main():
    parser = argparse.ArgumentParser(
        description="Export X-Bookmark posts to Obsidian vault"
    )
    parser.add_argument(
        "--vault-path",
        required=True,
        help="Path to Obsidian vault root",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full export (ignore last export timestamp)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without writing files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        logger.error(f"Vault path does not exist: {vault_path}")
        sys.exit(1)

    output_dir = vault_path / "Clippings" / "X-Bookmark"

    # Create output directory if needed
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Exporting to: {output_dir}")

    # Load state
    state = load_state(vault_path)
    last_export = state.get("last_export")

    if args.full:
        logger.info("Full export mode - ignoring previous state")
        last_export = None
    elif last_export:
        logger.info(f"Incremental export since: {last_export}")
    else:
        logger.info("No previous export - exporting all posts")

    # Connect to Supabase
    db = get_supabase_client()

    # Get posts to export
    if last_export:
        last_export_dt = datetime.fromisoformat(last_export.replace("Z", "+00:00"))
        posts = db.get_posts_since(last_export_dt)
    else:
        posts = db.get_all_posts()

    logger.info(f"Found {len(posts)} posts to export")

    if len(posts) == 0:
        logger.info("No new posts to export")
        return

    # Export each post
    stats = {"exported": 0, "skipped": 0, "errors": 0}
    exported_ids = list(state.get("exported_post_ids", []))

    for i, post in enumerate(posts):
        post_id = post.get("id")
        try:
            # Get linked entities and theses
            entities = db.get_post_entities(post_id)
            theses = db.get_post_theses(post_id)
            media = db.get_post_media(post_id)

            logger.debug(
                f"Post {post_id[:12]}: {len(entities)} entities, {len(theses)} theses"
            )

            filepath = export_post(
                post, entities, theses, media, output_dir, dry_run=args.dry_run
            )

            if args.dry_run:
                logger.info(f"[DRY RUN] Would write: {filepath}")
            else:
                logger.info(f"Exported: {filepath}")

            stats["exported"] += 1
            if post_id not in exported_ids:
                exported_ids.append(post_id)

        except Exception as e:
            logger.error(f"Error exporting post {post_id}: {e}")
            stats["errors"] += 1

        # Progress logging
        if (i + 1) % 10 == 0:
            logger.info(f"Progress: {i + 1}/{len(posts)}")

    # Update state
    if not args.dry_run:
        state["last_export"] = datetime.now().isoformat()
        state["exported_post_ids"] = exported_ids
        save_state(vault_path, state)
        logger.info(f"State saved to {vault_path / '.x-bookmark-export-state.json'}")

    # Summary
    logger.info("=" * 50)
    logger.info("Export Summary:")
    logger.info(f"  Exported: {stats['exported']}")
    logger.info(f"  Errors: {stats['errors']}")
    if args.dry_run:
        logger.info("  (Dry run - no files written)")


if __name__ == "__main__":
    main()
