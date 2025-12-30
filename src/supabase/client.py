"""
Supabase Client - Database operations for the X-Bookmark Knowledge Repository.

Provides:
- Post CRUD operations
- Vector search using pgvector
- Media metadata storage
- Thesis system operations (Phase 7)
"""

import os
import logging
from datetime import datetime
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")  # Use service key for server-side

# Singleton instance
_client: Optional["SupabaseClient"] = None


class SupabaseClient:
    """Supabase database client for post operations."""

    def __init__(self, url: str = None, key: str = None):
        """
        Initialize the Supabase client.

        Args:
            url: Supabase project URL (or set SUPABASE_URL env var)
            key: Supabase service key (or set SUPABASE_SERVICE_KEY env var)
        """
        self.url = url or SUPABASE_URL
        self.key = key or SUPABASE_KEY

        if not self.url or not self.key:
            raise ValueError(
                "Supabase credentials required. Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
            )

        self._client: Client = create_client(self.url, self.key)
        logger.info(f"Supabase client initialized for: {self.url}")

    # ===========================
    # POST OPERATIONS
    # ===========================

    def insert_post(
        self,
        post_id: str,
        url: str,
        content: str,
        author_handle: str = None,
        author_name: str = None,
        posted_at: datetime = None,
        archived_at: datetime = None,
        archived_via: str = "telegram",
        tags: list[str] = None,
        topics: list[str] = None,
        notes: str = None,
        importance: str = None,
        thread_position: int = None,
        is_thread: bool = False,
        quoted_post_id: str = None,
        quoted_text: str = None,
        quoted_author: str = None,
        quoted_url: str = None,
        embedding: list[float] = None,
    ) -> dict:
        """
        Insert a new post into the database.

        Returns the inserted row.
        """
        data = {
            "id": post_id,
            "url": url,
            "content": content,
            "author_handle": author_handle,
            "author_name": author_name,
            "archived_via": archived_via,
            "tags": tags or [],
            "topics": topics or [],
            "notes": notes,
            "importance": importance,
            "thread_position": thread_position,
            "is_thread": is_thread,
            "quoted_post_id": quoted_post_id,
            "quoted_text": quoted_text,
            "quoted_author": quoted_author,
            "quoted_url": quoted_url,
        }

        # Handle datetime fields
        if posted_at:
            data["posted_at"] = (
                posted_at.isoformat() if isinstance(posted_at, datetime) else posted_at
            )
        if archived_at:
            data["archived_at"] = (
                archived_at.isoformat()
                if isinstance(archived_at, datetime)
                else archived_at
            )

        # Handle embedding (pgvector format)
        if embedding:
            data["embedding"] = embedding

        result = self._client.table("posts").insert(data).execute()
        logger.info(f"Inserted post: {post_id}")
        return result.data[0] if result.data else None

    def upsert_post(self, post_data: dict) -> dict:
        """
        Insert or update a post.

        Args:
            post_data: Dict with post fields (must include 'id')

        Returns the upserted row.
        """
        result = self._client.table("posts").upsert(post_data).execute()
        return result.data[0] if result.data else None

    def get_post(self, post_id: str) -> Optional[dict]:
        """Get a single post by ID."""
        result = self._client.table("posts").select("*").eq("id", post_id).execute()
        return result.data[0] if result.data else None

    def get_recent_posts(self, limit: int = 10) -> list[dict]:
        """Get the most recently archived posts."""
        result = (
            self._client.table("posts")
            .select("*")
            .order("archived_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    def get_all_posts(self) -> list[dict]:
        """Get all posts (for migration/export)."""
        result = self._client.table("posts").select("*").execute()
        return result.data or []

    def post_exists(self, post_id: str) -> bool:
        """Check if a post already exists."""
        result = (
            self._client.table("posts").select("id").eq("id", post_id).execute()
        )
        return len(result.data) > 0

    def update_embedding(self, post_id: str, embedding: list[float]) -> bool:
        """Update the embedding for a post."""
        result = (
            self._client.table("posts")
            .update({"embedding": embedding})
            .eq("id", post_id)
            .execute()
        )
        return len(result.data) > 0

    def count_posts(self) -> int:
        """Count total posts in the database."""
        result = self._client.table("posts").select("id", count="exact").execute()
        return result.count or 0

    # ===========================
    # MEDIA OPERATIONS
    # ===========================

    def insert_media(
        self,
        post_id: str,
        media_type: str,
        url: str,
        category: str = None,
        description: str = None,
        extraction_model: str = None,
    ) -> dict:
        """Insert a media item for a post."""
        data = {
            "post_id": post_id,
            "type": media_type,
            "url": url,
            "category": category,
            "description": description,
            "extraction_model": extraction_model,
        }
        if description:
            data["extracted_at"] = datetime.now().isoformat()

        result = self._client.table("post_media").insert(data).execute()
        return result.data[0] if result.data else None

    def get_post_media(self, post_id: str) -> list[dict]:
        """Get all media items for a post."""
        result = (
            self._client.table("post_media")
            .select("*")
            .eq("post_id", post_id)
            .execute()
        )
        return result.data or []

    def update_media(
        self,
        media_id: int,
        category: str,
        description: str,
        extraction_model: str,
    ) -> bool:
        """
        Update a media item with extracted description.

        Args:
            media_id: The media item ID
            category: Image category (text_heavy, chart, general)
            description: Extracted description
            extraction_model: Model used for extraction

        Returns:
            True if update succeeded
        """
        data = {
            "category": category,
            "description": description,
            "extraction_model": extraction_model,
            "extracted_at": datetime.now().isoformat(),
        }
        result = (
            self._client.table("post_media")
            .update(data)
            .eq("id", media_id)
            .execute()
        )
        return len(result.data) > 0

    def get_media_without_descriptions(self, limit: int = 100) -> list[dict]:
        """
        Get media items that don't have descriptions yet.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of media items with id, post_id, type, and url
        """
        result = (
            self._client.table("post_media")
            .select("id, post_id, type, url")
            .is_("description", "null")
            .limit(limit)
            .execute()
        )
        return result.data or []

    # ===========================
    # VECTOR SEARCH
    # ===========================

    def search_posts(
        self,
        query_embedding: list[float],
        match_threshold: float = 0.7,
        match_count: int = 10,
    ) -> list[dict]:
        """
        Search posts by vector similarity using pgvector.

        Args:
            query_embedding: The 384-dim embedding vector for the query
            match_threshold: Minimum similarity score (0-1)
            match_count: Maximum number of results

        Returns:
            List of posts with similarity scores
        """
        result = self._client.rpc(
            "match_posts",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
            },
        ).execute()
        return result.data or []

    def search_posts_raw(
        self,
        query_embedding: list[float],
        limit: int = 10,
    ) -> list[dict]:
        """
        Alternative search using direct SQL (if RPC not available).

        Uses Supabase's .filter() for vector operations.
        """
        # This is a fallback - the RPC function is more efficient
        # For now, return empty and use match_posts RPC
        logger.warning("search_posts_raw not implemented - use search_posts with RPC")
        return []

    # ===========================
    # STATS
    # ===========================

    def get_stats(self) -> dict:
        """Get database statistics."""
        posts_count = self.count_posts()

        # Get unique authors
        authors_result = (
            self._client.table("posts")
            .select("author_handle")
            .execute()
        )
        unique_authors = len(
            set(p["author_handle"] for p in authors_result.data if p.get("author_handle"))
        )

        # Get tag counts
        tags_result = self._client.table("posts").select("tags").execute()
        all_tags = []
        for p in tags_result.data or []:
            all_tags.extend(p.get("tags") or [])
        unique_tags = len(set(all_tags))

        return {
            "total_posts": posts_count,
            "unique_authors": unique_authors,
            "unique_tags": unique_tags,
        }


def get_supabase_client() -> SupabaseClient:
    """Get the singleton Supabase client instance."""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client
