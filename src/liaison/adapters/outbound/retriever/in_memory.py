"""Adapter retriever hors-ligne : scoring par recouvrement de tokens (BM25 simplifie)."""

from __future__ import annotations

import re

from liaison.ports.retriever import Document

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    """Decoupe un texte en ensemble de tokens normalises."""
    return set(_TOKEN.findall(text.lower()))


class InMemoryRetriever:
    """Retriever hors-ligne par recouvrement de tokens (BM25 simplifie)."""

    def __init__(self, documents: list[Document]) -> None:
        self._documents = documents

    def _score(self, query_tokens: set[str], document: Document) -> int:
        doc_tokens = _tokenize(f"{document.title} {document.content}")
        return len(query_tokens & doc_tokens)

    async def search(self, query: str, top_k: int) -> list[Document]:
        query_tokens = _tokenize(query)
        ranked = sorted(
            self._documents,
            key=lambda d: self._score(query_tokens, d),
            reverse=True,
        )
        return [d for d in ranked if self._score(query_tokens, d) > 0][:top_k]
