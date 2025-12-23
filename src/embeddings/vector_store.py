"""
Vector Store - ChromaDB wrapper for storing and searching post embeddings.

Provides:
- Persistent storage of embeddings
- Semantic similarity search
- Metadata filtering
"""

import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import Optional
import logging

from .service import get_embedding_service, EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"
DEFAULT_VECTORS_DIR = DEFAULT_DATA_DIR / "vectors"

# Collection name
COLLECTION_NAME = "posts"


class VectorStore:
    """ChromaDB-backed vector store for post embeddings."""

    def __init__(self, persist_directory: Optional[Path] = None):
        """
        Initialize the vector store.

        Args:
            persist_directory: Where to store the ChromaDB files.
                             Defaults to data/vectors/
        """
        self.persist_directory = persist_directory or DEFAULT_VECTORS_DIR
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing ChromaDB at: {self.persist_directory}")

        self._client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )

        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "dimension": EMBEDDING_DIMENSION},
        )

        self._embedding_service = get_embedding_service()

    def add_post(
        self,
        post_id: str,
        content: str,
        metadata: Optional[dict] = None,
        embedding: Optional[list[float]] = None,
    ) -> None:
        """
        Add a post to the vector store.

        Args:
            post_id: Unique identifier for the post
            content: The text content to embed and store
            metadata: Optional metadata (author, tags, date, etc.)
            embedding: Pre-computed embedding. If None, generates one.
        """
        if embedding is None:
            embedding = self._embedding_service.generate(content)

        # ChromaDB metadata must be flat (str, int, float, bool)
        clean_metadata = self._flatten_metadata(metadata or {})
        clean_metadata["content_preview"] = content[:500] if content else ""

        self._collection.upsert(
            ids=[post_id],
            embeddings=[embedding],
            metadatas=[clean_metadata],
            documents=[content],
        )

        logger.debug(f"Added post to vector store: {post_id}")

    def search(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """
        Search for posts similar to the query.

        Args:
            query: Natural language search query
            n_results: Maximum number of results to return
            where: Optional metadata filter (ChromaDB where clause)

        Returns:
            List of results with id, content, metadata, and similarity score
        """
        query_embedding = self._embedding_service.generate_for_query(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted = []
        for i in range(len(results["ids"][0])):
            # ChromaDB returns cosine distance; convert to similarity
            distance = results["distances"][0][i]
            similarity = 1 - distance  # cosine similarity = 1 - cosine distance

            formatted.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity": round(similarity, 4),
            })

        return formatted

    def get_similar(
        self,
        post_id: str,
        n_results: int = 5,
    ) -> list[dict]:
        """
        Find posts similar to a given post.

        Args:
            post_id: The ID of the post to find similar posts for
            n_results: Maximum number of similar posts to return

        Returns:
            List of similar posts (excludes the original post)
        """
        # Get the embedding for the target post
        result = self._collection.get(
            ids=[post_id],
            include=["embeddings"],
        )

        if not result["ids"]:
            logger.warning(f"Post not found: {post_id}")
            return []

        embedding = result["embeddings"][0]

        # Query for similar posts
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=n_results + 1,  # +1 because it will include itself
            include=["documents", "metadatas", "distances"],
        )

        # Format and filter out the original post
        formatted = []
        for i in range(len(results["ids"][0])):
            if results["ids"][0][i] == post_id:
                continue

            distance = results["distances"][0][i]
            similarity = 1 - distance

            formatted.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity": round(similarity, 4),
            })

        return formatted[:n_results]

    def delete_post(self, post_id: str) -> bool:
        """
        Delete a post from the vector store.

        Args:
            post_id: The ID of the post to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            self._collection.delete(ids=[post_id])
            logger.debug(f"Deleted post from vector store: {post_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete post {post_id}: {e}")
            return False

    def get_post(self, post_id: str) -> Optional[dict]:
        """
        Get a single post by ID.

        Args:
            post_id: The ID of the post

        Returns:
            Post dict with id, content, metadata, or None if not found
        """
        result = self._collection.get(
            ids=[post_id],
            include=["documents", "metadatas"],
        )

        if not result["ids"]:
            return None

        return {
            "id": result["ids"][0],
            "content": result["documents"][0],
            "metadata": result["metadatas"][0],
        }

    def count(self) -> int:
        """Return the total number of posts in the store."""
        return self._collection.count()

    def get_stats(self) -> dict:
        """Get statistics about the vector store."""
        return {
            "total_posts": self.count(),
            "persist_directory": str(self.persist_directory),
            "collection_name": COLLECTION_NAME,
            "embedding_dimension": EMBEDDING_DIMENSION,
        }

    def _flatten_metadata(self, metadata: dict) -> dict:
        """
        Flatten metadata for ChromaDB compatibility.

        ChromaDB only supports str, int, float, bool values.
        Lists are converted to comma-separated strings.
        """
        flat = {}
        for key, value in metadata.items():
            if value is None:
                continue
            elif isinstance(value, list):
                flat[key] = ", ".join(str(v) for v in value)
            elif isinstance(value, (str, int, float, bool)):
                flat[key] = value
            else:
                flat[key] = str(value)
        return flat


def get_vector_store(persist_directory: Optional[Path] = None) -> VectorStore:
    """Get a vector store instance."""
    return VectorStore(persist_directory)
