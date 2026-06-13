"""
EmbeddingManager
----------------
Wraps the Gemini Embedding 2 API to produce 3,072-dim vectors.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "gemini-embedding-2"
DIMENSIONS      = 3072


class EmbeddingManager:
    """Generates 3,072-dimensional cross-modal vectors via the Gemini Embedding 2 API."""

    def __init__(self, api_key: Optional[str] = None, dimensions: int = DIMENSIONS):
        self.dimensions = dimensions
        self.api_key    = api_key
        self._client    = self._build_client()

    def generate_document_vector(
        self,
        text_content: str,
        title: Optional[str] = None,
        img_path: Optional[str] = None
    ) -> List[float]:
        """Structures text inputs as 'title: X | text: Y' to optimize index retrieval precision."""
        resolved_title = title if title else "none"
        structured_text = f"title: {resolved_title} | text: {text_content}"
        return self._execute_embedding(structured_text, img_path)

    def generate_query_vector(self, user_query: str) -> List[float]:
        """Structures text prompts as 'task: question answering | query: X' to enhance matching."""
        structured_query = f"task: question answering | query: {user_query}"
        return self._execute_embedding(structured_query, img_path=None)

    def _execute_embedding(self, structured_prompt: str, img_path: Optional[str] = None) -> List[float]:
        contents: List[Any] = []

        if img_path:
            img_bytes = self._load_image_bytes(img_path)
            if img_bytes:
                from google.genai import types
                mime = self._infer_mime(img_path)
                contents.append(
                    types.Part.from_bytes(data=img_bytes, mime_type=mime)
                )

        contents.append(structured_prompt)

        try:
            response = self._client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=contents,
                config={"output_dimensionality": self.dimensions}
            )
            vector: List[float] = response.embeddings[0].values
            return vector
        except Exception as exc:
            logger.error("Gemini Embedding 2 engine transaction failed: %s", exc)
            raise

    def _build_client(self) -> Any:
        try:
            from google import genai
            if self.api_key:
                return genai.Client(api_key=self.api_key)
            return genai.Client()
        except ImportError as exc:
            raise ImportError(
                "The required google-genai SDK package is missing. Run: pip install google-genai"
            ) from exc

    @staticmethod
    def _load_image_bytes(path: str) -> Optional[bytes]:
        p = Path(path)
        if not p.exists() or not p.is_file():
            return None
        return p.read_bytes()

    @staticmethod
    def _infer_mime(path: str) -> str:
        suffix = Path(path).suffix.lower()
        mapping = {
            ".png": "image/png", ".jpg": "image/jpeg", 
            ".jpeg": "image/jpeg", ".webp": "image/webp", 
            ".bmp": "image/bmp"
        }
        return mapping.get(suffix, "image/png")