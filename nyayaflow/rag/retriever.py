"""Legal document retriever using ChromaDB."""
import os
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

from rag.embeddings import EmbeddingService
from backend.config import get_settings

settings = get_settings()


class LegalRetriever:
    """Retrieve relevant Indian legal provisions using semantic search."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve top-k relevant legal provisions."""
        if not query.strip() or self.collection.count() == 0:
            return []
        query_embedding = self.embedding_service.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        statutes = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0
                raw_score = 1.0 - distance
                relevance_score = max(0.0, min(1.0, raw_score))
                statutes.append({
                    "act_name": meta.get("act_name", "Unknown Act"),
                    "section": meta.get("section", ""),
                    "title": meta.get("title", ""),
                    "content": doc,
                    "relevance_score": relevance_score,
                    "source_url": meta.get("source_url", ""),
                })

        return statutes

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add legal documents to the vector store."""
        texts = [d["content"] for d in documents]
        embeddings = self.embedding_service.embed(texts)

        ids = [d.get("id", f"doc_{i}") for i, d in enumerate(documents)]
        metadatas = [{
            "act_name": d.get("act_name", ""),
            "section": d.get("section", ""),
            "title": d.get("title", ""),
            "source_url": d.get("source_url", ""),
        } for d in documents]

        # Ingestion may be run repeatedly; replace unchanged chunk IDs rather than
        # failing with a duplicate-ID error.
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
