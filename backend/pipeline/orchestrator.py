"""
IngestionOrchestrator
---------------------
Orchestration master controller managing structural data pipelines.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class IngestionError(Exception):
    status_code: int = 400


class IngestionOrchestrator:
    """Coordinates video extraction, deduplication, indexing, and notes synthesis workflows."""

    def __init__(
        self,
        asset_dir:      str = "./assets",
        db_path:        str = "./notebooklm.db",
        chroma_dir:     str = "./chroma_db",
        gemini_api_key: str = "",
        llm_provider:   str = "groq",
        llm_api_key:    str = "",
    ):
        from db.repositories import Database, SourceRepository, ChunkRepository, VisualAidRepository
        from db.vector_store import VectorStore
        from pipeline.embedding_manager import EmbeddingManager
        from pipeline.generation_engine import GenerationEngine

        self.asset_dir = asset_dir
        Path(asset_dir).mkdir(parents=True, exist_ok=True)

        self._db         = Database(db_path)
        self._src_repo   = SourceRepository(self._db)
        self._chunk_repo = ChunkRepository(self._db)
        self._aid_repo   = VisualAidRepository(self._db)
        self._vs         = VectorStore(chroma_dir)
        self._embedder   = EmbeddingManager(gemini_api_key)
        self._gen        = GenerationEngine(llm_provider, llm_api_key)

    def ingest(self, file_path: str) -> Dict:
        p = Path(file_path)

        if not p.exists() or p.stat().st_size == 0:
            raise IngestionError(f"Target workspace file not found or empty: {file_path}")

        file_type = self._detect_type(p)
        if file_type is None:
            raise IngestionError(f"Unsupported file format extension layout: {p.suffix}")

        from models.entities import SourceMaterial
        src = SourceMaterial(
            file_name=p.name,
            file_type=file_type,
            storage_path=str(p.resolve()),
        )
        self._src_repo.insert(src)

        if file_type == "VIDEO":
            chunks = self._process_video(src)
        elif file_type == "AUDIO":
            chunks = self._process_audio(src)
        else:
            chunks = self._process_text(src)

        return {"source_id": str(src.source_id), "chunks": len(chunks)}

    def generate_notes(self, query: str, top_k: int = 5) -> str:
        vector  = self._embedder.generate_query_vector(query)
        results = self._vs.query(vector, top_k=top_k)

        for r in results:
            lp = r["metadata"].get("local_path", "")
            if lp and not Path(lp).exists():
                r["metadata"]["local_path"] = ""

        return self._gen.generate_notes(query, results)

    def generate_quiz(self, query: str, num_questions: int = 5) -> str:
        vector  = self._embedder.generate_query_vector(query)
        results = self._vs.query(vector, top_k=num_questions * 2)
        return self._gen.generate_quiz(results, num_questions)

    def _process_video(self, src) -> List:
        from pipeline.video_processor    import VideoProcessor
        from pipeline.image_deduplicator import ImageDeduplicator
        from models.entities             import DocumentChunk, VisualAid

        vp = VideoProcessor(src.storage_path)
        candidates = vp.extract_candidate_frames()

        if not candidates:
            return []

        deduper  = ImageDeduplicator()
        clusters = deduper.cluster_duplicates(candidates)
        winners  = deduper.persist_best_frames(clusters, self.asset_dir)

        chunks: List = []
        for w in winners:
            chunk = DocumentChunk(
                source_id=src.source_id,
                vector_id=uuid.uuid4().hex,
                text_content=f"[Keyframe at {w['timestamp_sec']:.1f}s]",
                start_time=w["timestamp_sec"],
                end_time=w["timestamp_sec"],
            )
            
            self._chunk_repo.insert(chunk)

            vector = self._embedder.generate_document_vector(
                text_content=chunk.text_content,
                title=src.file_name,
                img_path=w.get("local_path")
            )
            
            self._vs.upsert(
                vector_id=chunk.vector_id,
                vector=vector,
                text_content=chunk.text_content,
                metadata={
                    "chunk_id":   str(chunk.chunk_id),
                    "source_id":  str(src.source_id),
                    "local_path": w.get("local_path", ""),
                    "start_time": w["timestamp_sec"],
                    "end_time":   w["timestamp_sec"],
                },
            )

            aid = VisualAid(
                chunk_id=chunk.chunk_id,
                local_path=w.get("local_path", ""),
                phash_string=w.get("phash", ""),
                sharpness_score=w.get("sharpness_score", 0.0),
            )
            self._aid_repo.insert(aid)
            chunks.append(chunk)

        return chunks

    def _process_text(self, src) -> List:
            from models.entities import DocumentChunk
            
            content = ""
            
            if src.file_type == "PDF":
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(src.storage_path)
                    text_pages = []
                    for idx, page in enumerate(reader.pages):
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text_pages.append(f"--- PAGE {idx + 1} ---\n{page_text}")
                    content = "\n\n".join(text_pages)
                except Exception as e:
                    logger.error("Failed to parse structural PDF text layer: %s", e)
                    content = Path(src.storage_path).read_text(errors="replace")
            else:
                content = Path(src.storage_path).read_text(errors="replace")

            if not content.strip():
                content = "[Empty Document Layer Source File Content]"

            chunk_size = 1000
            raw_chunks = [
                content[i: i + chunk_size]
                for i in range(0, len(content), chunk_size)
                if content[i: i + chunk_size].strip()
            ]

            chunks: List = []
            for text in raw_chunks:
                chunk = DocumentChunk(
                    source_id=src.source_id,
                    vector_id=uuid.uuid4().hex,
                    text_content=text,
                    start_time=None,
                    end_time=None,
                )
                
                self._chunk_repo.insert(chunk)

                vector = self._embedder.generate_document_vector(
                    text_content=text,
                    title=src.file_name,
                    img_path=None
                )
                
                self._vs.upsert(
                    vector_id=chunk.vector_id,
                    vector=vector,
                    text_content=text,
                    metadata={
                        "chunk_id":  str(chunk.chunk_id),
                        "source_id": str(src.source_id),
                    },
                )
                chunks.append(chunk)

            return chunks

    def _process_audio(self, src) -> List:
        logger.warning("Audio processing module triggered: Whisper engine unconfigured.")
        return []

    @staticmethod
    def _detect_type(p: Path) -> Optional[str]:
        ext = p.suffix.lower()
        if ext in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
            return "VIDEO"
        if ext in {".mp3", ".wav", ".m4a", ".ogg", ".flac"}:
            return "AUDIO"
        if ext == ".pdf":
            return "PDF"
        if ext in {".txt", ".md", ".docx", ".html"}:
            return "TEXT"
        return None