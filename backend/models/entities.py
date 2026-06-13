"""
Data Carrier Entities
Domain Model
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


# ---------------------------------------------------------------------------
# SourceMaterial
# ---------------------------------------------------------------------------
@dataclass
class SourceMaterial:
    """Represents an uploaded raw media / document file."""
    source_id:    uuid.UUID = field(default_factory=uuid.uuid4)
    file_name:    str        = ""
    file_type:    str        = ""
    storage_path: str        = ""
    created_at:   datetime   = field(default_factory=lambda: datetime.now(timezone.utc))

    VALID_TYPES = {"PDF", "VIDEO", "AUDIO", "TEXT"}

    def __post_init__(self) -> None:
        self.file_type = self.file_type.strip().upper()
        self.validate()

    def validate(self) -> None:
        if self.file_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid file_type '{self.file_type}'. "
                f"Must be one of {self.VALID_TYPES}."
            )
        if not self.file_name.strip():
            raise ValueError("file_name must not be empty.")
        if not self.storage_path.strip():
            raise ValueError("storage_path must not be empty.")


# ---------------------------------------------------------------------------
# DocumentChunk
# ---------------------------------------------------------------------------
@dataclass
class DocumentChunk:
    """
    A bounded slice of text (or Whisper transcript) linked to a source.
    start_time / end_time are seconds-based offsets for video/audio.
    For pure text documents, these fields remain None.
    """
    chunk_id:     uuid.UUID  = field(default_factory=uuid.uuid4)
    source_id:    uuid.UUID  = field(default_factory=uuid.uuid4)
    vector_id:    str        = ""
    text_content: str        = ""
    start_time:   Optional[float] = None
    end_time:     Optional[float] = None


# ---------------------------------------------------------------------------
# VisualAid
# ---------------------------------------------------------------------------
@dataclass
class VisualAid:
    """Keyframe image extracted, de-duplicated, and saved to local asset dir."""
    image_id:        uuid.UUID = field(default_factory=uuid.uuid4)
    chunk_id:        uuid.UUID = field(default_factory=uuid.uuid4)
    local_path:      str       = ""
    phash_string:    str       = ""
    sharpness_score: float     = 0.0