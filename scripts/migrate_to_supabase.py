#!/usr/bin/env python3
"""
Migrate posts from file-based storage to Supabase.

Reads all posts from archive/posts/**/*.md and inserts them into Supabase.
Also copies embeddings from ChromaDB to pgvector.

USAGE:
    python scripts/migrate_to_supabase.py --dry-run    # Preview without writing
    python scripts/migrate_to_supabase.py              # Execute migration
    python scripts/migrate_to_supabase.py --force      # Overwrite existing posts

PREREQUISITES:
    1. Create Supabase project at supabase.com
    2. Run deploy/sql/001_initial_schema.sql in SQL Editor
    3. Set environment variables:
       - SUPABASE_URL=https://your-project.supabase.co
       - SUPABASE_SERVICE_KEY=your-service-role-key
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.utils import ARCHIVE_DIR, parse_post_file

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_all_post_files() -> list[Path]:
    """Find all post markdown files."""
    return sorted(ARCHIVE_DIR.glob("**/*.md"))


def parse_datetime(value: str) -> Optional[datetime]:
    """Parse various datetime formats from post files."""
    if not value:
        return None

    # Try ISO format first
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        pass

    # Try Twitter format: "Mon Dec 22 16:05:20 +0000 2025"
    try:
        return datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")
    except (ValueError, TypeError):
        pass

    # Return None if unparseable
    logger.warning(f"Could not parse datetime: {value}")
    return None


def load_chromadb_embeddings() -> dict:
    """Load embeddings from ChromaDB for migration."""
    embeddings = {}
    try:
        from src.embeddings import VectorStore

        store = VectorStore()
        logger.info(f"ChromaDB has {store.count()} posts")

        # Get all embeddings
        # ChromaDB doesn't have a direct "get all embeddings" method,
        # so we'll generate them fresh during migration if needed
        logger.info("Will generate fresh embeddings during migration")

    except Exception as e:
        logger.warning(f"Could not load ChromaDB: {e}")

    return embeddings


def migrate_posts(dry_run: bool = True, force: bool = False):
    """
    Migrate all posts from files to Supabase.

    Args:
        dry_run: If True, only preview changes without writing
        force: If True, overwrite existing posts in Supabase
    """
    if dry_run:
        logger.info("=== DRY RUN MODE - No changes will be made ===")
    else:
        # Import Supabase client only when actually needed
        from src.supabase import get_supabase_client

        client = get_supabase_client()

    # Import embedding service for generating embeddings
    try:
        from src.embeddings import EmbeddingService

        embedding_service = EmbeddingService()
        logger.info(f"Using embedding model: {embedding_service.model_name}")
    except Exception as e:
        logger.warning(f"Could not load embedding service: {e}")
        embedding_service = None

    # Find all post files
    post_files = get_all_post_files()
    logger.info(f"Found {len(post_files)} post files to migrate")

    if not post_files:
        logger.info("No posts to migrate")
        return

    # Track statistics
    stats = {
        "total": len(post_files),
        "migrated": 0,
        "skipped": 0,
        "errors": 0,
        "with_embeddings": 0,
    }

    for i, file_path in enumerate(post_files, 1):
        post_id = file_path.stem
        logger.info(f"[{i}/{len(post_files)}] Processing: {post_id}")

        try:
            # Parse the post file
            post_data = parse_post_file(file_path)
            metadata = post_data.get("metadata", {})
            body = post_data.get("body", "")

            # Check if post already exists (if not dry run)
            if not dry_run and not force:
                if client.post_exists(post_id):
                    logger.info(f"  Skipping (already exists): {post_id}")
                    stats["skipped"] += 1
                    continue

            # Extract author info
            author = metadata.get("author", {})
            author_handle = (
                author.get("handle") if isinstance(author, dict) else str(author)
            )
            author_name = author.get("name") if isinstance(author, dict) else None

            # Parse dates
            posted_at = parse_datetime(metadata.get("posted_at"))
            archived_at = parse_datetime(metadata.get("archived_at"))

            # Get content - prefer body, fallback to metadata content
            content = body.strip() if body else metadata.get("content", "")

            # Generate embedding
            embedding = None
            if embedding_service and content:
                try:
                    embedding = embedding_service.generate(content)
                    stats["with_embeddings"] += 1
                except Exception as e:
                    logger.warning(f"  Could not generate embedding: {e}")

            # Build post record
            post_record = {
                "id": post_id,
                "url": metadata.get("url", ""),
                "content": content,
                "author_handle": author_handle,
                "author_name": author_name,
                "posted_at": posted_at.isoformat() if posted_at else None,
                "archived_at": archived_at.isoformat() if archived_at else None,
                "archived_via": metadata.get("archived_via", "telegram"),
                "tags": metadata.get("tags", []),
                "topics": metadata.get("topics", []),
                "notes": metadata.get("notes"),
                "importance": metadata.get("importance"),
                "is_thread": metadata.get("thread", {}).get("is_thread", False),
                "thread_position": metadata.get("thread", {}).get("position"),
            }

            # Handle quoted posts
            quotes = metadata.get("quotes", {})
            if quotes:
                post_record["quoted_post_id"] = quotes.get("quoted_post_id")
                post_record["quoted_url"] = quotes.get("quoted_url")

            # Add embedding if available
            if embedding:
                post_record["embedding"] = embedding

            if dry_run:
                logger.info(f"  Would insert: {post_id}")
                logger.info(f"    Author: @{author_handle}")
                logger.info(f"    Content: {content[:100]}...")
                logger.info(f"    Tags: {post_record['tags']}")
                logger.info(f"    Has embedding: {embedding is not None}")
            else:
                # Insert into Supabase (upsert handles both insert and update)
                client.upsert_post(post_record)
                logger.info(f"  Migrated: {post_id}")

            stats["migrated"] += 1

            # Handle media items
            media = metadata.get("media", [])
            for media_item in media:
                if dry_run:
                    logger.info(f"    Would insert media: {media_item.get('type')}")
                else:
                    client.insert_media(
                        post_id=post_id,
                        media_type=media_item.get("type", "image"),
                        url=media_item.get("url", ""),
                        description=media_item.get("description"),
                    )

        except Exception as e:
            logger.error(f"  Error migrating {post_id}: {e}")
            stats["errors"] += 1

    # Print summary
    logger.info("")
    logger.info("=" * 50)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total posts found:    {stats['total']}")
    logger.info(f"Successfully migrated: {stats['migrated']}")
    logger.info(f"Skipped (existing):   {stats['skipped']}")
    logger.info(f"Errors:               {stats['errors']}")
    logger.info(f"With embeddings:      {stats['with_embeddings']}")

    if dry_run:
        logger.info("")
        logger.info("This was a DRY RUN. No changes were made.")
        logger.info("Run without --dry-run to execute the migration.")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate posts from files to Supabase"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without making changes",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing posts in Supabase"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    migrate_posts(dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
