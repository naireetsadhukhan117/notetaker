"""
Database layer – SQLite implementation of the ER schema.
"""

from __future__ import annotations
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, List, Optional

from models.entities import SourceMaterial, DocumentChunk, VisualAid

DDL = """
CREATE TABLE IF NOT EXISTS sources (
    source_id    TEXT PRIMARY KEY,
    file_name    VARCHAR(255) NOT NULL,
    file_type    VARCHAR(50)  NOT NULL CHECK(file_type IN ('PDF','VIDEO','AUDIO','TEXT')),
    storage_path TEXT         NOT NULL,
    created_at   TEXT         NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id      TEXT PRIMARY KEY,
    source_id     TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    vector_id     VARCHAR(128) UNIQUE NOT NULL,
    text_content  TEXT NOT NULL,
    start_seconds INTEGER,
    end_seconds   INTEGER
);

CREATE TABLE IF NOT EXISTS visual_aids (
    image_id      TEXT PRIMARY KEY,
    chunk_id      TEXT NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    local_path    TEXT NOT NULL,
    phash_string  VARCHAR(64) NOT NULL,
    sharpness     REAL NOT NULL
);
"""


class Database:
    def __init__(self, db_path: str = "notebooklm.db"):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(DDL)

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class SourceRepository:
    def __init__(self, db: Database):
        self._db = db

    def insert(self, src: SourceMaterial) -> None:
        src.validate()
        with self._db._conn() as conn:
            conn.execute(
                "INSERT INTO sources(source_id, file_name, file_type, storage_path, created_at) "
                "VALUES (?,?,?,?,?)",
                (str(src.source_id), src.file_name,
                 src.file_type.upper(), src.storage_path, src.created_at.isoformat())
            )

    def get(self, source_id: uuid.UUID) -> Optional[SourceMaterial]:
        with self._db._conn() as conn:
            row = conn.execute(
                "SELECT * FROM sources WHERE source_id=?", (str(source_id),)
            ).fetchone()
        if row is None:
            return None
        return SourceMaterial(
            source_id=uuid.UUID(row["source_id"]),
            file_name=row["file_name"],
            file_type=row["file_type"],
            storage_path=row["storage_path"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

    def list_all(self) -> List[SourceMaterial]:
        with self._db._conn() as conn:
            rows = conn.execute("SELECT * FROM sources ORDER BY created_at DESC").fetchall()
        return [
            SourceMaterial(
                source_id=uuid.UUID(r["source_id"]),
                file_name=r["file_name"],
                file_type=r["file_type"],
                storage_path=r["storage_path"],
                created_at=datetime.fromisoformat(r["created_at"])
            )
            for r in rows
        ]


class ChunkRepository:
    def __init__(self, db: Database):
        self._db = db

    def insert(self, chunk: DocumentChunk) -> None:
        start_secs = int(chunk.start_time) if chunk.start_time is not None else None
        end_secs = int(chunk.end_time) if chunk.end_time is not None else None

        with self._db._conn() as conn:
            conn.execute(
                "INSERT INTO chunks(chunk_id, source_id, vector_id, text_content, "
                "start_seconds, end_seconds) VALUES (?,?,?,?,?,?)",
                (str(chunk.chunk_id), str(chunk.source_id), chunk.vector_id,
                 chunk.text_content, start_secs, end_secs)
            )

    def get_by_source(self, source_id: uuid.UUID) -> List[DocumentChunk]:
        with self._db._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM chunks WHERE source_id=?", (str(source_id),)
            ).fetchall()
        return [
            DocumentChunk(
                chunk_id=uuid.UUID(r["chunk_id"]),
                source_id=uuid.UUID(r["source_id"]),
                vector_id=r["vector_id"],
                text_content=r["text_content"],
                start_time=float(r["start_seconds"]) if r["start_seconds"] is not None else None,
                end_time=float(r["end_seconds"]) if r["end_seconds"] is not None else None,
            )
            for r in rows
        ]


class VisualAidRepository:
    def __init__(self, db: Database):
        self._db = db

    def insert(self, aid: VisualAid) -> None:
        with self._db._conn() as conn:
            conn.execute(
                "INSERT INTO visual_aids(image_id, chunk_id, local_path, "
                "phash_string, sharpness) VALUES (?,?,?,?,?)",
                (str(aid.image_id), str(aid.chunk_id), aid.local_path,
                 aid.phash_string, aid.sharpness_score)
            )

    def get_by_chunk(self, chunk_id: uuid.UUID) -> Optional[VisualAid]:
        with self._db._conn() as conn:
            row = conn.execute(
                "SELECT * FROM visual_aids WHERE chunk_id=? ORDER BY sharpness DESC LIMIT 1",
                (str(chunk_id),)
            ).fetchone()
        if row is None:
            return None
        return VisualAid(
            image_id=uuid.UUID(row["image_id"]),
            chunk_id=uuid.UUID(row["chunk_id"]),
            local_path=row["local_path"],
            phash_string=row["phash_string"],
            sharpness_score=row["sharpness"],
        )