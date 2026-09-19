"""Embedding service for legal document retrieval."""
from typing import List
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Generate embeddings using sentence-transformers (local, no API calls)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts."""
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        return self.model.encode([text], show_progress_bar=False)[0].tolist()
