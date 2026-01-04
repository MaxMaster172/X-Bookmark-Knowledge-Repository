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


    # ===========================
    # ENTITY OPERATIONS
    # ===========================

    def get_all_entities_with_aliases(self) -> list[dict]:
        """
        Get all entities with their aliases and categories for matching.

        Returns list of dicts with: id, name, aliases, category_id, category_name
        """
        result = (
            self._client.table("entities")
            .select("id, name, aliases, category_id, entity_categories(name)")
            .execute()
        )

        entities = []
        for e in result.data or []:
            entities.append({
                "id": e["id"],
                "name": e["name"],
                "aliases": e.get("aliases") or [],
                "category_id": e.get("category_id"),
                "category_name": e.get("entity_categories", {}).get("name") if e.get("entity_categories") else None,
            })
        return entities

    def get_all_entity_categories(self) -> list[dict]:
        """Get all entity categories."""
        result = (
            self._client.table("entity_categories")
            .select("id, name, description")
            .execute()
        )
        return result.data or []

    def create_entity_category(self, name: str, description: str = None) -> str:
        """
        Create a new entity category.

        Returns the category ID.
        """
        data = {"name": name}
        if description:
            data["description"] = description

        result = self._client.table("entity_categories").insert(data).execute()
        logger.info(f"Created entity category: {name}")
        return result.data[0]["id"] if result.data else None

    def get_or_create_entity_category(self, name: str, description: str = None) -> str:
        """
        Get existing category by name or create if doesn't exist.

        Returns the category ID.
        """
        # Try to find existing
        result = (
            self._client.table("entity_categories")
            .select("id")
            .eq("name", name)
            .execute()
        )

        if result.data:
            return result.data[0]["id"]

        # Create new
        return self.create_entity_category(name, description)

    def create_entity(
        self,
        name: str,
        category_name: str = None,
        description: str = None,
        aliases: list[str] = None,
        embedding: list[float] = None,
    ) -> str:
        """
        Create a new entity.

        Returns the entity ID.
        """
        data = {"name": name}

        if category_name:
            category_id = self.get_or_create_entity_category(category_name)
            data["category_id"] = category_id

        if description:
            data["description"] = description
        if aliases:
            data["aliases"] = aliases
        if embedding:
            data["embedding"] = embedding

        result = self._client.table("entities").insert(data).execute()
        logger.info(f"Created entity: {name}")
        return result.data[0]["id"] if result.data else None

    def link_post_entity(
        self,
        post_id: str,
        entity_id: str,
        confidence: float = 1.0,
        manually_verified: bool = False,
    ) -> None:
        """Link a post to an entity."""
        data = {
            "post_id": post_id,
            "entity_id": entity_id,
            "confidence": confidence,
            "manually_verified": manually_verified,
        }

        # Use upsert to handle duplicates gracefully
        self._client.table("post_entities").upsert(data).execute()
        logger.debug(f"Linked post {post_id[:8]}... to entity {entity_id[:8]}...")

    # ===========================
    # THESIS OPERATIONS
    # ===========================

    def get_all_theses(self) -> list[dict]:
        """Get all theses for matching."""
        result = (
            self._client.table("theses")
            .select("id, name, category, description")
            .execute()
        )
        return result.data or []

    def create_thesis(
        self,
        name: str,
        category: str = "general",
        description: str = None,
        embedding: list[float] = None,
    ) -> str:
        """
        Create a new thesis.

        Returns the thesis ID.
        """
        data = {
            "name": name,
            "category": category,
        }

        if description:
            data["description"] = description
        if embedding:
            data["embedding"] = embedding

        result = self._client.table("theses").insert(data).execute()
        logger.info(f"Created thesis: {name}")
        return result.data[0]["id"] if result.data else None

    def link_post_thesis(
        self,
        post_id: str,
        thesis_id: str,
        contribution: str = None,
        confidence: float = 1.0,
        manually_verified: bool = False,
    ) -> None:
        """Link a post to a thesis with a contribution summary."""
        data = {
            "post_id": post_id,
            "thesis_id": thesis_id,
            "confidence": confidence,
            "manually_verified": manually_verified,
        }

        if contribution:
            data["contribution"] = contribution

        # Use upsert to handle duplicates gracefully
        self._client.table("post_theses").upsert(data).execute()
        logger.debug(f"Linked post {post_id[:8]}... to thesis {thesis_id[:8]}...")

    def link_entity_thesis(
        self,
        entity_id: str,
        thesis_id: str,
        role: str = "subject",
    ) -> None:
        """Link an entity to a thesis with a role."""
        data = {
            "entity_id": entity_id,
            "thesis_id": thesis_id,
            "role": role,
        }

        self._client.table("entity_theses").upsert(data).execute()
        logger.debug(f"Linked entity {entity_id[:8]}... to thesis {thesis_id[:8]}...")

    def create_thesis_relationship(
        self,
        thesis_a_id: str,
        thesis_b_id: str,
        relationship_type: str,
        description: str = None,
    ) -> None:
        """
        Create a relationship between two theses.

        Note: thesis_a_id must be < thesis_b_id (per DB constraint).
        """
        # Ensure proper ordering
        if thesis_a_id > thesis_b_id:
            thesis_a_id, thesis_b_id = thesis_b_id, thesis_a_id

        data = {
            "thesis_a_id": thesis_a_id,
            "thesis_b_id": thesis_b_id,
            "relationship_type": relationship_type,
        }

        if description:
            data["description"] = description

        self._client.table("thesis_relationships").upsert(data).execute()
        logger.debug(f"Created thesis relationship: {relationship_type}")

    # ===========================
    # API USAGE TRACKING
    # ===========================

    def get_or_create_usage_record(self, date_str: str = None) -> dict:
        """
        Get or create API usage record for a date.

        Args:
            date_str: Date in YYYY-MM-DD format (defaults to today)

        Returns dict with: date, analysis_count, synthesis_count
        """
        from datetime import date

        if date_str is None:
            date_str = date.today().isoformat()

        # Try to get existing
        result = (
            self._client.table("api_usage")
            .select("*")
            .eq("date", date_str)
            .execute()
        )

        if result.data:
            return result.data[0]

        # Create new record
        data = {
            "date": date_str,
            "analysis_count": 0,
            "synthesis_count": 0,
        }
        result = self._client.table("api_usage").insert(data).execute()
        return result.data[0] if result.data else data

    def increment_analysis_count(self) -> int:
        """
        Increment today's analysis count.

        Returns the new count.
        """
        from datetime import date

        date_str = date.today().isoformat()
        record = self.get_or_create_usage_record(date_str)
        new_count = record["analysis_count"] + 1

        self._client.table("api_usage").update(
            {"analysis_count": new_count}
        ).eq("date", date_str).execute()

        return new_count

    def increment_synthesis_count(self) -> int:
        """
        Increment today's synthesis count.

        Returns the new count.
        """
        from datetime import date

        date_str = date.today().isoformat()
        record = self.get_or_create_usage_record(date_str)
        new_count = record["synthesis_count"] + 1

        self._client.table("api_usage").update(
            {"synthesis_count": new_count}
        ).eq("date", date_str).execute()

        return new_count

    def check_analysis_limit(self, daily_limit: int = 20) -> bool:
        """
        Check if we're under the daily analysis limit.

        Returns True if we can make another analysis call.
        """
        record = self.get_or_create_usage_record()
        return record["analysis_count"] < daily_limit


def get_supabase_client() -> SupabaseClient:
    """Get the singleton Supabase client instance."""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client
