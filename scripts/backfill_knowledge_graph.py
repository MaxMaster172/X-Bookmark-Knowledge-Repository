#!/usr/bin/env python3
"""
Backfill knowledge graph analysis for posts without entity/thesis detection.

Usage:
    python scripts/backfill_knowledge_graph.py --dry-run    # Preview what would be analyzed
    python scripts/backfill_knowledge_graph.py --limit 5    # Process 5 posts
    python scripts/backfill_knowledge_graph.py              # Process all

Environment variables required:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_SERVICE_KEY: Your Supabase service role key
- ANTHROPIC_API_KEY: Your Anthropic API key
"""

import sys
import time
import logging
import argparse
from pathlib import Path

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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.supabase.client import get_supabase_client
from src.knowledge_graph.analyzer import get_post_analyzer

# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Rate limiting - be gentle with Claude API
DELAY_BETWEEN_POSTS = 2.0  # seconds


def get_posts_needing_backfill(db) -> list[dict]:
    """Get all posts that don't have entity or thesis links."""
    # Get all post IDs
    all_posts = db.get_all_posts()
    all_post_ids = {p["id"] for p in all_posts}

    # Get posts with entities
    result = db._client.table("post_entities").select("post_id").execute()
    posts_with_entities = {row["post_id"] for row in result.data}

    # Get posts with theses
    result = db._client.table("post_theses").select("post_id").execute()
    posts_with_theses = {row["post_id"] for row in result.data}

    # Posts with any analysis
    posts_analyzed = posts_with_entities | posts_with_theses

    # Filter to posts needing backfill
    needs_backfill_ids = all_post_ids - posts_analyzed

    # Return full post objects for those needing backfill
    return [p for p in all_posts if p["id"] in needs_backfill_ids]


def backfill_knowledge_graph(dry_run: bool = False, limit: int = None):
    """
    Run knowledge graph analysis on posts without entity/thesis detection.

    Args:
        dry_run: If True, just show what would be processed
        limit: Max number of posts to process
    """
    db = get_supabase_client()

    # Get posts needing backfill
    posts = get_posts_needing_backfill(db)
    total_needing = len(posts)

    logger.info(f"Total posts: {db.count_posts()}")
    logger.info(f"Posts needing backfill: {total_needing}")

    if limit:
        posts = posts[:limit]
        logger.info(f"Processing {len(posts)} posts (limited)")

    if dry_run:
        logger.info("=== DRY RUN - No changes will be made ===")
        for i, post in enumerate(posts, 1):
            content_preview = (post.get("content") or "")[:80].replace("\n", " ")
            logger.info(f"  {i}. [{post['id'][:8]}] @{post.get('author_handle', '?')}: {content_preview}...")
        return

    # Initialize analyzer
    analyzer = get_post_analyzer(db)

    processed = 0
    errors = 0

    for i, post in enumerate(posts, 1):
        post_id = post["id"]
        content = post.get("content") or ""
        author = post.get("author_handle") or "unknown"

        # Get any existing tags/topics from the post
        tags = post.get("tags") or []
        topics = post.get("topics") or []
        notes = post.get("notes")

        logger.info(f"[{i}/{len(posts)}] Analyzing post {post_id[:8]}... (@{author})")

        try:
            # Run analysis
            result = analyzer.analyze_post(
                content=content,
                author=author,
                tags=tags,
                topics=topics,
                notes=notes,
            )

            if result.has_results:
                # Apply to database
                stats = analyzer.apply_analysis(post_id, result)
                logger.info(
                    f"  -> Found {len(result.entities)} entities, {len(result.theses)} theses. "
                    f"Created: {stats['created']}, Linked: {stats['linked']}"
                )
            else:
                logger.info(f"  -> No entities/theses detected")

            processed += 1

        except Exception as e:
            logger.error(f"  -> Error: {e}")
            errors += 1

        # Rate limit
        if i < len(posts):
            time.sleep(DELAY_BETWEEN_POSTS)

    logger.info("=" * 50)
    logger.info(f"Backfill complete: {processed} processed, {errors} errors")


def main():
    parser = argparse.ArgumentParser(
        description="Backfill knowledge graph analysis for posts"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be processed without making changes",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of posts to process",
    )

    args = parser.parse_args()

    backfill_knowledge_graph(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
