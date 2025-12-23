#!/usr/bin/env python3
"""
Migration Script - Generate embeddings for all existing posts.

Usage:
    python scripts/migrate_embeddings.py [--dry-run] [--verbose]

This script:
1. Scans archive/posts/ for markdown files
2. Parses each post's content and metadata using tools/utils.py
3. Generates embeddings using BGE model
4. Stores in ChromaDB vector database
"""

import argparse
import logging
import sys
from pathlib import Path
from time import time

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from tools.utils import parse_post_file, ARCHIVE_DIR, BASE_DIR
from src.embeddings.service import get_embedding_service
from src.embeddings.vector_store import get_vector_store


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def iter_posts():
    """Iterate over all markdown posts in the archive."""
    if not ARCHIVE_DIR.exists():
        return

    for md_file in ARCHIVE_DIR.rglob("*.md"):
        post = parse_post_file(md_file)
        if post:
            # Extract post ID from filename or metadata
            metadata = post.get("metadata", {})
            post_id = metadata.get("id", md_file.stem)
            yield {
                "id": str(post_id),
                "path": md_file,
                "metadata": metadata,
                "body": post.get("body", ""),
            }


def count_posts() -> int:
    """Count markdown files in archive."""
    if not ARCHIVE_DIR.exists():
        return 0
    return len(list(ARCHIVE_DIR.rglob("*.md")))


def create_embedding_text(post: dict) -> str:
    """Create text representation for embedding."""
    parts = [post["body"]]

    metadata = post["metadata"]

    # Add author info
    author = metadata.get("author", {})
    if isinstance(author, dict):
        author_handle = author.get("handle")
        author_name = author.get("name")
        if author_handle:
            author_str = f"@{author_handle}"
            if author_name:
                author_str += f" ({author_name})"
            parts.append(f"Author: {author_str}")
    elif author:
        parts.append(f"Author: {author}")

    # Add tags
    if metadata.get("tags"):
        parts.append(f"Tags: {', '.join(metadata['tags'])}")

    # Add topics
    if metadata.get("topics"):
        parts.append(f"Topics: {', '.join(metadata['topics'])}")

    # Add notes (if not "skip")
    notes = metadata.get("notes")
    if notes and str(notes).lower() != "skip":
        parts.append(f"Notes: {notes}")

    return "\n\n".join(parts)


def create_metadata(post: dict) -> dict:
    """Create metadata dict for vector store."""
    metadata = post["metadata"]
    author = metadata.get("author", {})

    if isinstance(author, dict):
        author_handle = author.get("handle")
        author_name = author.get("name")
    else:
        author_handle = author
        author_name = None

    return {
        "author_handle": author_handle,
        "author_name": author_name,
        "url": metadata.get("url"),
        "tags": metadata.get("tags", []),
        "topics": metadata.get("topics", []),
        "importance": metadata.get("importance"),
        "notes": metadata.get("notes"),
        "archived_at": metadata.get("archived_at"),
        "posted_at": str(metadata.get("posted_at")) if metadata.get("posted_at") else None,
    }


def migrate(dry_run: bool = False, verbose: bool = False):
    """
    Run the embedding migration.

    Args:
        dry_run: If True, only report what would be done
        verbose: Enable debug logging
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Embedding Migration Script")
    logger.info("=" * 60)

    # Count posts
    posts_count = count_posts()

    logger.info(f"Posts directory: {ARCHIVE_DIR}")
    logger.info(f"Found {posts_count} markdown files")

    if posts_count == 0:
        logger.warning("No posts found to migrate.")
        logger.info("Add markdown files to archive/posts/ and run again.")
        return

    if dry_run:
        logger.info("[DRY RUN] Would process the following posts:")
        for post in iter_posts():
            preview = post["body"][:50].replace("\n", " ")
            logger.info(f"  - {post['id']}: {preview}...")
        logger.info(f"[DRY RUN] Would generate {posts_count} embeddings")
        return

    # Initialize embedding service (this loads the model)
    logger.info("Loading embedding model (this may take a moment)...")
    start = time()
    embedding_service = get_embedding_service()
    logger.info(f"Model loaded in {time() - start:.1f}s")
    logger.info(f"Using model: {embedding_service.model_name}")
    logger.info(f"Embedding dimension: {embedding_service.dimension}")

    # Initialize vector store
    vector_store = get_vector_store()
    initial_count = vector_store.count()
    logger.info(f"Vector store initialized. Existing entries: {initial_count}")

    # Process posts
    logger.info("-" * 60)
    logger.info("Processing posts...")

    processed = 0
    errors = 0
    start = time()

    for post in iter_posts():
        try:
            # Generate embedding text (content + metadata)
            embed_text = create_embedding_text(post)

            # Generate embedding
            embedding = embedding_service.generate(embed_text)

            # Store in vector store
            vector_store.add_post(
                post_id=post["id"],
                content=post["body"],
                metadata=create_metadata(post),
                embedding=embedding,
            )

            processed += 1

            if verbose:
                logger.debug(f"Processed: {post['id']}")
            elif processed % 10 == 0:
                logger.info(f"Progress: {processed}/{posts_count}")

        except Exception as e:
            logger.error(f"Failed to process {post['id']}: {e}")
            if verbose:
                import traceback
                logger.error(traceback.format_exc())
            errors += 1

    elapsed = time() - start

    # Report results
    logger.info("-" * 60)
    logger.info("Migration Complete!")
    logger.info(f"  Processed: {processed} posts")
    logger.info(f"  Errors: {errors}")
    logger.info(f"  Time: {elapsed:.1f}s ({elapsed/max(processed,1):.2f}s per post)")
    logger.info(f"  Vector store now contains: {vector_store.count()} entries")
    logger.info("=" * 60)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for all existing posts",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()
    migrate(dry_run=args.dry_run, verbose=args.verbose)


if __name__ == "__main__":
    main()
