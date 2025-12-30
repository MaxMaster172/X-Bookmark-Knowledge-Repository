#!/usr/bin/env python3
"""
Backfill image descriptions for existing media items.

Usage:
    python scripts/backfill_image_descriptions.py --dry-run    # Preview changes
    python scripts/backfill_image_descriptions.py --limit 10   # Process 10 images
    python scripts/backfill_image_descriptions.py              # Process all

Environment variables required:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_SERVICE_KEY: Your Supabase service role key
- ANTHROPIC_API_KEY: Your Anthropic API key

Optional:
- REGENERATE_EMBEDDINGS: Set to "true" to regenerate post embeddings after backfill
"""

import os
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
from src.vision import get_image_extractor
from src.embeddings.service import get_embedding_service

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Rate limiting
DELAY_BETWEEN_IMAGES = 1.0  # 1 second between API calls


def backfill_descriptions(
    dry_run: bool = False,
    limit: int = None,
    regenerate_embeddings: bool = False,
):
    """
    Backfill descriptions for media items without them.

    Args:
        dry_run: If True, only preview what would be processed
        limit: Maximum number of images to process
        regenerate_embeddings: If True, regenerate embeddings for affected posts
    """
    logger.info("Starting image description backfill...")

    # Initialize clients
    try:
        db = get_supabase_client()
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return

    if not dry_run:
        try:
            extractor = get_image_extractor()
        except Exception as e:
            logger.error(f"Failed to initialize image extractor: {e}")
            return

    # Get media without descriptions
    media_limit = limit if limit else 500
    media_items = db.get_media_without_descriptions(limit=media_limit)

    if not media_items:
        logger.info("No media items need description extraction.")
        return

    logger.info(f"Found {len(media_items)} media items without descriptions")

    if dry_run:
        logger.info("DRY RUN - No changes will be made")
        for item in media_items[:10]:  # Show first 10
            logger.info(f"  Would process: {item['url'][:60]}...")
        if len(media_items) > 10:
            logger.info(f"  ... and {len(media_items) - 10} more")
        return

    # Track affected posts for embedding regeneration
    affected_post_ids = set()
    success_count = 0
    error_count = 0

    for i, item in enumerate(media_items):
        if limit and i >= limit:
            break

        logger.info(f"Processing {i + 1}/{len(media_items)}: {item['url'][:50]}...")

        try:
            # Get post context for better extraction
            post_context = None
            if item.get("post_id"):
                post = db.get_post(item["post_id"])
                if post:
                    post_context = post.get("content", "")[:500]

            # Extract description
            result = extractor.describe_image(
                image_url=item["url"],
                post_context=post_context,
            )

            if result and result.get("description"):
                # Update the media item
                success = db.update_media(
                    media_id=item["id"],
                    category=result["category"],
                    description=result["description"],
                    extraction_model=result["extraction_model"],
                )

                if success:
                    success_count += 1
                    affected_post_ids.add(item["post_id"])
                    logger.info(f"  Updated: {result['category']} description")
                else:
                    error_count += 1
                    logger.warning(f"  Failed to update database")
            else:
                error_count += 1
                logger.warning(f"  No description extracted")

        except Exception as e:
            error_count += 1
            logger.error(f"  Error: {e}")

        # Rate limiting
        time.sleep(DELAY_BETWEEN_IMAGES)

    logger.info(f"\nBackfill complete: {success_count} succeeded, {error_count} failed")

    # Regenerate embeddings if requested
    if regenerate_embeddings and affected_post_ids:
        logger.info(f"\nRegenerating embeddings for {len(affected_post_ids)} affected posts...")
        embedding_service = get_embedding_service()

        for post_id in affected_post_ids:
            try:
                post = db.get_post(post_id)
                if not post:
                    continue

                # Get all media descriptions for this post
                media_items = db.get_post_media(post_id)
                descriptions = [
                    m["description"]
                    for m in media_items
                    if m.get("description")
                ]

                # Build embedding text
                embed_text = post.get("content", "")
                if post.get("author_handle"):
                    embed_text += f"\n\nAuthor: @{post['author_handle']}"
                if post.get("tags"):
                    embed_text += f"\nTags: {', '.join(post['tags'])}"
                if post.get("topics"):
                    embed_text += f"\nTopics: {', '.join(post['topics'])}"
                if post.get("notes"):
                    embed_text += f"\nNotes: {post['notes']}"
                if descriptions:
                    embed_text += f"\n\nImage content: {' | '.join(descriptions)}"

                # Generate and update embedding
                embedding = embedding_service.generate(embed_text)
                db.update_embedding(post_id, embedding)
                logger.info(f"  Updated embedding for post {post_id}")

            except Exception as e:
                logger.error(f"  Failed to regenerate embedding for {post_id}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Backfill image descriptions for existing media items"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without making them",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of images to process",
    )
    parser.add_argument(
        "--regenerate-embeddings",
        action="store_true",
        help="Regenerate embeddings for posts with new image descriptions",
    )

    args = parser.parse_args()

    # Check for REGENERATE_EMBEDDINGS env var
    regenerate = args.regenerate_embeddings or (
        os.environ.get("REGENERATE_EMBEDDINGS", "").lower() == "true"
    )

    backfill_descriptions(
        dry_run=args.dry_run,
        limit=args.limit,
        regenerate_embeddings=regenerate,
    )


if __name__ == "__main__":
    main()
