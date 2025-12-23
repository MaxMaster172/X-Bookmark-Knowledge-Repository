"""
Embedding Service - Generates vector embeddings for text using BGE model.

Uses BAAI/bge-small-en-v1.5:
- 384 dimensions (compact)
- High quality retrieval performance
- ~130MB model size
"""

from sentence_transformers import SentenceTransformer
from typing import Union
import logging

logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384


class EmbeddingService:
    """Generates embeddings using sentence-transformers."""

    _instance = None
    _model = None

    def __new__(cls):
        """Singleton pattern - only load model once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            self._load_model()

    def _load_model(self):
        """Load the embedding model into memory."""
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        self._model = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded successfully")

    def generate(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        # BGE models benefit from a query prefix for retrieval
        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return [emb.tolist() for emb in embeddings]

    def generate_for_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        BGE models use a specific prefix for queries to improve retrieval.

        Args:
            query: The search query

        Returns:
            Query embedding vector
        """
        # BGE instruction for retrieval queries
        prefixed_query = f"Represent this sentence for searching relevant passages: {query}"
        embedding = self._model.encode(prefixed_query, normalize_embeddings=True)
        return embedding.tolist()

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return EMBEDDING_DIMENSION

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return MODEL_NAME


def get_embedding_service() -> EmbeddingService:
    """Get the singleton embedding service instance."""
    return EmbeddingService()
