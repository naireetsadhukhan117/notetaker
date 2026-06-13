"""
VectorStore
-----------
Thin wrapper around ChromaDB for storing and querying 3,072-dim vectors.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

CONFIDENCE_CUTOFF   = 0.30
COLLECTION_NAME     = "notebooklm_chunks"


class VectorStore:
    """Manages local ChromaDB collections with defensive query boundaries."""

    def __init__(self, persist_directory: str = "./chroma_db"):
        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("VectorStore initialised at '%s'.", persist_directory)

    def _sanitize_metadata(self, metadata: Optional[Dict]) -> Dict:
        if not metadata:
            return {}
        return {k: v for k, v in metadata.items() if v is not None}

    def upsert(
        self,
        vector_id: str,
        vector: List[float],
        text_content: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        sanitized_meta = self._sanitize_metadata(metadata)
        self._collection.upsert(
            ids=[vector_id],
            embeddings=[vector],
            documents=[text_content],
            metadatas=[sanitized_meta],
        )

    def upsert_batch(
        self,
        vector_ids: List[str],
        vectors: List[List[float]],
        text_contents: List[str],
        metadatas: Optional[List[Dict]] = None,
    ) -> None:
        if not vector_ids:
            return

        processed_metas = []
        if metadatas:
            processed_metas = [self._sanitize_metadata(m) for m in metadatas]
        else:
            processed_metas = [{}] * len(vector_ids)

        self._collection.upsert(
            ids=vector_ids,
            embeddings=vectors,
            documents=text_contents,
            metadatas=processed_metas,
        )

    def query(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        """Semantic search execution logic. Converts cosine distances to similarity metrics."""
        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results.get("ids") or len(results["ids"]) == 0 or not results["ids"][0]:
            return []

        hits: List[Dict] = []
        ids       = results["ids"][0]
        docs      = results["documents"][0]
        metas     = results["metadatas"][0]
        distances = results["distances"][0]

        for vid, doc, meta, dist in zip(ids, docs, metas, distances):
            similarity = 1.0 - dist          
            if similarity < CONFIDENCE_CUTOFF:
                continue
                
            hits.append(
                {
                    "vector_id":    vid,
                    "text_content": doc,
                    "metadata":     meta,
                    "similarity":   round(similarity, 4),
                }
            )

        return hits