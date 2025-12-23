#!/usr/bin/env python3
"""
Migration Script - Generate embeddings for all existing posts.

Usage:
    python scripts/migrate_embeddings.py [--dry-run] [--verbose]

This script:
1. Scans data/posts/ for markdown files
2. Parses each post's content and metadata
3. Generates embeddings using BGE model
4. Stores in ChromaDB vector database
"""

import argparse
import logging
import sys
from pathlib import Path
from time import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.posts.parser import PostParser
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

    # Initialize components
    parser = PostParser()
    posts_count = parser.count_posts()

    logger.info(f"Posts directory: {parser.posts_dir}")
    logger.info(f"Found {posts_count} markdown files")

    if posts_count == 0:
        logger.warning("No posts found to migrate.")
        logger.info("Add markdown files to data/posts/ and run again.")
        return

    if dry_run:
        logger.info("[DRY RUN] Would process the following posts:")
        for post in parser.iter_posts():
            logger.info(f"  - {post.id}: {post.content[:50]}...")
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

    for post in parser.iter_posts():
        try:
            # Generate embedding text (content + metadata)
            embed_text = post.to_embedding_text()

            # Generate embedding
            embedding = embedding_service.generate(embed_text)

            # Store in vector store
            vector_store.add_post(
                post_id=post.id,
                content=post.content,
                metadata=post.to_metadata(),
                embedding=embedding,
            )

            processed += 1

            if verbose:
                logger.debug(f"Processed: {post.id}")
            elif processed % 10 == 0:
                logger.info(f"Progress: {processed}/{posts_count}")

        except Exception as e:
            logger.error(f"Failed to process {post.id}: {e}")
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
