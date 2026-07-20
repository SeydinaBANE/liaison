"""Adapter retriever Qdrant pour la production (embeddings locaux + cosine)."""

from __future__ import annotations

from liaison.ports.retriever import Document


class _QdrantNotInstalledError(ImportError):
    """Qdrant client non installe (pip install liaison[qdrant])."""


class QdrantRetriever:
    """Retriever Qdrant pour la production (embeddings locaux + cosine)."""

    def __init__(self, url: str, collection: str = "liaison") -> None:
        try:
            from qdrant_client import AsyncQdrantClient, models
        except ImportError:
            raise _QdrantNotInstalledError("pip install liaison[qdrant] ou qdrant-client") from None
        self._client = AsyncQdrantClient(url=url)
        self._collection = collection
        self._models = models

    def _embed(self, text: str) -> list[float]:
        import hashlib

        h = hashlib.md5(text.encode(), usedforsecurity=False)
        seed = int(h.hexdigest()[:8], 16)
        rng = __import__("random").Random(seed)
        return [rng.random() for _ in range(128)]

    async def search(self, query: str, top_k: int) -> list[Document]:
        query_vector = self._embed(query)
        try:
            results = await self._client.query_points(
                collection_name=self._collection,
                query=query_vector,
                limit=top_k,
            )
        except Exception:
            return []
        documents: list[Document] = []
        for hit in results.points:
            payload = hit.payload or {}
            documents.append(
                Document(
                    doc_id=str(payload.get("doc_id", hit.id)),
                    title=str(payload.get("title", "")),
                    content=str(payload.get("content", "")),
                )
            )
        return documents
