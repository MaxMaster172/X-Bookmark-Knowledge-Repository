"""
Integration tests for Supabase functionality.

These tests verify the Supabase client and embedding service work correctly.
Requires environment variables:
- SUPABASE_URL
- SUPABASE_SERVICE_KEY

Run with: pytest tests/test_supabase_integration.py -v
"""

import os
import sys
import pytest
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env if present
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


# Skip all tests if credentials not available
pytestmark = pytest.mark.skipif(
    not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_SERVICE_KEY"),
    reason="Supabase credentials not configured"
)


class TestSupabaseClient:
    """Tests for the Supabase client."""

    @pytest.fixture
    def client(self):
        """Get a Supabase client instance."""
        from src.supabase.client import get_supabase_client
        return get_supabase_client()

    def test_client_connects(self, client):
        """Test that the client can connect to Supabase."""
        # get_stats() will fail if connection is bad
        stats = client.get_stats()
        assert isinstance(stats, dict)
        assert "total_posts" in stats

    def test_get_stats(self, client):
        """Test getting database statistics."""
        stats = client.get_stats()
        assert "total_posts" in stats
        assert "unique_authors" in stats
        assert "unique_tags" in stats
        assert stats["total_posts"] >= 0

    def test_get_recent_posts(self, client):
        """Test getting recent posts."""
        posts = client.get_recent_posts(limit=5)
        assert isinstance(posts, list)
        # Should return at most 5 posts
        assert len(posts) <= 5

    def test_post_exists_false(self, client):
        """Test checking for non-existent post."""
        # Use a random UUID that definitely doesn't exist
        fake_id = f"test_{uuid4().hex}"
        assert client.post_exists(fake_id) is False

    def test_insert_and_check_post(self, client):
        """Test inserting a post and checking it exists."""
        # Create a unique test post ID
        test_id = f"test_{uuid4().hex[:8]}"

        try:
            # Insert the post
            result = client.insert_post(
                post_id=test_id,
                url=f"https://x.com/test/status/{test_id}",
                content="This is a test post for integration testing.",
                author_handle="test_user",
                author_name="Test User",
                archived_at=datetime.now(),
                archived_via="test",
                tags=["test", "integration"],
                topics=["testing"],
            )

            # Verify it was inserted
            assert result is not None

            # Verify it exists
            assert client.post_exists(test_id) is True

            # Verify we can retrieve it
            post = client.get_post(test_id)
            assert post is not None
            assert post["id"] == test_id
            assert post["author_handle"] == "test_user"
            assert "test" in post["tags"]

        finally:
            # Clean up: delete the test post
            try:
                client._client.table("posts").delete().eq("id", test_id).execute()
            except Exception:
                pass  # Ignore cleanup errors


class TestEmbeddingService:
    """Tests for the embedding service."""

    @pytest.fixture
    def service(self):
        """Get an embedding service instance."""
        from src.embeddings.service import get_embedding_service
        return get_embedding_service()

    def test_service_loads(self, service):
        """Test that the embedding service loads successfully."""
        assert service is not None
        assert service.dimension == 384

    def test_generate_embedding(self, service):
        """Test generating an embedding for text."""
        text = "This is a test sentence for embedding generation."
        embedding = service.generate(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    def test_generate_query_embedding(self, service):
        """Test generating a query embedding."""
        query = "test query for search"
        embedding = service.generate_for_query(query)

        assert isinstance(embedding, list)
        assert len(embedding) == 384

    def test_embeddings_are_normalized(self, service):
        """Test that embeddings are normalized (unit vectors)."""
        import math

        text = "Test text for normalization check"
        embedding = service.generate(text)

        # Calculate L2 norm
        norm = math.sqrt(sum(x * x for x in embedding))

        # Should be approximately 1.0 (normalized)
        assert abs(norm - 1.0) < 0.01


class TestVectorSearch:
    """Tests for vector search functionality."""

    @pytest.fixture
    def client(self):
        """Get a Supabase client instance."""
        from src.supabase.client import get_supabase_client
        return get_supabase_client()

    @pytest.fixture
    def embedding_service(self):
        """Get an embedding service instance."""
        from src.embeddings.service import get_embedding_service
        return get_embedding_service()

    def test_search_posts_returns_results(self, client, embedding_service):
        """Test that search_posts returns results for a valid query."""
        # Generate a query embedding
        query = "machine learning artificial intelligence"
        query_embedding = embedding_service.generate_for_query(query)

        # Search with low threshold to get results
        results = client.search_posts(
            query_embedding=query_embedding,
            match_threshold=0.0,  # Very low to ensure results
            match_count=5
        )

        # Results should be a list (may be empty if no posts in DB)
        assert isinstance(results, list)

    def test_search_posts_has_similarity_scores(self, client, embedding_service):
        """Test that search results include similarity scores."""
        query = "programming code development"
        query_embedding = embedding_service.generate_for_query(query)

        results = client.search_posts(
            query_embedding=query_embedding,
            match_threshold=0.0,
            match_count=5
        )

        # If we have results, they should have similarity scores
        for result in results:
            assert "similarity" in result
            assert isinstance(result["similarity"], (int, float))
            assert 0 <= result["similarity"] <= 1


class TestCredentialHandling:
    """Tests for credential error handling."""

    def test_missing_credentials_raises_error(self):
        """Test that missing credentials raise an appropriate error."""
        from src.supabase.client import SupabaseClient

        # Temporarily clear env vars
        original_url = os.environ.pop("SUPABASE_URL", None)
        original_key = os.environ.pop("SUPABASE_SERVICE_KEY", None)

        try:
            with pytest.raises(ValueError) as exc_info:
                SupabaseClient(url=None, key=None)

            assert "credentials required" in str(exc_info.value).lower()

        finally:
            # Restore env vars
            if original_url:
                os.environ["SUPABASE_URL"] = original_url
            if original_key:
                os.environ["SUPABASE_SERVICE_KEY"] = original_key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
