#!/usr/bin/env python3
"""
Semantic Search CLI - Query your bookmark archive.

Usage:
    python scripts/search.py "your search query"
    python scripts/search.py "your search query" --limit 5
    python scripts/search.py --stats
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.embeddings.vector_store import get_vector_store


def search(query: str, limit: int = 10):
    """Perform semantic search and display results."""
    vector_store = get_vector_store()

    print(f"\nSearching for: '{query}'")
    print("-" * 60)

    results = vector_store.search(query, n_results=limit)

    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, 1):
        similarity = result["similarity"]
        content = result["content"]
        metadata = result["metadata"]

        # Truncate content for display
        preview = content[:200] + "..." if len(content) > 200 else content

        print(f"\n{i}. [{similarity:.1%} match]")
        print(f"   ID: {result['id']}")

        if metadata.get("author"):
            print(f"   Author: {metadata['author']}")

        if metadata.get("tags"):
            print(f"   Tags: {metadata['tags']}")

        print(f"   Content: {preview}")
        print()


def show_stats():
    """Display vector store statistics."""
    vector_store = get_vector_store()
    stats = vector_store.get_stats()

    print("\nVector Store Statistics")
    print("-" * 60)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Semantic search for bookmark archive",
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Search query",
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show vector store statistics",
    )

    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.query:
        search(args.query, limit=args.limit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
